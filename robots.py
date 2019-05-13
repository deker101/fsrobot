from PIL import Image,ImageDraw
import operator
import math
import random

def tadd(a,b):
    return tuple(map(operator.add, a, b))

def tsub(a,b):
    return tuple(map(operator.sub, a, b))

def dist(a,b):
    d = (a[0]-b[0])*(a[0]-b[0])
    d = d + (a[1]-b[1])*(a[1]-b[1])
    return int(math.sqrt(d))

def polar(dec):
    x, y = dec
    r = math.sqrt(x*x+y*y)
    fi = 0
    if (x>0) and (y>=0):
        fi = math.atan(y/x)
    if (x>0) and (y<0):
        fi = math.atan(y/x)+math.pi()*2
    if (x>0) and (y<0):
        fi = math.atan(y/x)+math.pi()
    if (x==0) and (y>0):
        fi = math.pi()/2
    if (x==0) and (y<0):
        fi = math.pi()*3/2
    fi = round(math.degrees(fi))
    return (r, fi)
    
def decart(pol):
    r, fi = pol
    fi = math.radians(fi)
    x = round(r*math.cos(fi))
    y = round(r*math.sin(fi))
    return (x,y)

class RWorld():
    def __init__(self):
        print ('Init world')
        self.robots = []
        self.__global_map = RMap()
        self.__maxrobots = 5
        self.__log = []
        self.__log.append("Hello world")
        self.time = 0
        self.deg=0
        self.pos_err=0 #2


    def get_global_map(self):
        return self.__global_map
    def get_world_png(self):
        img = self.__global_map.get_png()
        d = ImageDraw.Draw(img)
        for index, robot in enumerate(self.robots):
            img.putpixel(robot[1],(255,0,0))

            #print(wn,es)\
            
            t=[]
            
            for e in robot[2]:
                t.append(e)
                if len(t)>3 and (len(t)%2 == 0): 
                    d.line(t[-4:], fill=(255,0,0), width=1)
            r = (robot[0].fov,robot[0].fov)
            #px, py = robot[1]
            wn=tsub(robot[1],r)
            es=tadd(robot[1],r)
            d.ellipse([wn, es], outline=(255,0,0))
            r = (robot[0].safe_dist,robot[0].safe_dist)
            #px, py = robot[1]
            wn=tsub(robot[1],r)
            es=tadd(robot[1],r)
            d.ellipse([wn, es], outline=(255,0,0))
            d.text((robot[1]),str(index),(255,0,0))
        return img
        
    def load_map(self,path):
        self.__global_map.gen_map_from_image(path)
        self.__log.append("Loadmap %s"%path)
        self.robots = []
        #for robot in reversed(self.robots):
        #    if self.__global_map.check_block(robot[1]):
        #        self.__log.append("Kill robot %d @ %s"%(self.robots.index(robot),str(robot[1])))
        #        self.robots.remove(robot)
        #        robot.reset()
        
    def spawn_robot(self, r, pos):
        if self.__global_map.check_block(pos):
            self.__log.append("FAIL Spawn robot @ %s"%str(pos))
            return
        for index, robot in enumerate(self.robots):
            if pos == robot[1]:
                self.__log.append("FAIL Spawn robot @ %s. Busy by %d"%(str(pos),index))
                return
        if len(self.robots) >= self.__maxrobots:
                self.__log.append("Too much robots.. :(")
                return
        trace = [pos[0], pos[1]]
        self.robots.append([r,pos, trace])
        self.__log.append("Spawn robot @ %s"%str(pos))        
    
    def get_log(self):
        res = ''
        for l in self.__log[-30:]:
            res = l+"<br>"+res
        return res
        
    def step(self):
        self.time = self.time + 1
        
        
        for r in self.robots:
            rlist = range(-r[0].settings['gpserr'][0], r[0].settings['gpserr'][0]+1, 1)
            pos_noise=(random.choice(rlist),random.choice(rlist))
            r[0].ext_pos = tadd(r[1],pos_noise) ##add rand noise
            r[0].ext_cam = self.__global_map.get_part(r[1],r[0].fov)
            r[0].step()
            dist, ang = r[0].move
            spos = r[1]
            for i in range(1,dist+1):
                check_pos = tadd(decart((i,ang)),spos)
                if self.__global_map.check_block(check_pos):
                    break
                else:
                    r[1]=check_pos
            r[2].append(r[1][0])
            r[2].append(r[1][1])
            
            
    def run(self):
        sleepcnt = 0
        for i in range(0,1000):
            self.step()
            for r in self.robots:
                if (r[0].move[0] == 0):
                    sleepcnt = sleepcnt + 1
                else:
                    sleepcnt = 0
                    break
            if (sleepcnt > 5):
                break
    
    def reset(self):
        self.time = 0
        self.__log.append("World reset @")
        for r in self.robots:
            r[2]=[]
            r[0].reset()

        
class RRobot():
    def __init__(self): 
        self.__pos=None
        self.__log=[]
        self.ext_pos=None
        self.ext_cam=[]
        self.__trace=[]

        self.move=(0,0)
        self.__lmap=RMap()
        self.program_list = ['go_n','round_l','sleep']
        self.__prog = None
        self.__param = None
        self.settings = dict()
        self.settings['gpserr'] = [1, 0, 5] #default, min, max
        self.settings['speed'] = [10, 1, 50]
        self.settings['FOV'] = [20, 2, 51]
        self.settings['safe_dist'] = [5, 1, 50]
        self.settings['CMDS'] = ['go_n, round_l, sleep', 0, 0]
        self.__log.append("HELLO")
        self.fov=self.settings['FOV'][0]
        self.speed=self.settings['speed'][0]
        self.safe_dist=self.settings['safe_dist'][0]

    def update(self, p, val):
        if not p in self.settings:
            self.__log.append("E unknown param %s"%p)
            return 

        if (p == 'CMDS'):
            val = val.replace('+','')
            val = val.replace('%2C',',')
            self.settings[p][0] = val
            self.program_list = self.settings[p][0]
            
            return
        try:
            t = int(val)
        except ValueError:
            self.__log.append("E not int param %s"%p)
            return

        if t < self.settings[p][1]:
            t = self.settings[p][1]
        if t > self.settings[p][2]:
            t = self.settings[p][2]
            self.settings[p][2]
        self.settings[p][0]=t

        if self.settings['safe_dist'][0] < self.settings['gpserr'][0]:
            self.settings['safe_dist'][0] = self.settings['gpserr'][0]+1
 
        if self.settings['speed'][0] > self.settings['FOV'][0]:
            self.settings['speed'][0] = self.settings['FOV'][0]-1

        if self.settings['safe_dist'][0] > self.settings['FOV'][0]:
            self.settings['safe_dist'][0] = self.settings['FOV'][0]-1
            
        self.fov=self.settings['FOV'][0]
        self.speed=self.settings['speed'][0]
        self.safe_dist=self.settings['safe_dist'][0]
        
        return
            
    def step(self):
        self.getpos()
        self.lookout()
        prog = self.__prog
        if (abs(self.move[1])>180):
            self.move = (self.move[0],self.move[1] % 360)
        if self.__prog == None:
            if len(self.program_list)>0:
                prog = self.program_list[0]
                self.__prog = prog
                self.program_list.remove(prog)
            else:
                self.__log.append("P nothing todo")
                prog = "sleep"
        else:
            prog = self.__prog

        if prog.startswith("sleep"):
            self.__log.append("Psleep")
            self.move=(0,0)
            self.__prog = None
            return
        if prog.startswith("step"):
            if prog[5]=='n': #north
                self.move=(self.speed,-90)
            if prog[5]=='s': 
                self.move=(self.speed,90)
            if prog[5]=='e': 
                self.move=(self.speed,0)
            if prog[5]=='w': 
                self.move=(self.speed,180)
            self.__prog = None    
            self.__log.append("move %s : %s"%(str(self.move),prog))
            return
        
        if prog.startswith("go"):      
        
            if prog[3]=='n': #north
                self.move=(self.speed,-90)
            if prog[3]=='s': 
                self.move=(self.speed,90)
            if prog[3]=='e': 
                self.move=(self.speed,0)
            if prog[3]=='w': 
                self.move=(self.speed,180)
            dang_area=[]
            
            check_pos = decart(self.move)
            check_pos = tadd(check_pos,self.__pos)
            dang_area = self.__lmap.get_part(check_pos,self.safe_dist)
            #print("safe area",check_pos,self.safe_dist,self.__pos,dang_area)
            if dang_area:
                self.__log.append("PStop")
                self.__prog = None 
                self.move = (0, self.move[1]) #save move angle
                return
            self.__log.append("move %s : %s"%(str(self.move),prog))
            return
            
        if prog.startswith("round"):
            if (self.__param) == None:
                self.__param=[prog[6],self.move[1],1, self.__pos, 0]
            param=self.__param
            param[4]=param[4]+1
            if param[4]>3:
                #print ("dist: ", dist(param[3],self.__pos))
                if dist(param[3],self.__pos)<(self.settings['gpserr'][0]+self.settings['gpserr'][0]+self.speed+1):
                    self.__log.append("Round by finished")
                    self.__param = None
                    self.__prog = None
            #print ("param",param, "pos",self.__pos, "last move:",self.move)
            cazm = param[1]
            if prog[6]=='l':
                aturn = list(range(5, 90, 5))
                amain = list(range(0,-185,-5))
            else:
                aturn = list(range(-5, -90, -5))
                amain = list(range(0, 185, 5))
           
            distances = [self.speed]#list(range(self.safe_dist,self.speed,self.safe_dist))
            #print (azms)
            check1 = {}
            check2 = {}
            if (param[2] == 0):
                for a in aturn:
                    max_free_vision = 0
                    #dang_area = []
                    for d in distances:
                        dir = (d,a+cazm)
                        check_pos = tadd(decart(dir),self.__pos)
                        #print ("check_pos",check_pos)
                        dang_area = self.__lmap.get_part(check_pos,self.safe_dist)
                        #print (a,d,not dang_area)
                        if (not dang_area):
                            if d > max_free_vision:
                                max_free_vision=d
                                
                            check1[a+cazm]=max_free_vision
                            #print (a+cazm,d)
                        else:
                            #print ("break",a+cazm,d)
                            break
                            
            for a in amain:
                max_free_vision = 0
                #dang_area = []
                for d in distances:
                    dir = (d,a+cazm)
                    check_pos = tadd(decart(dir),self.__pos)
                    #print ("check_pos",check_pos)
                    dang_area = self.__lmap.get_part(check_pos,self.safe_dist)
                    #print (a,d,not dang_area)
                    if (not dang_area):
                        if d > max_free_vision:
                            max_free_vision=d
                            
                        check2[a+cazm]=max_free_vision
                        #print (a+cazm,d)
                    else:
                        #print ("break",a+cazm,d)
                        break
            #print ("radar",amain)
            max_free_vision=0
           
            min_free_vision = self.fov+1
            max_free_vision = self.speed
            rmove=(0,0)
            tmove=(0,0)
            
            #print ("check1",check1)
            for m in check1:
                #print ("tr", m, check1[m],max_free_vision)
                if check1[m] >= max_free_vision:
                    if max_free_vision<self.speed:
                        tmove=(max_free_vision,m)
                    else:
                        tmove=(self.speed,m)
                    max_free_vision = check1[m]
                else:
                    break
            
            for m in check2:
                #print ("radar", m, check2[m])
                if check2[m] < min_free_vision:
                    if min_free_vision<self.speed:
                        rmove=(min_free_vision,m)
                    else:
                        rmove=(self.speed,m)
                    min_free_vision = check2[m]
                #else:
                #    break;
            if param[2] == 1:
                param[2] = 0
                tmove=(0,0)
            #print ("rt!",tmove,rmove)
            #tmove=(0,0)
            if tmove !=(0,0):
                param[1]=tmove[1]
                self.move=tmove
            else:
                param[1]=rmove[1]
                self.move=rmove            
            self.__param=param
                
            #print ("turn right:", rmove)
            #self.move=rmove
            self.__log.append("Round @ %s : %s"%(self.move,prog))
            return
            
        self.__log.append("PUnk : %s"%prog)
        self.__prog = None
        
    def getpos(self):
        self.__pos = self.ext_pos
        #self.__log.append("POS: %s"%str(self.__pos))
        self.__trace.append(self.__pos)
        
    def lookout(self):
        pos = self.__pos

        #print ("mapsize: ",self.__lmap.get_size())
        for p in self.ext_cam:
            b=tadd(p,pos)
            #print("lookout", p, pos,tadd(p,pos)) 
            self.__lmap.add_block(b)
        msx, msy = self.__lmap.get_size()
        if (msx<pos[0]+self.fov):
            msx=pos[0]+self.fov
        if (msy<pos[1]+self.fov):
            msy=pos[1]+self.fov
        self.__lmap.resize((msx,msy)) 
        #self.__log.append("CAMERA: %s"%str(self.ext_cam))
        return
        
    def reset(self):
        self.__pos=None
        self.__log=[]
        self.ext_pos=None
        self.ext_cam=[]
        self.__trace=[]

        self.move=(0,0)
        self.__lmap=RMap()
        self.program_list = self.settings['CMDS'][0].replace(' ','').split(',')
        self.__prog = None
        self.__param = None
        self.__log.append("RESET")
        
    def get_pos(self):
        return self.__pos
    
    def get_log(self):
        res = ''
        for l in self.__log[-20:]:
            res = l+"<br>"+res
        return res
    
    def camera_png(self):
        img = Image.new('RGB', (self.fov*2+1, self.fov*2+1), color = (200, 200, 200))
        c = (self.fov,self.fov)
        for p in self.ext_cam:
            t = tadd(p,(self.fov,self.fov))
            img.putpixel(t,(0,0,0))
        return img
    def local_map_png(self):
        img = self.__lmap.get_png()
        d = ImageDraw.Draw(img)
        l = []
        for points in self.__trace:
            l.append(points[0])
            l.append(points[1])
            if len(l)>3: 
                d.line(l[-4:], fill=(255,0,0), width=1)
        return img
    
    
    

class RMap():
    def __init__(self, xm=1, ym=1):
        self.__xm=xm
        self.__ym=ym
        self.__points = dict()
        self.__name = ''
    def get_xm(self):
        return self.__xm
    def get_ym(self):
        return self.__ym
        
    def get_size(self):
        return (self.__xm,self.__ym)
        
    def resize(self,size):
        self.__xm, self.__ym = size
        
    def get_part(self, pos, rad):
        field = []
        mx, my = pos
        for x in range(-rad,rad+1):
            for y in range(-rad,+rad+1):
                dist = math.sqrt(x*x+y*y)
                if dist <= rad:
                    if self.check_block((mx+x,my+y)):
                        #print ("check", (x,y),(mx+x,my+y))
                        field.append((x,y))
        return field
        
    def gen_map_from_image(self,path):
        im = Image.open(path)
        im.load()
        self.__xm, self.__ym = im.size
        self.__points = dict()
        
        for x in range(0,self.__xm):
            for y in range(0,self.__ym):
                r, g, b = im.getpixel((x, y))
                if (((r+g+b)/3)>127):
                    c = 0
                else:
                    c = 1
                    self.__points[(x,y)] = c
        self.__name = path
                #print ((x,y),c)
        #print (self.__points)
    def get_name(self):
        return self.__name
    def get_png(self):
        img = Image.new('RGB', (self.__xm+1, self.__ym+1), color = (240, 240, 240))
        for p in self.__points:
            #print (p)
            img.putpixel(p,(0,0,0))
        return img
    def check_block(self, p):
        
        x,y = p
        if x < 0:
            return True
        if y < 0:
            return True
        if x > self.__xm:
            return True
        if y > self.__ym:
            return True
        
        return (p in self.__points)
        
    def add_block(self, p):
        
        x,y = p
        if x < 0:
            return
        if y < 0:
            return
        if x > self.__xm:
            self.__xm = x
        if y > self.__ym:
            self.__ym = y
        if not p in self.__points:
            self.__points[(x,y)] = 1