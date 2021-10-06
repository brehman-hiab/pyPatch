from HIABCSUnityIO import NEOSimIO
import socket
import json
import time
import config
# this script runs just as simulatorReceiver_test.py but in a modular way, defaults to keyboard controller

model = NEOSimIO()
model.run()