import serial
import time
import math
import re
from functools import partial

def moduleDict():
    res = {
        "button": {
            "id": 1,
            "name": "button",
            "raw": {
                "state": "int,0,1",
            },
            "properties": {
                "state": "bool",
            },
        },
        "dial": {
            "id": 2,
            "name": "dial",
            "raw": {
                "degree": "int,0,4095",
            },
            "properties": {
                "degree": "int,30,330",
            },
        },
        "gesture": {
            "id": 3,
            "name": "gesture",
            "raw": {
                "direction": "int,0,6",
            },
            "properties": {
                "direction": "enum,None,Up,Down,Left,Right,Near,Far",
            },
        },
        "color": {
            "id": 4,
            "name": "color",
            "raw": {
                "alpha": "int,0,5000",
                "red": "int,0,5000",
                "green": "int,0,5000",
                "blue": "int,0,5000",
            },
            "properties": {
                "color": "rgba",
                "hex": "str",
            },
        },
        "proximity": {
            "id": 5,
            "name": "proximity",
            "raw": {
                "amount": "int,0,255",
            },
            "properties": {
                "amount": "int,0,100",
            },
        },
        "joystick": {
            "id": 6,
            "name": "joystick",
            "raw": {
                "x": "int,0,4095",
                "y": "int,0,4095",
            },
            "properties": {
                "x": "int,0,100",
                "y": "int,0,100",
            },
        },
        "spin": {
            "id": 7,
            "name": "spin",
            "raw": {
                "rotation": "int,-30000,30000",
            },
            "properties": {
                "rotation": "int,-30000,30000",
                "direction": "enum,Still,Clockwise,Counterclockwise",
            },
        },
        "distance": {
            "id": 8,
            "name": "distance",
            "raw": {
                "milimeters": "float,0,1800",
            },
            "properties": {
                "milimeters": "float,0,1800",
                "inches": "float,0,70.8",
                "feet": "float,0,5.9",
            },
        },
        "glow": {
            "id": 9,
            "name": "glow",
            "functions": {
                "setColor": [
                    ["start", "int", 0,6],
                    ["end", "int", 0,6],
                    ["'", 0],
                    ["hue", "int", 0,255],
                    ["saturation", "int", 0,255],
                ],
                "setBrightness": [
                    ["start", "int",0,6],
                    ["end", "int",0,6],
                    ["'" , 1],
                    ["brightness", "int",0,255],
                ],
                "setWheel": [
                    ["start","int",0,6],
                    ["end","int",0,6],
                    ["'",2],
                    ["speed","int",0,255],
                ],
                "setGlitter": [
                    ["start","int",0,6],
                    ["end","int",0,6],
                    ["'",3],
                    ["hue","int",0,255],
                    ["saturation","int",0,255],
                ],
                "setDot": [
                    ["start","int",0,6],
                    ["end","int",0,6],
                    ["'",4],
                    ["hue","int",0,255],
                    ["saturation","int",0,255],
                    ["position","int",0,6],
                    ["spread","int",0,6],
                    ["gradient","toggle",0,1],
                ],
                "setMovingDot": [
                    ["start","int",0,6],
                    ["end","int",0,6],
                    ["'",5],
                    ["hue","int",0,255],
                    ["saturation","int",0,255],
                    ["movement","toggle",0,1],
                    ["speed","int",0,100],
                    ["spread","int",0,6],
                    ["gradient","toggle",0,1],
                    ["bounce","toggle",0,1],
                ],
                "setArc": [
                    ["start","int",0,6],
                    ["end","int",0,6],
                    ["'",6],
                    ["hue","int",0,255],
                    ["saturation","int",0,255],
                    ["movement","toggle",0,1],
                    ["position","int",0,6],
                    ["gradient","toggle",0,1],
                ],
                "setPulse": [
                    ["start","int",0,6],
                    ["end","int",0,6],
                    ["'",7],
                    ["hue","int",0,255],
                    ["saturation","int",0,255],
                    ["movement","toggle",0,1],
                    ["speed","int",0,100],
                    ["gradient","toggle",0,1],
                    ["bounce","toggle",0,1],
                ],
                "setConfetti": [
                    ["start","int",0,6],
                    ["end","int",0,6],
                    ["'",8],
                    ["bpm","float",1,600],
                    ["fade","float",0.1,1000],
                ],
                "setCrissCross": [
                    ["start","int",0,6],
                    ["end","int",0,6],
                    ["'",9],
                    ["bpm","float",1,600],
                    ["fade","float",0.1,1000],
                ],
                "setFade": [
                    ["start","int",0,6],
                    ["end","int",0,6],
                    ["'",10],
                    ["hue","int",0,255],
                    ["saturation","int",0,255],
                    ["movement","toggle",0,1],
                    ["speed","int",0,100],
                    ["low","int",0,255],
                    ["high","int",0,255],
                    ["bounce","toggle",0,1],
                ],
            },
        },
        "digital": {
            "id": 10,
            "name": "digital",
            "raw": {
                "state": "int,0,1",
            },
            "properties": {
                "state": "bool,0,1",
            },
        },
        "light": {
            "id": 11,
            "name": "light",
            "raw": {
                "brightness": "int,0,4095",
            },
            "properties": {
                "brightness": "int,0,100",
            },
        },
        "sound": {
            "id": 12,
            "name": "sound",
            "raw": {
                "volume": "int,0,4095",
            },
            "properties": {
                "volume": "int,0,100",
            },
        },
        "thermal": {
            "id": 13,
            "name": "thermal",
            "raw": {
                "pixel_temperatures": "op",
            },
            "properties": {
                "average_temperature_celsius": "float,0,80",
                "average_temperature_fahrenheit": "float,32,176",
                "center_temperature_celsius": "float,0,80",
                "center_temperature_fahrenheit": "float,32,176",
            },
        },
        "move": {
            "id": 14,
            "name": "move",
            "functions": {
                "setDegree": [
                    ["degree","int",0,180],
                ],
            },
        },
        "slider": {
            "id": 15,
            "name": "slider",
            "raw": {
                "position": "int,0,4095",
            },
            "properties": {
                "position": "int,0,100",
            },
        },
        "touch": {
            "id": 16,
            "name": "touch",
            "raw": {
                "amount": "int,0,90",
            },
            "properties": {
                "amount": "int,0,100",
            },
        },
        "tone": {
            "id": 17,
            "name": "tone",
            "functions": {
                "setTone": [
                    ["frequency", "int",0,3000],
                    ["time", "int",0,10000],
                ],
            },
        },
        "motion": {
            "id": 18,
            "name": "motion",
            "raw": {
                "movement": "int,0,1",
            },
            "properties": {
                "movement": "enum,Stilness,Movement",
            },
        },
        "flex": {
            "id": 19,
            "name": "flex",
            "raw": {
                "bend": "int,0,1000",
            },
            "properties": {
                "bend": "int,0,100",
            },
        },
        "force": {
            "id": 20,
            "name": "force",
            "raw": {
                "strength": "int,0,4095",
            },
            "properties": {
                "strength": "int,0,100",
            },
        },
        "environment": {
            "id": 21,
            "name": "environment",
            "raw": {
                "temperature": "float,-40,85",
                "pressure": "float,300,1100",
                "humidity": "float,0,90",
                "gas": "float,0,500",
                "altitude": "float,0,10",
            },
            "properties": {
                "temperature_celsius": "float,-40,85",
                "temperature_fahrenheit": "float,-40,185",
                "pressure": "float,300,1100",
                "humidity": "float,0,90",
                "gas": "float,0,500",
                "altitude": "float,0,10",
            },
        },
        "vibration": {
            "id": 26,
            "functions": {
                "setState": [
                    ["state", "toggle",0,1],
                ],
            },
        },
    }
    return res
MODULE_FROM_ID = (lambda d:{str(d[k]['id']):k for k in d})(moduleDict())

class ModuleOutput:
    def __init__(self,port,modID,send=lambda x:x):
        self.port = port
        self.modID = modID
        self.module = MODULE_FROM_ID.get(str(self.modID))
        self._send = send
        defs = moduleDict().get(self.module)
        if defs is not None and "functions" in defs:
            i = 0
            self._defs = defs["functions"]
            for m in self._defs:
                setattr(self,m,partial(self.runFunction,m))
    def type_coerce(self,type_,val):
        coercers = {"int":int,"toggle":lambda v:int(bool(v)),"float":float}
        assert type_ in coercers,f"internal error: unknown {self.module} arg type {repr(type_)}"
        return coercers[type_](val)
    def runFunction(self,method,*args,**kwargs):
        assert method in self._defs, f"unknown {self.module} method {repr(method)}"
        r = [3,self.port,self.modID]
        sig = self._defs[method]
        inds = dict()
        i = 0
        for a in sig:
            if a[0] == "'":
                r.append(a[1])
                continue
            inds[a[0]] = len(r)
            if i < len(args):
                r.append(self.type_coerce(a[1],args[i]))
            else:
                r.append(a[2])
            i += 1
        for k in kwargs:
            assert k in inds,f"unknown argument to {method}: {repr(k)}"
            r[inds[k]] = self.type_coerce(sig[inds[k]][1],kwargs[k])
        return self._send(",".join(str(v) for v in r))
    def help(self,method=None):
        if method is None:
            return "call help on a method name to see its arguments and their recommended ranges"
        else:
            if method not in self._defs:
                return f"unknown method, available methods: {list(self._defs)}"
            d = self._defs[method]
            return method+"("+', '.join(f"{k[0]}:{k[1:]}" for k in d if k[0] != "'")+")"
    def __repr__(self):
        return f"<{self.module} output>"

class ModuleInput:
    def __init__(self,moduleID,data):
        self.modID = moduleID
        self.rawData = data
        self.module = MODULE_FROM_ID.get(str(self.modID))
        self._defns = moduleDict().get(self.module)
        self.data_valid = False
        
        defs = self._defns
        if defs is not None and "raw" in defs:
            raw = defs["raw"]
            if data != "-":
                arr = data.split(',')
                i = 0
                for k in raw:
                    d = arr[i]
                    if raw[k] == "op":#special case for thermal
                        grid = []
                        for row in range(8):
                            grid.append([])
                            for col in range(8):
                                grid[row].append(ModuleInput.type_coerce("float",arr[i]))
                                i += 1
                        setattr(self,k,grid)
                    else:
                        t,l,h = raw[k].split(",")
                        setattr(self,k,ModuleInput.type_coerce(t,d))
                        i += 1
            self.data_valid = True
    @staticmethod
    def type_coerce(type_,val):
        coercers = {"int":int,"toggle":lambda v:int(bool(v)),"float":float}
        assert type_ in coercers,f"internal error: unknown type {repr(type_)}"
        return coercers[type_](val)
    def __repr__(self):
        return f"ModuleData({self.module}:{self.rawData})"


#bare-bones quaternion class for those who don't want to use a quaternion library
class Quaternion:
    #https://en.wikipedia.org/wiki/Cayley%E2%80%93Dickson_construction
    def __init__(self,r,i=0,j=0,k=0):
        if isinstance(r,Quaternion):
            i+=r.i;j+=r.j;k+=r.k;r=r.r;
        if isinstance(i,Quaternion):
            r-=i.i;k+=i.j;j-=i.k;i=i.r;
        if isinstance(j,Quaternion):
            k+=j.i;r-=j.j;i+=j.k;j=j.r;
        if isinstance(k,Quaternion):
            j-=k.i;i+=k.j;r-=k.k;k=k.r;
        if isinstance(r,complex):
            j+=r.imag;r=r.real
        if isinstance(i,complex):
            k+=i.imag;i=i.real
        if isinstance(j,complex):
            r-=j.imag;j=j.real
        if isinstance(k,complex):
            i+=k.imag;k=k.real            
        self.ri = complex(float(r),float(i))
        self.jk = complex(float(j),float(k))
    @staticmethod
    def XYZW(x,y,z,w):
        return Quaternion(w,x,y,z)
    @staticmethod
    def of(ri,jk):
        return Quaternion(ri.real,ri.imag,jk.real,jk.imag)
    @property
    def r(self): return self.ri.real
    @r.setter
    def r(self,v): self.ri = complex(float(v),self.i)
    @property
    def i(self): return self.ri.imag
    @i.setter
    def i(self,v): self.ri = complex(self.r,float(v))
    @property
    def j(self): return self.jk.real
    @j.setter
    def j(self,v): self.jk = complex(float(v),self.k)
    @property
    def k(self): return self.jk.imag
    @k.setter
    def k(self,v): self.jk = complex(self.j,float(v))
    @property
    def x(self): return self.i
    @r.setter
    def x(self,v): self.i = v
    @property
    def y(self): return self.j
    @y.setter
    def y(self,v): self.j = v
    @property
    def z(self): return self.k
    @z.setter
    def z(self,v): self.k = v
    @property
    def w(self): return self.r
    @w.setter
    def w(self,v): self.r = v
    @property
    def rijk(self): return (self.r,self.i,self.j,self.k)
    @property
    def xyzw(self): return (self.x,self.y,self.z,self.w)
    def __repr__(self):
        c = [str(v) for v in self.rijk]
        for i in range(1,4):
            if c[i][0] != '-': c[i] = "+"+c[i]
        return f"({c[0]}{c[1]}i{c[2]}j{c[3]}k)"
    def __add__(self,o):
        o = Quaternion(o)
        return Quaternion.of(self.ri+o.ri,self.jk+o.jk)
    def __radd__(self,o):
        o = Quaternion(o)
        return Quaternion.of(o.ri+self.ri,o.jk+self.jk)
    def __sub__(self,o):
        o = Quaternion(o)
        return Quaternion.of(self.ri-o.ri,self.jk-o.jk)
    def __rsub__(self,o):
        o = Quaternion(o)
        return Quaternion.of(o.ri-self.ri,o.jk-self.jk)
    def conjugate(self):
        return Quaternion.of(self.ri.conjugate(),-self.jk)
    def __mul__(self,o):
        o = Quaternion(o)
        return Quaternion.of(self.ri*o.ri-o.jk.conjugate()*self.jk,o.jk*self.ri+self.jk*o.ri.conjugate())
    def __rmul__(self,o):
        o = Quaternion(o)
        return o.__mul__(self)
    def __truediv__(self,o):
        o = Quaternion(o)
        return self*(o.conjugate()*(1/(o.r**2+o.i**2+o.j**2+o.k**2)))
    def __rtruediv__(self,o):
        o = Quaternion(o)
        return o.__truediv__(self)
    def rotate(self,x,y,z):
        p = self*Quaternion(0,x,y,z)*self.conjugate()
        return p.i,p.j,p.k
    @property
    def real(self):
        return self.r
    @property
    def imag(self):
        return Quaternion.of(complex(0,self.ri.imag),self.jk)
    
        

class HardwareState:
    def __init__(self):
        self.modules = [None]*8
        self.battery_raw = None
    @staticmethod
    def parse(line):
        res = HardwareState()
        res.raw = line
        chunks = line.split(';')
        for i in range(8):
            res.modules[i] = ModuleInput(*chunks[i].split(":"))
        res.battery_raw = chunks[8]
        imudat = res.imudat = chunks[9].split("<")[0].split(":")
        imumode = res.imumode = imudat[0]
        imu_patterns = {'0':(),
                        '1':(('accel',lambda *a:a,3),),
                        '2':(('gyro',lambda *a:a,3),),
                        '3':(('euler',lambda *a:a,3),),
                        '4':(('quaternion',Quaternion.XYZW,4),),
                        '5':(('quaternion',Quaternion.XYZW,4),('accel',lambda *a:a,3)),}
        if imumode in imu_patterns:
            pattern = imu_patterns[imumode]
            args = tuple(float(v) if v != '-' else 0 for v in imudat[1:])
            i = 0
            for a,c,n in pattern:
                setattr(res,a,c(*(args[i+j] for j in range(n))))
                i += n
        return res
    def __repr__(self):
        return f"HardwareState({self.modules},bat_raw={self.battery_raw},imu={tuple(float(v) for v in self.imudat)})"

class Module:
    def __init__(self,port,data,send=lambda x:x):
        self.data = data
        self.port = port
        self.out = ModuleOutput(port,data.modID,send)
    def __repr__(self):
        return f"Module({self.out.module})"

MESH_PACKET_PATTERN = re.compile(r"(\d+);(\d+);([\dA-F]{12});((\d+:\d+:[^;]+;)*)")
class Hardware:
    def __init__(self,serialport):
        self.port = serialport
        self.ser = None
        self.modules = [None]*8
        self.timestamp = -1
        self.mesh = dict()
        self.message_prefix = ""
    def __repr__(self):
        return f"Hardware({repr(self.port)})"
    def __enter__(self):
        self.ser = serial.Serial(self.port,115200)
        self.ser.__enter__()
        return self
    def __exit__(self,*a):
        if self.ser is not None: self.ser.__exit__(*a)
    def read(self,quiet=1):
        assert self.ser is not None, "hardware not connected"
        assert not self.ser.closed, "hardware disconnected"
        oldtimestamp = self.timestamp
        try:
            
            line = self.ser.readline().decode("utf8")
            timestamp = time.time()
            if ":" not in line.split(";")[0]:
                #mesh packet
                m = MESH_PACKET_PATTERN.match(line)
                #assert m,"malformed mesh packet"
                if m:
                    mac = m.group(3)
                    data = m.group(4)
                    if mac not in self.mesh:
                        self.mesh[mac] = Hardware(f"mesh-{mac}")
                        self.mesh[mac].mac = mac
                        self.mesh[mac].ser = self.ser
                        self.mesh[mac].message_prefix = f"4,6,1,{mac},"
                    d = self.mesh[mac]
                    for msg in data.split(";"):
                        if len(msg) == 0: continue
                        port,mod,*mod_data = msg.split(":")
                        mod_data = ":".join(mod_data)
                        res = Module(port,ModuleInput(mod,mod_data),d.send)
                        d.modules[int(port)-1] = res
                        res.timestamp = timestamp
                    d.timestamp = timestamp
            else:
                data = HardwareState.parse(line)
                self.timestamp = timestamp
                data.timestamp = timestamp
                for i in range(8):
                    self.modules[i] = Module(i+1,data.modules[i],lambda v: self.send(v))
                self.battery_raw = data.battery_raw
                self.quaternion = data.quaternion if hasattr(data,"quaternion") else None
                self.euler = data.euler if hasattr(data,"euler") else None
                self.accel = data.accel if hasattr(data,"accel") else None
                self.imudat = data.imudat
                return data
        except Exception as e:
            if not quiet: raise e
            if quiet <= 1:
                print("error in read:",e)
        #return stale data
        data = HardwareState()
        self.timestamp = oldtimestamp
        data.timestamp = oldtimestamp
        for i in range(8):
            data.modules[i] = self.modules[i].data if self.modules[i] is not None else self.modules[i]
        data.battery_raw = self.battery_raw if hasattr(self,"battery_raw") else -1
        data.quaternion = self.quaternion if hasattr(self,"quaternion") else None
        data.euler = self.euler if hasattr(self,"euler") else None
        data.accel = self.accel if hasattr(self,"accel") else None
        data.imudat = self.imudat if hasattr(self,"imudat") else ()
        return data
    def send(self,cmd):
        self.ser.write((self.message_prefix+cmd+"\r\n").encode("utf8"))
        self.ser.flush()
    def connect(self):
        self.disconnect()
        self.ser = serial.Serial(self.port,115200)
    def disconnect(self):
        if self.ser is not None:
            self.ser.close()
            self.ser = None
    def __del__(self):
        self.disconnect()
        
