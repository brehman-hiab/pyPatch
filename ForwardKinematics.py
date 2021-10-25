import numpy as np
from numpy import sin, cos
a = 2.45 # scaling parameter
l1 = 1.01*a
l2 = a
l3_max = 3.92*a 
x1,y1 = -0.24*a, 0.78*a #offset
max_boomext = 9.5 #data coming from NeoSim
#!
#! ratio from optimization x1,y1,l1,l2 [-0.19532414,  0.76244694, 1. , 1.1420685] . scaling is 2.4893467
def FKXY(NeoSimData): #takes data dict from NeoSim
    AJ1 = NeoSimData['Aj'][1]*np.pi/180
    AJ2 = NeoSimData['Aj'][2]*np.pi/180
    BoomExt = NeoSimData['Length'][2]/max_boomext*l3_max
    x,y = FKxy_(AJ1, AJ2, BoomExt)
    return x, y

def FKxy_(AJ1, AJ2, BoomExt): #takes states directly
    x = x1 + l1*cos(AJ1) + (l2+BoomExt)*cos(AJ1+AJ2) 
    y = y1 + l1*sin(AJ1) + (l2+BoomExt)*sin(AJ1+AJ2) 
    return x,y