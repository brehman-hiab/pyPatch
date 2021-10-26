from HIABCSUnityIO import NEOSimIO
import socket
import json
import time
import config
import numpy as np
from io import BytesIO
# this script runs just as simulatorReceiver_test.py but in a modular way, defaults to keyboard controller

from RemoteController import HIABRemoteController

controller = HIABRemoteController()

model = NEOSimIO(controller = controller.policy)
model.run()