from HIABCSUnityIO import NEOSimIO
import socket
import json
import time
import config
# this script runs just as simulatorReceiver_test.py but in a modular way, defaults to keyboard controller

from RemoteController import HIABRemoteController

controller = HIABRemoteController()
for _ in range(100):
    time.sleep(0.1)
    print(controller.get_last_remote_cmd())


#? model = NEOSimIO(controller = controller.policy)
#? model.run()