#!/usr/bin/env python3
from http.server import CGIHTTPRequestHandler, HTTPServer
from socketserver import ThreadingMixIn
import cgi
import time
import string
import random
import os
import asyncio

import multiprocessing as mp
from queue import Queue

PORT = 8000
CHUNKSIZE=1024*200 # 200kb
UPLOAD_NAME="upload/%s_%s"
TMP_FILE="/tmp/file_%s"

def percentage(part, whole):
    return "%.2f" % (part / whole * 100)

def rand_id(size=6, alph=string.ascii_lowercase + string.digits):
    return ''.join([random.choice(alph) for _ in range(size)])

            
class ThreadedHTTPServer(ThreadingMixIn, HTTPServer):
    pass

class FileLoader(CGIHTTPRequestHandler):
    files = {}
    def do_POST(self):
        file_id = rand_id()
        self.files[file_id] = {"tmp": TMP_FILE % file_id}

        self.send_response(200)
        self.send_header("Content-type", "text")
        self.end_headers()

        self.wfile.write(bytes(file_id, "utf-8"))

    def do_PUT(self):
        print(self.rfile)
        file_id = self.path.replace('/', '')
        if file_id not in self.files:
            self.send_response(404)
            self.send_header("Content-type", "text")
            self.end_headers()

            self.wfile.write(bytes("No such file_id", "utf-8"))
            return

        self.files[file_id]["len"] = int(self.headers['content-length'])
        
        self.send_response(200)
        self.send_header("Content-type", "text")
        self.end_headers()

        self.wfile.write(bytes(self.save_file(file_id), "utf-8"))

    def do_GET(self):
        file_id = self.path.replace('/', '')
        if file_id not in self.files:
            super(FileLoader, self).do_GET()
        else:
            self.send_response(200)
            self.send_header("Content-type", "text")
            self.end_headers()

            self.wfile.write(bytes(percentage(os.stat(self.files[file_id]["tmp"]).st_size, self.files[file_id]["len"]), "utf-8"))


    def save_file(self, file_id):
        length = self.files[file_id]["len"]
        tmp = open(self.files[file_id]["tmp"], "w+b")

        tmp_len = length
        while tmp_len > 0:
            print(percentage(tmp_len, length))
            part = self.rfile.read(min(tmp_len, CHUNKSIZE))
            if not part: break
            tmp.write(part)
            tmp_len -= len(part)
        tmp.seek(0)

        form = cgi.FieldStorage(
            fp=tmp,
            headers=self.headers,
            environ={
                'REQUEST_METHOD':'POST',
                'CONTENT_TYPE':self.headers['Content-Type'],
        })

        upload = form['file']
        if upload.filename:
            name = os.path.basename(upload.filename)
            upload_name = UPLOAD_NAME % (file_id, name)
            out = open(upload_name, 'wb', CHUNKSIZE)

            while True:
                packet = upload.file.read(CHUNKSIZE)
                if not packet:
                    break
                out.write(packet)
            out.close()

            return upload_name


if __name__ == "__main__":
    httpd = ThreadedHTTPServer(("0.0.0.0", PORT), FileLoader)

    try:
        print("serving at port", PORT)
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass

    httpd.server_close()

