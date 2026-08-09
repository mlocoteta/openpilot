#!/usr/bin/env python3
import time
import math
import cereal.messaging as messaging

def main():
  print("Starting fake CSC demo publisher (Curve Speed Controller)...")
  
  # Create a PubMaster for the required services
  pm = messaging.PubMaster(['starpilotPlan'])
  
  # Publish at 20Hz
  rate = 0.05 
  
  while True:
    now = time.time()
    
    # Fake StarPilot Plan
    sp = messaging.new_message('starpilotPlan')
    
    # 8-second cycle stepping through all 4 color spectrums:
    # 0s - 2s: Green  (Low curvature, t = 0.0)
    # 2s - 4s: Amber  (Medium curvature, t = 0.38)
    # 4s - 6s: Orange (High curvature, t = 0.56)
    # 6s - 8s: Red    (Max curvature, t = 1.0)
    t = now % 8.0
    
    sp.starpilotPlan.cscControllingSpeed = True
    sp.starpilotPlan.cscTraining = False
    
    if t < 2.0:
      # Green phase
      sp.starpilotPlan.roadCurvature = 0.0000
    elif t < 4.0:
      # Amber/Yellow phase
      sp.starpilotPlan.roadCurvature = 0.0080
    elif t < 6.0:
      # Orange phase
      sp.starpilotPlan.roadCurvature = 0.0115
    else:
      # Red phase
      sp.starpilotPlan.roadCurvature = 0.0200
      
    pm.send('starpilotPlan', sp)
    
    time.sleep(rate)

if __name__ == "__main__":
  main()
