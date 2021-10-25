
## Helper classes for data IO through UDP to Unity (NeoSim) 
import config
import socket
from threading import Event
import json
import threading
import time
import os
import pickle
from ForwardKinematics import FKXY
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
        # self.sendThread = dataSendThread(self.recvThread, config.UDP_PORT_SEND_EXTRA) #extra socket to send (used in Simulink)
        # socket for sending commands to sim, opening port and sending stop
        self.soc_send =  socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        print("Socket UDP (for sending commands) initialized...")
        self.send_cmd_stop()
        self.cmd_last = self.get_cmd_stop()

        ### for data collection and control
        self.controller = controller 
        if self.controller is None:
          self.controller = self.keyboardController
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
          self.send_cmd(self.u_control)
          if self.verbose > 0:
              self.print_states()
          #log data
          self.logCurrentData()
        #finish up    
        self.safeCompletion()
    def getLeverMsg(self):
      return self.currentData['Lever']

    def select_states(self, data):
      Lever = self.getLeverMsg()[0:4]
      JointAng = data['Aj'][0:3]
      BoomExt = [data['Length'][2]] # second boom extension length 
      return JointAng + BoomExt # Lever + JointAng + BoomExt

    def select_actions(self, u):
      return u['SpoolOpenings'][0:4]

    def get_states(self):
      return self.select_states(self.currentData)

    def print_states(self):
      #print selected states
      x,y = FKXY(self.currentData) #x,y,z
      states = [f'{s:+07.2f}' for s in self.get_states()]
      states = " | ".join(states)
      actions = [f'{a:+04.0f}' for a in self.select_actions(self.u_control)]
      actions = " | ".join(actions)
      print(f't: {self.currentTime:07.2f} - States: {states} - Control: {actions} - X: {x:07.3f}, Y: {y:07.3f}')

      # or all states ################
      # print(f'Time: {self.currentTime:.2f} - States: {self.currentData}\n Action: {self.u_control}')

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

    def keyboardController(self, voidInput):
      u = self.getLeverMsg()[0:4]
      data_out = self.assemble_command_u(u)
      return data_out
    
    def assemble_command_u(self, u): #put together selected actions to a full send command template       
      #start from a dummy =0 msg
      data_out = self.get_cmd_stop() # 'SpoolOpenings' (10,)|'Signals': (6,)
      #set cmds
      data_out['SpoolOpenings'][0:len(u)] = u
      data_out['Signals'] = [200]*6
      return data_out


          
class dataThread(threading.Thread):
  '''Data acquisition thread.'''
  def __init__(self, kEvent, port_recv, recv_buffer):
    threading.Thread.__init__(self,daemon=True)
    self.kEvent = kEvent
    self.lock = threading.Lock()
    self.currentData = None
    # self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) # UDP
    # print("UDP Socket (for receiving data) initialized...")
    self.PORT = port_recv
    self.UDP_RECV_BUFF = recv_buffer
    self.HOST = ""
    self.RECV_TIME = config.SAMPLE_TIME/5

  def run(self):
    '''Data collection'''
    #! these are disabled, seems to be a unity issue
    # self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    # self.bind_socket()
    #! 
    ## self.sock.settimeout(5)
    rxData = None
    while not self.kEvent.wait(timeout=self.RECV_TIME): # better than self.kEvent.is_set() + time.sleep(SAMPLE_TIME)
        # "collect data"
        # time.sleep(self.SAMPLE_TIME)
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) # UDP
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        self.bind_socket()
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
      # print('Socket_receive bind OK.')
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

class dataSendThread(threading.Thread): #experimental
  '''Data send thread. To Simulink.'''
  def __init__(self, recvThread, port_send):
    threading.Thread.__init__(self,daemon=True)
    self.ip, self.port_send = config.SIM_IP, port_send
    self.kEvent = recvThread.kEvent
    # self.lock = threading.Lock()
    # self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) # UDP
    # print("UDP Socket (for receiving data) initialized...")
    self.PORT = port_send
    self.HOST = ""
    self.send_TIME = config.SEND_TIME_EXTRA

  def run(self):
    '''Data collection'''
    # self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    # self.sock.settimeout(5)
    while not self.kEvent.wait(timeout=self.send_TIME): # better than self.kEvent.is_set() + time.sleep(SAMPLE_TIME)
        # "collect data"
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) # UDP
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)

        data = self.recvThread.getCurrentData()
        self.send_cmd(data)

    print('Data send to Simulink is signaled to stop...')
    self.sock.close()
    print('SOCKET (send Simulink) closed...')
  
  def send_cmd(self, dict_data): #send command through this function (a dictionary data)
      try:
          # MESSAGE = json.dumps(dataObj.__dict__) #Converting to json from OBJECT
          MESSAGE = json.dumps(dict_data) #Converting to json from dict
          self.soc_send.sendto(MESSAGE.encode(),(self.ip, self.port_send)) #Sending to simulator an encoded msg 
          self.cmd_last = dict_data
      except Exception as e:
          print("Command Send Error:", e)