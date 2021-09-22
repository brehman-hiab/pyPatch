import socket
import json
import time

#This class is part of the protocol at which Simulator is publishing information
#If Black Baron changes this and Simulator adopt then, this script needs to updated too
class BB_DataIn():
        At =[0.0,0.0,0.0]
        Aj = [0.0,0.0,0.0,0.0,0.0]
        Pressure = [0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0]
        Length = [0.0,0.0,0.0,0.0]
        Lever =[0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0]
        Counter = int(0)
        RemoteControlButtons = int(0)
        SimulatedMs = int(0)
#Same as above this needs to match the simulator protocol
class BB_DataOut():
        def __init__(self):
            self.Ticks = 0
            self.SpoolOpenings = [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
            self.Signals=[0.0,0.0,0.0,0.0,0.0,0.0]
            self.Counter=0
            self.Menu=0
        
#Use port 5555 to recive this from simulator and 4444 from Sumulink/Python Scripts
def setUpUDP(UDP_IP = "127.0.0.1",UDP_PORT = 4444):
        print("Inside Set Up UDP")
        sock = socket.socket(socket.AF_INET, # Internet
                     socket.SOCK_DGRAM) # UDP
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

#This is dummy message for testing
PWM =[0.0, -50.0, 50.0, 5.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
sig = [41.42, 52.17, 53.64, 37.98, 35.059998, 0.0]

#Above classes objects
DataIn_object = BB_DataIn()
DataOut_object = BB_DataOut()

#Need to create an handle for scoket to send msg to Simulator
socket_sendHandle = setUpUDP(UDP_IP="127.0.0.1",UDP_PORT=4444)

#Need to create an handle for scoket to get msg from Simulator
socket_receivehandle = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
socket_receivehandle.bind(("127.0.0.1", 5555)) #Only required for receiving handle

counter = 0
while (counter<1000):
    #print("Inside while")
    DataOut_object.SpoolOpenings = PWM #Assigning dummy msg to the object
    DataOut_object.Signals=sig #Assigning dummy msg to the object
    DataOut_object.Counter=counter #Assigning dummy msg to the object
    MESSAGE = json.dumps(DataOut_object.__dict__) #Converting to json
    socket_sendHandle.sendto(MESSAGE.encode(),("127.0.0.1",4444)) #Sending to simulator an encoded msg 
    rx_data_dict = rxData(socket_receivehandle) #Getting msg decoded from simulator 
    print(rx_data_dict) #Prinding recevide info
    counter = counter +1


tearDownUDP(socket_sendHandle) #closing the socket
tearDownUDP(socket_receivehandle) #closing the socket
