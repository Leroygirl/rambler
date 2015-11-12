#!/usr/bin/env python3
from http.server import CGIHTTPRequestHandler, HTTPServer
from socketserver import ThreadingMixIn
import cgi
import time
import string
import random
import os
import asyncio
import re

import multiprocessing as mp
from queue import Queue

PORT = 8000
CHUNKSIZE=1024*200 # 200kb

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
        self.files[file_id] = {}

        self.send_response(200)
        self.send_header("Content-type", "text")
        self.end_headers()

        self.wfile.write(bytes(file_id, "utf-8"))

    def do_PUT(self):
        file_id = self.path.replace('/', '')
        if file_id not in self.files:
            self.send_response(404)
            self.send_header("Content-type", "text")
            self.end_headers()

            self.wfile.write(bytes("No such file_id", "utf-8"))
            return

        is_succ, s = self.save_file(file_id)
        
        if is_succ:
            status = 200
        else:
            status = 400

        self.send_response(status)
        self.send_header("Content-type", "text")
        self.end_headers()

        self.wfile.write(bytes(s, "utf-8"))

    def do_GET(self):
        file_id = self.path.replace('/', '')
        if file_id not in self.files:
            super(FileLoader, self).do_GET()
        else:
            self.send_response(200)
            self.send_header("Content-type", "text")
            self.end_headers()

            if "path" in self.files[file_id]:
                self.wfile.write(bytes(percentage(os.stat(self.files[file_id]["path"]).st_size, self.files[file_id]["len"]), "utf-8"))
            else:
                self.wfile.write(bytes("0.0", "utf-8"))



    def save_file(self, file_id):
        boundary = bytes(self.headers['content-type'].split("=")[1], 'utf-8')
        boundary_line_re = re.compile(b'\r\n[-]+' + boundary + b'[-]+\r\n')

        remainbytes = int(self.headers['content-length'])
        line = self.rfile.readline()
        remainbytes -= len(line)

        line = self.rfile.readline()
        remainbytes -= len(line)
        fn = re.findall(r'Content-Disposition.*name="file"; filename="(.*)"', str(line))
        if not fn:
            return (False, "Can't find file name...")
        os.mkdir(os.path.join("upload", file_id))
        fn = os.path.join("upload", file_id, fn[0])


        line = self.rfile.readline()
        remainbytes -= len(line)
        line = self.rfile.readline()
        remainbytes -= len(line)
        try:
            out = open(fn, 'wb')
        except IOError:
            return (False, "Can't create file to write, do you have permission to write?")
                
        self.files[file_id]["path"] = fn
        self.files[file_id]["len"] = remainbytes

        chunksize = max(CHUNKSIZE, len(boundary))
        prechunk = self.rfile.read(chunksize)
        remainbytes -= len(prechunk)

        while True:
            if remainbytes:
                chunk = self.rfile.read(chunksize)
                remainbytes -= len(chunk)
                two_chunks = prechunk + chunk
            else:
                two_chunks = prechunk

            # print(two_chunks)
            if boundary in two_chunks:
                out.write(two_chunks.replace(boundary_line_re.findall(two_chunks)[0], b''))
                out.close()
                self.files[file_id]["len"] = os.stat(self.files[file_id]["path"]).st_size
                return (True, fn)
            else:
                out.write(prechunk)
                prechunk = chunk
        return (False, "Unexpect Ends of data.")


if __name__ == "__main__":
    httpd = ThreadedHTTPServer(("0.0.0.0", PORT), FileLoader)

    try:
        print("serving at port", PORT)
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass

    httpd.server_close()
