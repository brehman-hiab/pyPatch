
## Helper classes for data IO through UDP to Unity (NeoSim) 
import config
import socket
from threading import Event
import json
import threading
import time
import os
import pickle
# ------ IO Module----- 
'''
*starts a thread to continuously recieve data, sends commands to sim  
*list of data, if empty: 
    At =[0.0,0.0,0.0] #%tilt
    Aj = [0.0,0.0,0.0,0.0,0.0] #joint (deg)
    Pressure = [0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0]
    Length = [0.0,0.0,0.0,0.0]
    Lever =[0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0]
    Counter = int(0)
    RemoteControlButtons = int(0)
    SimulatedMs = int(0)

'''
class NEOSimIO():
    def __init__(self, controller=None, Tf = 1000, log_path=None, verbose=1):
        ### communication units        
        self.ip = config.SIM_IP
        self.port_recv = config.UDP_PORT_RECV # for reading data from simulator
        self.port_send = config.UDP_PORT_SEND # for sending control data to simulator
        self.kEvent = Event() #event that runs through the threads
        # module to receive data continuously
        self.recvThread = dataThread(self.kEvent, self.port_recv, config.UDP_RECV_BUFF)
        self.recvThread.start() # enabling data receiving
        self.kEvent.wait(timeout=1) #wait for dataThread to run
        # socket for sending commands to sim, opening port and sending stop
        self.soc_send =  socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        print("Socket UDP (for sending commands) initialized...")
        self.send_cmd_stop()
        self.cmd_last = self.get_cmd_stop()

        ### for data collection and control
        self.controller = controller 
        if self.controller is None:
          self.controller = self.passiveController
        self.verbose = verbose
        self.StartTime = time.time()
        self.Tfinal = Tf #will stop running if time exceeds this value
        self.checkptCurrentTime()
        self.lastcheckpointTime = self.currentTime 
        self.checkpoint_dt = config.SAMPLE_TIME
        # self.log_keys = ['time', 'u', 'data'] #save these variables
        self.logs = {'time':[], # time
                      'u':[], # sent commands to sim
                      'data':[] } # received data from sim
        self.log_path = log_path
        if self.log_path is None:
          self.log_path = './temp/'
        os.makedirs(self.log_path, exist_ok=True)
        self.file_path =  self.log_path + '_data.pkl'

    def checkptCurrentTime(self):
        self.currentTime = time.time() - self.StartTime

    def get_data(self):
        data = self.recvThread.getCurrentData()
        return data

    def send_cmd_stop(self): #send stop command
        self.send_cmd(self.get_cmd_stop())

    def get_cmd_stop(self): #returns a template dict for sending data 
        return {'Ticks': 0,
                'SpoolOpenings': [0.0]*10,
                'Signals': [0.0]*6, 
                'Counter': 0,
                'Menu': 0}

    def send_cmd(self, dict_data): #send command through this function (a dictionary data)
        try:
            # MESSAGE = json.dumps(dataObj.__dict__) #Converting to json from OBJECT
            MESSAGE = json.dumps(dict_data) #Converting to json from dict
            self.soc_send.sendto(MESSAGE.encode(),(self.ip, self.port_send)) #Sending to simulator an encoded msg 
            self.cmd_last = dict_data
        except Exception as e:
            print("Command Send Error:", e)
    
    def run(self):
        while not self.kEvent.wait(self.checkpoint_dt/2):
          self.checkptCurrentTime()          
          ## time control functions 
          # while (self.currentTime - self.lastcheckpointTime) <= self.checkpoint_dt: 
          #     self.checkptCurrentTime()
          # self.lastcheckpointTime = self.currentTime
          if (self.currentTime > self.Tfinal): 
            print(f"Timeout of {self.Tfinal:.1f} reached... ")    
            self.safeCompletion()

          self.currentData = self.get_data()
          self.u_control = self.controller(self)
          
          if self.verbose > 0:
              self.print_states()
          #log data
          self.logCurrentData()
        #finish up    
        self.safeCompletion()

    def print_states(self):
      #print selected or all states ################
      print(f'Time: {self.currentTime:.2f} - States: {self.currentData}\n Action: {self.u_control}')

    def safeCompletion(self):
        """
        safely kills the main running event, stops the execution of main loops in connected threads, then saves and cleans up 
        """
        # //TODO send stop/reset commands to simulator here
        # time.sleep(0.1)
        self.safeKill()
        print('Finishing Run...')
        self.saveExperiment()

    def safeKill(self):
        "safely kills the main running event, use safeCompletion() to save the collected data"
        print('Sending Stop Command...')
        self.send_cmd_stop()
        print('Stopping All Threads...')
        self.kEvent.set()

    def logCurrentData(self):
        self.logs['time'].append(self.currentTime)
        self.logs['u'].append(self.u_control)
        self.logs['data'].append(self.currentData)

    def saveExperiment(self):
        self.save_to_file(self.logs, self.filepath)
    def save_to_file(self, data, filepath):
        with open(filepath, 'wb') as f:
            pickle.dump(data, f)

    def passiveController(self, voidInput):
      #for testing functionality
      return self.get_cmd_stop()

            
class dataThread(threading.Thread):
  '''Data acquisition thread.'''
  def __init__(self, kEvent, port_recv, recv_buffer):
    threading.Thread.__init__(self,daemon=True)
    self.kEvent = kEvent
    self.lock = threading.Lock()
    self.currentData = None
    self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) # UDP
    print("UDP Socket (for receiving data) initialized...")
    self.PORT = port_recv
    self.UDP_RECV_BUFF = recv_buffer
    self.HOST = ""
    self.RECV_TIME = config.SAMPLE_TIME/5

  def run(self):
    '''Data collection'''
    self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    # self.sock.settimeout(5)
    self.bind_socket()
    rxData = None
    while not self.kEvent.wait(timeout=self.RECV_TIME): # better than self.kEvent.is_set() + time.sleep(SAMPLE_TIME)
        # "collect data"
        # time.sleep(self.SAMPLE_TIME)
        rxData, _ = self.sock.recvfrom(self.UDP_RECV_BUFF)
        # set data, use locking
        self.setData(rxData)
    print('Data Acquisition is signaled to stop...')
    self.sock.close()
    print('SOCKET (receive) closed...')

  def bind_socket(self):
    try:
    # binding host and port
      self.sock.bind((self.HOST, self.PORT))
      print('Socket_receive bind OK.')
    except socket.error as massage:
      # if any error occurs then with the 
      # help of sys.exit() exit from the program
      print('Socket_receive bind failed. Error Code : ' 
            + str(massage[0]) + ' Message ' 
            + massage[1])
      raise ConnectionRefusedError
  
  def setData(self, data):
    self.lock.acquire()
    self.currentData = self.json2dict(data)
    self.lock.release()

  def json2dict(self, data):
    data_dict = json.loads(data)
    return data_dict

  def getCurrentData(self): 
    '''Get current data value, returns a dict.'''
    # get data, use locking
    self.lock.acquire()
    data = self.currentData
    self.lock.release()
    return data
    