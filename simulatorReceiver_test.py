import socket
import json


class BB_DataIn():
        At =[0.0,0.0,0.0]
        Aj = [0.0,0.0,0.0,0.0,0.0]
        Pressure = [0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0]
        Length = [0.0,0.0,0.0,0.0]
        Rcl =[0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0]
        Counter = int(0)
        RemoteControlButtons = int(0)
        SimulatedMs = int(0)

class BB_DataOut():
        def __init__(self):
            self.Ems = 0
            self.Ctrl = [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
            self.Signals=[0.0,0.0,0.0,0.0,0.0,0.0]
            self.Counter=0
            self.Menu=0
        
#Use port 5555 to recive this from simulator and 4444 from Blackbaron, later from Sumulink
def setUpUDP(UDP_IP = "127.0.0.1",UDP_PORT = 4444):
        print("Inside Set Up UDP")
        sock = socket.socket(socket.AF_INET, # Internet
                     socket.SOCK_DGRAM) # UDP
        #sock.settimeout(10.1)
        #sock.setblocking(1)
        sock.bind((UDP_IP, UDP_PORT))
        return sock

def rxData(sock):
        rxData, addr = sock.recvfrom(1024)
        data_dict = json.loads(rxData)
        return data_dict

def getMappedDistToObject(data_dict):
     BB_dataIn = BB_DataIn()
     BB_dataIn.At = data_dict["At"]
     BB_dataIn.Aj = data_dict["Aj"]
     BB_dataIn.Pressure = data_dict["Pressure"]
     BB_dataIn.Length = data_dict["Length"]
     BB_dataIn.Rcl= data_dict["Rcl"]
     BB_dataIn.Counter= data_dict["Counter"]
     BB_dataIn.RemoteControlButtons= data_dict["RemoteControlButtons"]
     BB_dataIn.SimulatedMs= data_dict["SimulatedMs"]
     return BB_dataIn

def getLeverMsg(lvrData):
        levers=[0, 0, 0, 0, 0, 0, 0, 0]
        levers[0]=float(lvrData[0])
        levers[1]=float(lvrData[1])
        levers[2]=float(lvrData[2])
        levers[3]=float(lvrData[3])
        levers[4]=float(lvrData[4])
        levers[5]=float(lvrData[5])
        levers[6]=float(lvrData[6])
        levers[7]=float(lvrData[7])

        return levers

def tearDownUDP(sock):
        print("Inside tear down UDP")
        sock.close()

PWM =[0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
sig = [41.42, 52.17, 53.64, 37.98, 35.059998, 0.0]




socket_sendHandle = setUpUDP(UDP_IP="127.0.0.1",UDP_PORT=4444)
DataOut_object = BB_DataOut()



#socket_handle = setUpUDP(UDP_IP = "127.0.0.1",UDP_PORT = 5555)
#DataIn_object = BB_DataIn()
counter = 0
while (counter<100000):
    print("Inside while")
    DataOut_object.Ctrl = PWM
    DataOut_object.Signals=sig
    DataOut_object.Counter=counter
    MESSAGE = json.dumps(DataOut_object.__dict__)
    #print(DataOut_object.__dict__)
    #print(json.dumps(DataOut_object.__dict__))
    socket_sendHandle.sendto(MESSAGE.encode(),("127.0.0.1",4444))
    #rx_data_dict = rxData(socket_handle)
    #rx_data_dict = rxData(socket_sendHandle)
    #print(rx_data_dict)
#    DataIn_object = getMappedDistToObject(rx_data_dict)
#    print(DataIn_object.Aj)
    counter = counter +1
#
#tearDownUDP(socket_handle)
tearDownUDP(socket_sendHandle)






#RcLever=getLeverMsg(BB_dataIn.Rcl)
#print(BB_dataIn.Aj)

#print("Data %s" % BB_DataIn_object.Aj)
