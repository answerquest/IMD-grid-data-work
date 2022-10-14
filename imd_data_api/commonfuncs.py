#commonfuncs.py
import json, os, time, datetime, secrets # uuid
import pandas as pd
# from math import sin, cos, sqrt, atan2, radians
import haversine

root = os.path.dirname(__file__)
timeOffset = 5.5
maxThreads = 8

logFolder = os.path.join(root,'logs')
os.makedirs(logFolder, exist_ok=True)


def logmessage( *content ):
    global timeOffset
    timestamp = '{:%Y-%m-%d %H:%M:%S} :'.format(datetime.datetime.utcnow() + datetime.timedelta(hours=timeOffset)) # from https://stackoverflow.com/a/26455617/4355695
    line = ' '.join(str(x) for x in list(content)) # from https://stackoverflow.com/a/3590168/4355695
    print(timestamp,line) # print to screen also

    logFilename = 'log.txt'
    if root.startswith('/mnt/PERSONAL'): logFilename = 'local_log.txt'
    
    with open(os.path.join(logFolder,logFilename), 'a') as f:
        print(timestamp, line, file=f) # file=f argument at end writes to file. from https://stackoverflow.com/a/2918367/4355695

def makeError(message):
    logmessage(message)
    return 400, json.dumps({"status":"error","message":message}, default=str)

def makeSuccess(returnD={}):
    returnD['status'] = 'success'
    return 200, json.dumps(returnD, default=str)


def makeTimeString(x, offset=5.5, format="all"):
    '''
    format values: all, time, date
    '''
    # logmessage(type(x))
    if isinstance(x, pd._libs.tslibs.nattype.NaTType) : return ''
    
    if isinstance(x, (pd._libs.tslibs.timestamps.Timestamp,datetime.datetime, datetime.date) ):
        if format == 'time':
            return (x + datetime.timedelta(hours=offset)).strftime('%H:%M:%S')
        elif format == 'date':
            return (x + datetime.timedelta(hours=offset)).strftime('%Y-%m-%d')
        else:
            # default: all
            return (x + datetime.timedelta(hours=offset)).strftime('%Y-%m-%d %H:%M')
    else:
        return ''


def quoteNcomma(a):
    # turn array into sql IN query string: 'a','b','c'
    holder = []
    for n in a:
        holder.append("'{}'".format(n))
    return ','.join(holder)


def keyedJson(df, key='trainNo'):
    arr = df.to_dict(orient='records')
    keysList = sorted(df[key].unique().tolist())
    returnD = {}
    for keyVal in keysList:
        returnD[keyVal] = df[df[key]==keyVal].to_dict(orient='records')
    return returnD
    

def IRdateConvert(x):
    # sample: "26 Feb 2021", "4 Mar 2021", "-"
    if x == '-': return None
    x2 = datetime.datetime.strptime(x, '%d %b %Y').strftime('%Y-%m-%d')
    return x2


def parseParams(url):
    # from https://stackoverflow.com/a/5075477/4355695
    parsed = urlparse.urlparse(url)
    return parse_qs(parsed.query)


# def makeUID(nobreaks=False):
#     if nobreaks:
#         return uuid.uuid4().hex
#     else:
#         return str(uuid.uuid4())

def makeUID(length=4):
    return secrets.token_urlsafe(length).upper()


def getDate(timeOffset=5.5, daysOffset=0, returnObj=False):
    d = datetime.datetime.utcnow().replace(microsecond=0) + datetime.timedelta(hours=timeOffset) + datetime.timedelta(days=daysOffset)
    if returnObj: return d
    return d.strftime('%Y-%m-%d')

def getTime(timeOffset=5.5, secsOffset=0, returnObj=False):
    d = datetime.datetime.utcnow().replace(microsecond=0) + datetime.timedelta(hours=timeOffset) + datetime.timedelta(seconds=secsOffset)
    if returnObj: return d
    return d.strftime('%Y-%m-%d %H:%M:%S')

def assignUID(df, col='id', length=4):
    ids = [makeUID(length) for x in range(len(df))]
    return pd.Series(ids)


# quick lambda function to zap a string
zapper = lambda x: ''.join(e.lower() for e in str(x) if e.isalnum())


# make proper gtfs time string
def timeFormat(x):
    # getting rid of artefacts: from question itself in https://stackoverflow.com/questions/947776/strip-all-non-numeric-characters-except-for-from-a-string-in-python
    x = ''.join([c for c in x if c in '1234567890:'])
    
    holder1 = x.split(':')
    if len(holder1) < 2:
        # if it's like '1320' then interpret it
        justnum = holder1[0]
        if justnum == '':
            # blank string
            return ''
        if len(justnum) in [3,4]:
            holder1 = [ justnum[:-2], justnum[-2:] ]
            logmessage("Special case: {} becomes {}".format(justnum,holder1))
        else:
            logmessage('{} is an invalid time string. Skipping it.'.format(x))
            # raise ValueError("'{}' is an invalid time string.".format(x))
            return ''
    hh = holder1[0].rjust(2,'0')
    mm = holder1[1].rjust(2,'0')
    if len(holder1) >= 3: ss = holder1[2].rjust(2,'0')
    else: ss = '00'
    return "{}:{}:{}".format(hh,mm,ss)


# def lat_long_dist(lat1,lon1,lat2,lon2):
#     # function for calculating ground distance between two lat-long locations
#     R = 6373.0 # approximate radius of earth in km. 

#     lat1 = radians( float(lat1) )
#     lon1 = radians( float(lon1) )
#     lat2 = radians( float(lat2) )
#     lon2 = radians( float(lon2) )

#     dlon = lon2 - lon1
#     dlat = lat2 - lat1

#     a = sin(dlat / 2)**2 + cos(lat1) * cos(lat2) * sin(dlon / 2)**2
#     c = 2 * atan2(sqrt(a), sqrt(1 - a))

#     distance = round(R * c, 2)
#     return distance

def computeDistance(sequencedf):
    prevLat = prevLon = 0 # dummy initiation
    total_dist = 0
    for N in range(len(sequencedf)):
        lat = float(sequencedf.at[N,'stop_lat'])
        lon = float(sequencedf.at[N,'stop_lon'])
        
        if N == 0:
            sequencedf.at[N,'ll_dist'] = 0
        else:
            #sequencedf.at[N,'ll_dist'] = lat_long_dist(lat,lon, prevLat,prevLon)
            sequencedf.at[N,'ll_dist'] = round(haversine.haversine((lat,lon),(prevLat,prevLon)),2)
            # https://towardsdatascience.com/calculating-distance-between-two-geolocations-in-python-26ad3afe287b
        
        total_dist += sequencedf.at[N,'ll_dist']
        sequencedf.at[N,'ll_dist_traveled'] = round(total_dist,2)
        prevLat = lat
        prevLon = lon
        
    return round(total_dist,2)
    # even the original sequencedf passed is changed with the ll_dist and ll_dist_traveled columns added, unless a copy was passed in.


def validateLL(lat, lon):
    try:
        lat = float(lat)
        lon = float(lon)
    except:
        return False
    
    if not isinstance(lat, (int, float)): return False
    if not isinstance(lon, (int, float)): return False

    latLimits = (-90,90)
    lonLimits = (-180,180)

    if lat < latLimits[0] or lat > latLimits[1]: return False
    if lon < lonLimits[0] or lon > lonLimits[1]: return False
    return True


# time calculations
def time2secs(hhmmss):
    hhmmss = hhmmss.replace("'","")
    holder1 = hhmmss.split(':')
    if len(holder1) < 2:
        logmessage('{} is an invalid time string.'.format(hhmmss))
        raise ValueError("'{}' is an invalid time string.".format(hhmmss))
    hh = int(float(holder1[0]))
    mm = int(float(holder1[1]))
    if len(holder1) >= 3: ss = int(float(holder1[2])) # taking precautions for cases like '0.0' - first parse float, then int
    else: ss = 0
    return (hh*3600 + mm*60 + ss)

def secs2time(secs):
    # data cleaning: secs must be int
    secs = int(float(secs))
    hh = str(int(secs/3600)).rjust(2,'0')
    remaining = secs % 3600
    mm = str(int(remaining/60)).rjust(2,'0')
    ss = str(remaining % 60).rjust(2,'0')
    return "{}:{}:{}".format(hh,mm,ss)

def timeDiff(t1,t2,formatted=True):
    diff = time2secs(t2) - time2secs(t1)
    if diff < 0:
        logmessage("Yo time travel man: {} to {}".format(t1,t2))
        diff = 0 - diff
    # convert the diff back into hh:mm:ss format
    if formatted:
        return secs2time(diff)
    else:
        return diff

def timeAdd(t1,delta):
    return secs2time( time2secs(t1) + delta)


def getEpochTime():
    # fetch time in microsecs
    return time.time_ns() // pow(10,3)

def checkAge(t1):
    t2 = getEpochTime()
    return (t2 - t1) / pow(10,6) # convert microsecs to secs

