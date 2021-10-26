#minimal functions to test if the CAN bus from xsDrive works 
# prints controller outputs

from RemoteController import HIABRemoteController

controller = HIABRemoteController()

for _ in range(100000):
    print(controller.get_last_remote_msg()) #or get_last_remote_cmd()
