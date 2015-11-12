#!/usr/bin/env python3
import http.server
import socketserver
import cgi

PORT = 8000

Handler = http.server.CGIHTTPRequestHandler

class Handler1(Handler):
    def do_POST(self):
        print(self.request)
        form = cgi.FieldStorage(
            fp=self.rfile,
            headers=self.headers,
            environ={'REQUEST_METHOD':'POST',
            'CONTENT_TYPE':self.headers['Content-Type'],
        })
        length = int(self.headers['content-length'])
        print("_____________")
        print(form)
        print("_____________")
        #data = form['file'].file.read(length)
        #open("/tmp/file.a", "wb").write(data)
        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()

httpd = socketserver.TCPServer(("", PORT), Handler1)

print("serving at port", PORT)
httpd.serve_forever()

