import can
from can.interfaces import pcan 
from time import sleep

class HIABRemoteController():
    def __init__(self) -> None:
        self.Bus = PCANBus()

    def get_last_remote_cmd(self):
        return self.Bus.get_last_cmd()
    
    def policy(self, voidNeoSimObject):
      u = self.get_last_remote_cmd()[0:4] #self.getLeverMsg()[0:4]
      data_out = self.assemble_command_u(u, voidNeoSimObject)
      return data_out
    
    def assemble_command_u(self, u, voidNeoSimObject): #put together selected actions to a full send command template       
      #start from a dummy =0 msg
      data_out = voidNeoSimObject.get_cmd_stop() # 'SpoolOpenings' (10,)|'Signals': (6,)
      #set cmds
      data_out['SpoolOpenings'][0:len(u)] = u
      data_out['Signals'] = [200]*6
    #   data_out['Signals'][0:len(u)] = u
      return data_out
# # # set PCAN-USB bus number (starts from 1)
# b =  pcan.PcanBus(channel = 'PCAN_USBBUS1', bitrate = 125000)
# listener = SomeListener()
# msg = my_bus.recv()

# # now either call
# listener(msg)
# # or
# listener.on_message_received(msg)

# # Important to ensure all outputs are flushed
# listener.stop()


import logging


def _get_message(msg):
    return msg

class PCANBus(object):
    def __init__(self):
        self.bus = pcan.PcanBus(channel = 'PCAN_USBBUS1', bitrate = 125000)
        self.buffer = can.BufferedReader()
        self.notifier = can.Notifier(self.bus, [_get_message, self.buffer])
        self.msg_aid = int('0x500', 16)  # = int('0x500', 16) = 1280
    
    def send_message(self, message):
        try:
            self.bus.send(message)
            return True
        except can.CanError:
            logging.error("message not sent!")
            return False

    def flush_buffer(self):
        msg = self.buffer.get_message()
        while (msg is not None):
            msg = self.buffer.get_message()

    def cleanup(self):
        self.notifier.stop()
        self.bus.shutdown()

    def get_last_cmd(self):
        a_id = None
        # while (a_id ~= self.msg_aid)
        for _ in range(10000):
            msg = self.buffer.get_message()
            while msg is not None:
                if msg.arbitration_id==self.msg_aid:
                    print(msg)
                    # return msg
                msg = self.buffer.get_message()
                    
            self.sendAliveMsgs()
        u = 1
        return u

    def sendAliveMsgs(self): #from xsDrtoROS
        aliveMsg = [1, 1, 1, 1, 1, 1, 1, 1] #Need to send this msg to xsDrive start up
        aliveMsg2 = [3,1,1,1,1,1,0x98,1] #Need to send this msg to xsDrive start up        
        self.send_message(can.Message(arbitration_id=1024, data=aliveMsg))
        self.send_message(can.Message(arbitration_id=1025, data=aliveMsg))
        self.send_message(can.Message(arbitration_id=1040, data=aliveMsg))
        self.send_message(can.Message(arbitration_id=1048, data=aliveMsg))
        self.send_message(can.Message(arbitration_id=1312, data=aliveMsg2))
