from HIABCSUnityIO import NEOSimIO
import socket
import json
import time
import config
# this script runs just as simulatorReceiver_test.py but in a modular way

#This class is part of the protocol at which Simulator is publishing information
#If Black Baron changes this and Simulator adopt then, this script needs to updated too
        
#Same as above this needs to match the simulator protocol
def BB_DataOutDummy(): #dictionary data
        return {
                'Ticks': 0,
                'SpoolOpenings':[0.0, -50.0, 50.0, 5.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
                'Signals':[41.42, 52.17, 53.64, 37.98, 35.059998, 0.0],
                'Counter':0,
                'Menu':0
        }
          
#Above classes objects
DummyControlData = BB_DataOutDummy()
model = NEOSimIO()
model.run()