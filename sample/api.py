# -*- coding: UTF-8 -*-
import os, sys, time, json, cgi

from http.server import BaseHTTPRequestHandler,HTTPServer
from webwhatsapi import WhatsAPIDriver
from webwhatsapi.objects.message import Message, MediaMessage

SECURITY_TOKEN = '<<ENTER YOUR TOKEN HERE>>'

print("Environment", os.environ)
try:
   os.environ["SELENIUM"]
except KeyError:
   print("Please set the environment variable SELENIUM to Selenium URL")
   sys.exit(1)

class Server(BaseHTTPRequestHandler):
    def _set_headers(self):
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        
    def do_HEAD(self):
        self._set_headers()
        
    # GET sends back a Hello world message
    def do_GET(self):
        self._set_headers()
        self.wfile.write(json.dumps({'status': 'ok'}).encode(encoding='utf_8'))
        
    # POST echoes the message adding a JSON field
    def do_POST(self):
        ctype, pdict = cgi.parse_header(self.headers.get('content-type'))
        
        # refuse to receive non-json content
        if ctype != 'application/json':
            self.send_response(400)
            self.end_headers()
            return

        if self.path != '/send':
            self.send_response(404)
            self.end_headers()
            return

        if self.headers.get('token') != SECURITY_TOKEN:
            self.send_response(401)
            self.end_headers()
            return
            
        # read the message and convert it into a python dictionary
        length = int(self.headers.get('content-length'))
        response = self.rfile.read(length)
        message = json.loads(response)
        
        print(message)
        Server.driver.send_message_to_id(message['address'], message['body'])
        
        # send the message back
        self._set_headers()
        self.wfile.write(json.dumps(message).encode(encoding='utf_8'))
        
def run(server_class=HTTPServer, handler_class=Server, port=8008):
    ##Save session on "/firefox_cache/localStorage.json".
    ##Create the directory "/firefox_cache", it's on .gitignore
    ##The "app" directory is internal to docker, it corresponds to the root of the project.
    ##The profile parameter requires a directory not a file.
    profiledir=os.path.join(".","firefox_cache")
    if not os.path.exists(profiledir): os.makedirs(profiledir)
    print("Initializing driver")
    driver = WhatsAPIDriver(profile=profiledir, client='remote', loadstyles=True, command_executor=os.environ["SELENIUM"])
    print("Waiting for login")
    driver.wait_for_login()
    print("Saving session")
    driver.save_firefox_profile(remove_old=False)
    print("Bot started")

    handler_class.driver = driver
    server_address = ('', port)
    httpd = server_class(server_address, handler_class)
    
    print('Starting httpd on port %d...' % port)
    httpd.serve_forever()
    
if __name__ == "__main__":
    from sys import argv
    
    if len(argv) == 2:
        run(port=int(argv[1]))
    else:
        run()