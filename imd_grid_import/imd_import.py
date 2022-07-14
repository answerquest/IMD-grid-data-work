# imd_download.py

import imdlib, os, time, datetime, json
import pandas as pd
import geopandas as gpd
from sqlalchemy import create_engine

start = time.time()
root = os.path.dirname(__file__)
print(root)
timeOffset = 5.5

logFolder = os.path.join(root, 'logs')

rainFolder = os.path.join(root,'rain')
tmaxFolder = os.path.join(root,'tmax')
tminFolder = os.path.join(root,'tmin')

for folder in (rainFolder, tmaxFolder, tminFolder, logFolder):
    os.makedirs(folder, exist_ok=True)


##################
# FUNCTIONS

def logmessage( *content ):
    global timeOffset
    timestamp = '{:%Y-%m-%d %H:%M:%S} :'.format(datetime.datetime.utcnow() + datetime.timedelta(hours=timeOffset)) # from https://stackoverflow.com/a/26455617/4355695
    line = ' '.join(str(x) for x in list(content)) # from https://stackoverflow.com/a/3590168/4355695
    print(timestamp, line) # print to screen also
    filename = 'log.txt'
    if root.startswith('/mnt/PERSONAL/'):
        filename = 'local_log.txt'
    with open(os.path.join(logFolder,filename), 'a') as f:
        print(timestamp, line, file=f) # file=f argument at end writes to file. from https://stackoverflow.com/a/2918367/4355695


def makegpd(x,lat='lat',lon='lon'):
    gdf = gpd.GeoDataFrame(x, geometry=gpd.points_from_xy(x[lon],x[lat]), crs="EPSG:4326")
    gdf.drop(columns=[lat,lon], inplace=True)
    return gdf


def grouper1(x):
    returnD = {}
    obj1 = {}
    dates = x['time'].unique().tolist()
    cols = x.columns.tolist()
    for row in x.to_dict(orient='records'):
        obj1[row['time']] = {}
        if 'tmax' in cols:
            if row['tmax'] != '':
                obj1[row['time']]['tmax'] = row['tmax']
        if 'tmin' in cols:
            if row['tmin'] != '':
                obj1[row['time']]['tmin'] = row['tmin']
        if 'rain' in cols:
            if row['rain'] != '':
                obj1[row['time']]['rain'] = row['rain']
    returnD = { 'data': json.dumps(obj1) }
    return pd.Series(returnD)


##################
# DB CONNECT

creds = { 
    'DB_SERVER': os.environ.get('DB_SERVER',''),
    'DB_DBNAME': os.environ.get('DB_DBNAME',''),
    'DB_USER': os.environ.get('DB_USER',''),
    'DB_PW': os.environ.get('DB_PW',''),
    'DB_PORT': os.environ.get('DB_PORT','5432')
}
engine = create_engine(f"postgresql://{creds['DB_USER']}:{creds['DB_PW']}@{creds['DB_SERVER']}:{creds['DB_PORT']}/{creds['DB_DBNAME']}")

batchSize = int(os.environ.get('BATCH_SIZE','100000'))

##################
# MAIN PROG

TEMP_START = int(os.environ.get('TEMP_START','2015'))
TEMP_END = int(os.environ.get('TEMP_END','2020'))
TEMP_DISABLE = os.environ.get('TEMP_DISABLE','N')

RAIN_START= int(os.environ.get('RAIN_START','2015'))
RAIN_END= int(os.environ.get('RAIN_END','2016'))

if TEMP_DISABLE != 'Y':
    allStart = min(TEMP_START, RAIN_START)
    allEnd = max(TEMP_END, RAIN_END)
else:
    allStart = RAIN_START
    allEnd = RAIN_END

# TEMP
for year in range(allStart, allEnd+1 ):
    time.sleep(5)
    logmessage(year)
    fileT = f"{year}.GRD"
    fileR = f"{year}.grd"

    tempFlag = False
    rainFlag = False

    # check if file is there already. if yes, then skip downloading
    
    if year >= TEMP_START and year <= TEMP_END and TEMP_DISABLE != 'Y':
        tempFlag = True
        if not os.path.isfile(os.path.join(tmaxFolder,fileT)):
            res1 = imdlib.get_data('tmax', year, year, fn_format='yearwise')

        if not os.path.isfile(os.path.join(tminFolder,fileT)):
            res2 = imdlib.get_data('tmin', year, year, fn_format='yearwise')

        tmax1 = imdlib.open_data('tmax', year, year, 'yearwise').get_xarray().to_dataframe()
        tmax2 = tmax1[tmax1['tmax'] < 99].reset_index()

        tmin1 = imdlib.open_data('tmin', year, year, 'yearwise').get_xarray().to_dataframe()
        tmin2 = tmin1[tmin1['tmin'] < 99].reset_index()

        # merge temps
        df1 = pd.merge(tmax2, tmin2, how='outer', on=['time','lat','lon'], sort=False )
    else:
        df1 = pd.DataFrame()

    
    if year >= RAIN_START and year <= RAIN_END:
        rainFlag = True
        if not os.path.isfile(os.path.join(rainFolder,fileR)):
            res3 = imdlib.get_data('rain', year, year, fn_format='yearwise')

        rain1 = imdlib.open_data('rain', year, year, 'yearwise').get_xarray().to_dataframe()
        rain2 = rain1[rain1['rain'] > -100].reset_index()
    else:
        rain2 = pd.DataFrame()
    
    if tempFlag and rainFlag:
        # merge with rain
        df2 = pd.merge(df1, rain2, how='outer', on=['time','lat','lon'], sort=False ).fillna('')
    elif tempFlag:
        df2 = df1
    elif rainFlag:
        df2 = rain2
    else:
        continue

    # adapt table
    df2['month1'] = df2['time'].apply(lambda x: int(x.strftime('%-m'))) 
    # %-m : month number without zero-padding, from strftime.org
    df2['time'] = df2['time'].astype(str)
    
    # combining all records for one location in one month together
    df3 = df2.groupby(['month1','lat','lon']).apply(grouper1).reset_index(drop=False)
    df3['year1'] = year

    """
    sample 'data' column value for one location+year+month that is returned by grouper1 function:
    {"1901-01-01": {"rain": 0.0}, "1901-01-02": {"rain": 0.0}, "1901-01-03": {"rain": 0.0}, "1901-01-04": {"rain": 4.105218410491943}, "1901-01-05": {"rain": 0.0}, "1901-01-06": {"rain": 0.0}, "1901-01-07": {"rain": 0.0}, "1901-01-08": {"rain": 0.0}, "1901-01-09": {"rain": 0.0}, "1901-01-10": {"rain": 4.69198751449585}, "1901-01-11": {"rain": 0.0}, "1901-01-12": {"rain": 0.0}, "1901-01-13": {"rain": 0.0}, "1901-01-14": {"rain": 0.0}, "1901-01-15": {"rain": 0.0}, "1901-01-16": {"rain": 0.0}, "1901-01-17": {"rain": 0.0}, "1901-01-18": {"rain": 0.7860288619995117}, "1901-01-19": {"rain": 5.037391662597656}, "1901-01-20": {"rain": 47.343116760253906}, "1901-01-21": {"rain": 18.70335578918457}, "1901-01-22": {"rain": 0.0}, "1901-01-23": {"rain": 0.0}, "1901-01-24": {"rain": 0.0}, "1901-01-25": {"rain": 0.0}, "1901-01-26": {"rain": 0.0}, "1901-01-27": {"rain": 0.0}, "1901-01-28": {"rain": 0.0}, "1901-01-29": {"rain": 0.0}, "1901-01-30": {"rain": 0.0}, "1901-01-31": {"rain": 0.0}}
    """

    rows_reduction = round(100*len(df3)/len(df2),2)
    logmessage(f"{year}: {round(len(df3)/1000,2)}K records; reduced to {rows_reduction}% from original count of {round(len(df2)/1000000,2)}M")

    # DB
    d1 = f"delete from imd_data where year1={year}"
    c = engine.connect()
    d1Res = c.execute(d1)
    c.close()
    if d1Res.rowcount:
        logmessage(f"{year}: existing rows deleted")

    gdf1 = makegpd(df3)
    gdf1.to_postgis('imd_data', engine, if_exists='append', index=False, chunksize=batchSize)

    logmessage(f"{year}: {round(len(df3)/1000,2)}K rows uploaded to DB")
    
    # merge: how='outer' from https://pandas.pydata.org/pandas-docs/stable/reference/api/pandas.DataFrame.merge.html

end = time.time()
logmessage(f"Script completed in {round((end-start)/60,1)} secs")

