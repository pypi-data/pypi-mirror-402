import serial
import time
import math

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
                "setColor": {
                    "start": "int,0,6",
                    "end": "int,0,6",
                    "hue": "int,0,255",
                    "saturation": "int,0,255",
                },
                "setBrightness": {
                    "start": "int,0,6",
                    "end": "int,0,6",
                    "brightness": "int,0,255",
                },
                "setWheel": {
                    "start": "int,0,6",
                    "end": "int,0,6",
                    "speed": "int,0,255",
                },
                "setGlitter": {
                    "start": "int,0,6",
                    "end": "int,0,6",
                    "hue": "int,0,255",
                    "saturation": "int,0,255",
                },
                "setDot": {
                    "start": "int,0,6",
                    "end": "int,0,6",
                    "hue": "int,0,255",
                    "saturation": "int,0,255",
                    "position": "int,0,6",
                    "spread": "int,0,6",
                    "gradient": "toggle,0,1",
                },
                "setMovingDot": {
                    "start": "int,0,6",
                    "end": "int,0,6",
                    "hue": "int,0,255",
                    "saturation": "int,0,255",
                    "movement": "toggle,0,1",
                    "speed": "int,0,100",
                    "spread": "int,0,6",
                    "gradient": "toggle,0,1",
                    "bounce": "toggle,0,1",
                },
                "setArc": {
                    "start": "int,0,6",
                    "end": "int,0,6",
                    "hue": "int,0,255",
                    "saturation": "int,0,255",
                    "movement": "toggle,0,1",
                    "position": "int,0,6",
                    "gradient": "toggle,0,1",
                },
                "setPulse": {
                    "start": "int,0,6",
                    "end": "int,0,6",
                    "hue": "int,0,255",
                    "saturation": "int,0,255",
                    "movement": "toggle,0,1",
                    "speed": "int,0,100",
                    "gradient": "toggle,0,1",
                    "bounce": "toggle,0,1",
                },
                "setConfetti": {
                    "start": "int,0,6",
                    "end": "int,0,6",
                    "bpm": "float,1,600",
                    "fade": "float,0.1,1000",
                },
                "setCrissCross": {
                    "start": "int,0,6",
                    "end": "int,0,6",
                    "bpm": "float,1,600",
                    "fade": "float,0.1,1000",
                },
                "setFade": {
                    "start": "int,0,6",
                    "end": "int,0,6",
                    "hue": "int,0,255",
                    "saturation": "int,0,255",
                    "movement": "toggle,0,1",
                    "speed": "int,0,100",
                    "low": "int,0,255",
                    "high": "int,0,255",
                    "bounce": "toggle,0,1",
                },
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
                "setDegree": {
                    "degree": "int,0,180",
                },
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
                "setTone": {
                    "frequency": "int,0,3000",
                    "time": "int,0,10000",
                },
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
    }
    return res


def parseCSV(p, portID):
    m = p.split(":")
    id = int(m[0]) - 1
    name = list(moduleDict().keys())[id]
    if (id == -1):
        return id
    moduleInfo = moduleDict()
    obj = moduleInfo[name]
    data = m[1].split(",")
    res = {}
    raw = obj.get('raw')
    if (raw):
        i = 0
        for k, v in raw.items():
            d = float(data[i])
            t = v.split(",")
            raw_min = float(t[1])
            raw_max = float(t[2])
            norm = (d-raw_min)/(raw_max-raw_min)
            key = "{}-{}-raw-{}".format(name, k, portID)
            res[key] = d
            key = "{}-{}-map-{}".format(name, k, portID)
            res[key] = norm
            i += 1
    return res


def parse(p, portID):
    m = p.split(":")
    id = int(m[0]) - 1
    name = list(moduleDict().keys())[id]
    if (id == -1):
        return id

    res = {
        "name": name,
        "id": id,
    }
    moduleInfo = moduleDict()
    obj = moduleInfo[name]

    data = m[1].split(",")

    raw = obj.get('raw')
    if (raw):
        res["raw"] = {}
        i = 0
        for k, v in raw.items():
            d = data[i]
            # print(k, v, type(d))
            t = v.split(",")
            match t[0]:
                case "int":
                    t[1] = int(t[1])
                    t[2] = int(t[2])
                    d = int(d)
                case "float":
                    t[1] = float(t[1])
                    t[2] = float(t[2])
                    d = float(d)
                case _:
                    pass

            res["raw"][k] = {
                "value": d, "dataType": t[0], "min": t[1], "max": t[2]
            }
            i += 1

    properties = obj.get('properties')
    if (properties):
        res["properties"] = {}
        for k, v in properties.items():
            d = res["raw"].get(k)
            if (d == None):
                continue
            dmin, dmax = d.get("min"), d.get("max")
            d = d["value"]
            t = v.split(",")
            match t[0]:
                case "int":
                    t[1] = int(t[1])
                    t[2] = int(t[2])
                    d = (d-dmin)/(dmax-dmin)*(t[2]-t[1]) + t[1]
                    d = int(d)
                case "float":
                    t[1] = float(t[1])
                    t[2] = float(t[2])
                    d = (d-dmin)/(dmax-dmin)*(t[2]-t[1]) + t[1]
                    d = float(d)
                case "bool":
                    d = bool(d)
                case _:
                    pass
            res["properties"][k] = d

    # res = res.get("properties")
    hardware = {"name": name}
    hardware["module"] = {}
    raw = {}
    for key, value in res.get("raw").items():
        raw[key] = value["value"]
    hardware["module"]["raw"] = raw
    hardware["module"]["properties"] = res.get("properties")
    hardware["data"] = data
    # res.update({"name": name})
    # return res
    return hardware


class Device:
    def __init__(self, port, simulate=False):
        self.port = port
        self.simulate = simulate
        self.ser = None
        self.initial_time = 0
        self.time = 0

    def connect(self):
        try:
            self.ser = serial.Serial(self.port, 115200, timeout=1)
            self.ser.flush()
        except serial.SerialException as e:
            print(e)
        self.initial_time = time.time()
        self.time = self.initial_time

    def read(self, format=None):
        t = time.time() - self.initial_time
        self.time = t
        if self.simulate:
            m = (math.sin(t)/2)+0.5
            line = "1:{};6:{},{};0:0;0:0;0:0;0:0;0:0;0:0;0".format(
                round(m), int(m*4095), int(m*4095))
        else:
            if self.ser != None:
                line = self.ser.readline().decode("utf-8")
            else:
                raise Exception("Device not connected.")

        data = line.split(";")

        res = None
        if format == "csv":
            res = list(map(parseCSV, data[0:8], range(0, 8)))
        else:
            res = list(map(parse, data[0:8], range(0, 8)))
        return res

    def disconnect(self):
        if self.ser != None:
            self.ser.close()
        return
