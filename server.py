#!/usr/bin/python3
# -*- coding: utf-8 -*-

from http.server import BaseHTTPRequestHandler, HTTPServer
from http.cookies import SimpleCookie as cookie
from io import BytesIO,StringIO
from PIL import Image 
from robots import RWorld, RRobot
from uuid import uuid4
from time import time
import os

# HTTPRequestHandler class
html_top = """<!DOCTYPE HTML>
<html>
<head>
<meta charset="utf-8">
<title>Hello Robot!</title>
</head>
<body>
"""
html_bottom = """</body>
</html>
"""
worlds = dict()

class testHTTPServer_RequestHandler(BaseHTTPRequestHandler):
  sessioncookies = {} 
  # GET
  def _session_cookie(self,forcenew=False):  
    cookiestring = "\n".join(self.headers.get_all('Cookie',failobj=[]))  
    c = cookie()  
    c.load(cookiestring)
    try:  
        if forcenew or self.sessioncookies[c['session_id'].value]-time() > 3600:  
            raise ValueError('new cookie needed')  
    except:  
        c['session_id']=uuid4().hex  
    
    for m in c:  
        if m=='session_id':  
            self.sessioncookies[c[m].value] = time()  
            c[m]["httponly"] = True  
            c[m]["max-age"] = 3600  
            c[m]["expires"] = self.date_time_string(time()+3600)  
            self.sessionidmorsel = c[m]  
            break      
  def do_POST(self):
    self._session_cookie()
    sname = self.sessionidmorsel.value
    
    self.send_response(301)
    self.send_header('Location','/')
    self.end_headers()

    #print ('path = ', self.path)
    if (sname in worlds):
        content_length = int(self.headers['Content-Length']) # <--- Gets the size of data
        post_data = self.rfile.read(content_length) # <--- Gets the data itself
        post_data = post_data.decode('utf-8')
        if self.path=="/step":
            worlds[sname].step()
        if self.path=="/run":
            worlds[sname].run()
        if self.path=="/reset":
            worlds[sname].reset()
        if self.path.startswith("/update"):
            print ("path:", self.path, "post_data:", post_data)
            rid = self.path.strip("/update")
            rid = rid.split('/')
            rid = int(rid[0])
            settings = post_data.split('&')
            robot = worlds[sname].robots[rid][0]
            for s in settings:
                #print ("settings: ",s.splot)
                t = s.split('=')
                robot.update(t[0],t[1])
            robot.reset()
        if self.path.startswith("/kill"):
            rid = self.path.strip("/kill")
            rid = rid.split('/')
            rid = int(rid[0])
            robot = worlds[sname].robots[rid]
            worlds[sname].robots.remove(robot)
        if post_data.startswith('mapimg'):
            post_data = post_data.split('=')
            if (post_data[0] == 'mapimg'):
                worlds[sname].load_map(post_data[1])
            return
        if post_data.startswith('mapclick'):
            post_data = post_data.replace('&','=').split('=')
            rr = RRobot()
            rpos = (int(post_data[1]),int(post_data[3]))
            worlds[sname].spawn_robot(rr,rpos)
            return
  
  def do_GET(self):
        self._session_cookie()  

        global world
        #self.send_error(404,'File Not Found: %s' % self.path)
        #return
        # Send response status code

        if self.path=="/favicon.ico":
            self.send_response(200)
            self.send_header("Content-type", "image/x-icon")
            self.end_headers()
            try:
                ico = open("favicon.ico","rb")
            except IOError:
                print ('favicon not found')
            else:
                self.wfile.write(ico.read())
            return
        
        output = StringIO()
        output.write(html_top)
        sname = self.sessionidmorsel.value
        
        if self.path=="/img/worldmap.png":
            if not (sname in worlds):
                self.send_response(404)
                return
            else:
                self.send_response(200)
            self.send_header("Content-type", "image/png")
            self.end_headers()
            #img = Image.new('RGB', (60, 30), color = (73, 109, 137))
            img = worlds[sname].get_world_png()
            byte_io = BytesIO()
            img.save(byte_io, 'PNG')
            byte_io.seek(0)
            self.wfile.write(byte_io.read())
            return
            
        if self.path.startswith("/img/robot/"):
            if not (sname in worlds):
                self.send_response(404)
                return
            else:
                self.send_response(200)
            self.send_header("Content-type", "image/png")
            self.end_headers()
            rid = self.path.strip("/img/robot/")
            rid = rid.split('/')
            id = int(rid[0])
            #img = Image.new('RGB', (60, 30), color = (73, 109, 137))
            if rid[1].startswith("camera"):
                img = worlds[sname].robots[id][0].camera_png()
            else:
                img = worlds[sname].robots[id][0].local_map_png()
            byte_io = BytesIO()
            img.save(byte_io, 'PNG')
            byte_io.seek(0)
            self.wfile.write(byte_io.read())
            return
            
        if self.path=="/":
            if not (sname in worlds):
                output.write('Welcome to the real world! %s'%sname)
                worlds[sname] = RWorld()
                worlds[sname].load_map('map00.png')
            else:
                output.write('Hello robot! %s'%sname)

        else:
            output.write('Bad robot :[')
        output.write('<table><tr><td valign="top">')
        output.write('Current time %d<br>'%worlds[sname].time)
        output.write('<form action="" method="POST"><button formaction="step">Step</button><button formaction="run">Run</button><button formaction="reset">Reset</button></form>')
        output.write('World [%dx%d] map: '%(worlds[sname].get_global_map().get_xm(),worlds[sname].get_global_map().get_ym()))
        output.write('<form action="mapselect" method="POST"><select name="mapimg" id="mapimg" onchange="this.form.submit()">')
        for f in os.listdir('.'):
            if os.path.isfile(f):#print (f)
                if f.endswith('.png'):
                    if f == worlds[sname].get_global_map().get_name():
                        output.write('<option value="%s" selected="selected">%s</option>'%(f,f))
                    else:
                        output.write('<option value="%s">%s</option>'%(f,f))
        
        output.write('</select></form><br>')
       
        output.write('<form action="mapclick" method="POST">')
        output.write('<input name="mapclick" type="image" src="/img/worldmap.png" alt="Submit">')
        output.write('</form>')
        output.write('</td><td valign="top">World log:<br>%s</td></tr></table>'%worlds[sname].get_log())

        output.write('<table border="1"><tr>')
        for index, robot in enumerate(worlds[sname].robots):
            output.write('<td>Robot #%d @ %s mv %s</td>'%(index,robot[1],str(robot[0].move)))
        output.write('</tr><tr>')
        for index, robot in enumerate(worlds[sname].robots):
            output.write('<td>Camera view: <img src="/img/robot/%d/camera.png"></td>'%index)
        #    
        #    #output.write(str(index)+str(robot[1])+'<br>')
        output.write('</tr><tr>')
        for index, robot in enumerate(worlds[sname].robots):
            output.write('<td valign="top"><img src="/img/robot/%d/localmap.png"></td>'%index)
        output.write('</tr><tr>')
        for index, robot in enumerate(worlds[sname].robots):
            output.write('<td><form action="update/%d" method="POST">'%index)
            for s in robot[0].settings:
                output.write('%s: <input type="text" name="%s" value="%s"><br>'%(s,s,str(robot[0].settings[s][0])))
                #output.write('<td>Settings:<br>%s</td>'%str(robot[0].settings))
            output.write('<input type="submit" value="Update"><input formaction="kill/%d" type="submit" value="KILL"></td></form>'%index)
        output.write('</tr><tr>')
        for index, robot in enumerate(worlds[sname].robots):
            output.write('<td>Log:<br>%s</td>'%robot[0].get_log())
        #output.write('</table>')
        #output.write('<br><img src=/img/worldmap.png>')
        output.write('<tr></table>')
        output.write(html_bottom)
        #print ('putput: '+output)
        output.seek(0)
        self.send_response(200)
        self.send_header("Content-type", "text/html")
        if not (self.sessionidmorsel is None):  
            self.send_header('Set-Cookie',self.sessionidmorsel.OutputString())
        self.end_headers()
        self.wfile.write(bytes(output.read(),encoding = 'utf-8'))
        #self.wfile.write()
        return
 
def run():
  print('starting server...')
  
  # Server settings
  # Choose port 8080, for port 80, which is normally used for a http server, you need root access
  server_address = ('', 8080)
  httpd = HTTPServer(server_address, testHTTPServer_RequestHandler)
  print('running server...')
  httpd.serve_forever()

#lworld = RWorld()
#print (uuid4().hex)
#lworld.get_global_map().gen_map_from_image('map01.png')
#print ("Map XM: ", lworld.get_global_map().__points)
run()