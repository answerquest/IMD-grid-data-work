# globals.py

from fastapi import HTTPException
import commonfuncs as cf
import os

root = os.path.dirname(__file__)

vizFolder = os.path.join(root,'viz')
os.makedirs(vizFolder, exist_ok=True)

ipTracker = {} # in-memory json db - could replace at a later time with red-- nah, yawn

defaultRateLimit = 5

def logIP(X_Forwarded_For, action, limit=defaultRateLimit):
    global ipTracker
    if not X_Forwarded_For:
        X_Forwarded_For = 'localhost'

    if not ipTracker.get(X_Forwarded_For, False):
        ipTracker[X_Forwarded_For] = {action: cf.getEpochTime()}
        return
    else:
        if not ipTracker[X_Forwarded_For].get(action, False):
            ipTracker[X_Forwarded_For][action] = cf.getEpochTime()
            return
        else:
            # check last usage
            lastHit = ipTracker[X_Forwarded_For][action]
            age = cf.checkAge(lastHit)
            if age <= limit:
                raise HTTPException(status_code=429, detail=f"Rate limited, pls try after {limit} secs")
            else:
                ipTracker[X_Forwarded_For][action] = cf.getEpochTime()
                return
    