# imd_temperature_import.py

# separate program to process just the temperature data (which is a much smaller set), 
# and populate the grid points in a separate grid table for temperatures

import imdlib, os, time, datetime, json
import pandas as pd
import geopandas as gpd
from sqlalchemy import create_engine

start = time.time()
root = os.path.dirname(__file__)
print(root)
timeOffset = 5.5

logFolder = os.path.join(root, 'logs')

tmaxFolder = os.path.join(root,'tmax')
tminFolder = os.path.join(root,'tmin')

for folder in (tmaxFolder, tminFolder, logFolder):
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
            if row['tmax'] != '' and row['tmax'] < 999:
                obj1[row['time']]['tmax'] = row['tmax']
        if 'tmin' in cols:
            if row['tmin'] != ''  and row['tmin'] < 999:
                obj1[row['time']]['tmin'] = row['tmin']
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


for year in range(TEMP_START, TEMP_END+1 ):
    # time.sleep(5)
    logmessage(year)
    fileT = f"{year}.GRD"

    # check if file is there already. if yes, then skip downloading
    
    if not os.path.isfile(os.path.join(tmaxFolder,fileT)):
        res1 = imdlib.get_data('tmax', year, year, fn_format='yearwise')

    if not os.path.isfile(os.path.join(tminFolder,fileT)):
        res2 = imdlib.get_data('tmin', year, year, fn_format='yearwise')

    tmax1 = imdlib.open_data('tmax', year, year, 'yearwise').get_xarray().to_dataframe().fillna('')
    tmax2 = tmax1[tmax1['tmax'] < 99].reset_index()

    tmin1 = imdlib.open_data('tmin', year, year, 'yearwise').get_xarray().to_dataframe().fillna('')
    tmin2 = tmin1[tmin1['tmin'] < 99].reset_index()

    # merge temps
    df1 = pd.merge(tmax2, tmin2, how='outer', on=['time','lat','lon'], sort=False )
    
    # adapt table
    df1['month1'] = df1['time'].apply(lambda x: int(x.strftime('%-m'))) 
    # %-m : month number without zero-padding, from strftime.org
    df1['time'] = df1['time'].astype(str)
    
    # combining all records for one location in one month together
    df2 = df1.groupby(['month1','lat','lon']).apply(grouper1).reset_index(drop=False)
    df2['year1'] = year

    """
    sample 'data' column value for one location+year+month that is returned by grouper1 function:
    """

    rows_reduction = round(100*len(df2)/len(df1),2)
    logmessage(f"{year}: {round(len(df2)/1000,2)}K records; reduced to {rows_reduction}% from original count of {round(len(df1)/1000,2)}K")

    # DB
    d1 = f"delete from imd_temp_data where year1={year}"
    c = engine.connect()
    d1Res = c.execute(d1)
    c.close()
    if d1Res.rowcount:
        logmessage(f"{year}: {d1Res.rowcount} existing rows deleted")

    gdf1 = makegpd(df2)
    gdf1.to_postgis('imd_temp_data', engine, if_exists='append', index=False, chunksize=batchSize)

    logmessage(f"{year}: {round(len(df2)/1000,2)}K rows uploaded to DB")


##########

# collate distinct locations and load into temp_grid table
logmessage("Collecting distinct grid locations to load into temp_grid table")
s2 = "select distinct geometry from imd_temp_data"
gdf2 = gpd.read_postgis(s2, con=engine, geom_col='geometry')

d2 = f"delete from temp_grid"
c = engine.connect()
d2Res = c.execute(d2)
c.close()
if d2Res.rowcount:
    logmessage(f"{d2Res.rowcount} existing rows in temp_grid deleted")

gdf2.to_postgis('temp_grid', con=engine, if_exists='append', index=False)
logmessage(f"{len(gdf2)} distinct grid points having temperature data loaded into temp_grid")

##########

end = time.time()
logmessage(f"Script completed in {round((end-start)/60,1)} mins")

