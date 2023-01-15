# api_data.py

from typing import Optional, List
from pydantic import BaseModel
from fastapi.responses import Response
from fastapi import HTTPException, Header, File, UploadFile, Form, status

import pandas as pd
import os, random
import matplotlib.pyplot as plt
from matplotlib.ticker import MultipleLocator
from io import BytesIO

# from imdapi_launch import app
from imdapi_launch import app
import commonfuncs as cf
import dbconnect
from globalvars import logIP, vizFolder


root = os.path.dirname(__file__)

###################

@app.get("/API/initialData", tags=["data"])
def initialData(which: Optional[str]="temp", X_Forwarded_For: Optional[str] = Header(None)):
    cf.logmessage("initialData api call")
    logIP(X_Forwarded_For, 'list', limit=1)
    returnD = {}
    
    # load grid from saved CSV
    gridFile = os.path.join(root, 'imd_rain_Vs_temp_grid.csv')
    griddf1 = pd.read_csv(gridFile, dtype=str, keep_default_na=False)

    # locations
    if which.lower() == 'temp':
        # s1 = f"""select sr, ST_Y(geometry) as lat, ST_X(geometry) as lon from temp_grid"""
        griddf2 = griddf1[griddf1['temp_sr'] != 'NULL'][['lat','lon']].copy().reset_index(drop=True)
        returnD['locations'] = griddf2.to_csv(index=False)
    else:
        # s1 = f"""select sr, ST_Y(geometry) as lat, ST_X(geometry) as lon from grid"""
        returnD['locations'] = griddf1.to_csv(index=False)

    
    
    # years
    if which.lower() == 'temp':
        s2 = f"""select distinct year1 from imd_temp_data"""
    else:
        s2 = f"""select distinct year1 from imd_data"""
    
    returnD['years'] =  dbconnect.makeQuery(s2, output='column')

    return returnD


# class fetchDataReq(BaseModel):
#     which: Optional[str] = "all"
#     year: int
#     lat: float
#     lon: float

@app.get("/API/fetchData", tags=["data"])
async def fetchData(year:int, lat:float, lon:float, which:Optional[str] = "all", 
        token: Optional[str] = None ,
        X_Forwarded_For: Optional[str] = Header(None)
    ):
    cf.logmessage("fetchData api call")
    
    
    # token validation
    if token:
        s1 = f"select userid from sessions where token='{token}'"
        userid = dbconnect.makeQuery(s1, output='oneValue')
        if not userid:
            raise HTTPException(status_code=401, detail="Invalid token; pls login again")
            return
        # allow more hits if token is present
        logIP(str(userid), 'fetchData', limit=0.2)
    else:
        # open apis : restrict hits
        if not X_Forwarded_For: X_Forwarded_For = 'localhost'
        logIP(X_Forwarded_For, 'fetchData_anon', limit=10)

    which = which.lower()
    if which not in ('all','rain','temp'):
        raise HTTPException(status_code=400, detail="Invalid which - should be all, rain or temp, omit for default all")
        return
    if which in ('all','rain'):
        s1 = f"""select data from imd_data
        where year1 = {year}
        and geometry = ST_GeomFromText('POINT({lon} {lat})',4326)
        order by month1
        """
    else:
        s1 = f"""select data from imd_temp_data
        where year1 = {year}
        and geometry = ST_GeomFromText('POINT({lon} {lat})',4326)
        order by month1
        """
    # get an array of jsons
    arr1 = dbconnect.makeQuery(s1, output='column')
    if not len(arr1):
        return {'success':False, 'message': "No data for give location / year"}

    # convert each json in the array into a df
    arr2 = [pd.DataFrame(x).transpose().reset_index().rename(columns={'index':'date'}) for x in arr1]
    
    # concatenate the dfs into one
    df1 = pd.concat(arr2, sort=False, ignore_index=True)

    # just sanity check
    if not len(df1):
        return {'success':False, 'message': "No data for give location / year"}

    df1['latitude'] = lat
    df1['longitude'] = lon
    
    if which == 'rain':
        df1.drop(columns=['tmin','tmax'], inplace=True, errors='ignore')

    data = df1.to_csv(index=False)
    filename1 = f"{lat}_{lon}_{year}_{which}.csv"

    # file download response
    headers1 = {'Content-Disposition': f'attachment; filename="{filename1}"'}
    return Response(data, media_type='text/csv', headers=headers1)



###################
# FUNCTIONS called from other APIs

def fetch2yrsTempData(y1:int,y2:int,lat:float,lon:float):

    s1 = f"""select year1, month1, data from imd_temp_data
    where year1 in ({y1},{y2})
    and ST_Y(geometry)={lat}
    and ST_X(geometry)={lon}
    order by year1, month1
    """
    df1 = dbconnect.makeQuery(s1, output='df')

    tableY1 = []
    tableY2 = []
    for N,r in df1.iterrows():
        if r['year1'] == y1:
            for date1 in r['data'].keys():
                row = r['data'][date1]
                dt = date1.split('-')[-1]
                mo = date1.split('-')[1]
                trow = {'MD': f"{mo}-{dt}", 'y1_tmax':row.get('tmax',''),
                    'y1_tmin':row.get('tmin','') }
                tableY1.append(trow)
        elif r['year1'] == y2:
             for date1 in r['data'].keys():
                row = r['data'][date1]
                dt = date1.split('-')[-1]
                mo = date1.split('-')[1]
                trow = {'MD': f"{mo}-{dt}", 'y2_tmax':row.get('tmax',''),
                    'y2_tmin':row.get('tmin','') }
                tableY2.append(trow)
    y1_df = pd.DataFrame(tableY1)
    y2_df = pd.DataFrame(tableY2)
    comdf1 = pd.merge(y1_df, y2_df, on='MD', how='inner')
    cf.logmessage(f"fetch2yrsTempData: comdf1: {len(comdf1)} rows")
    # previews
    # print(y1_df.head(5))
    # print(y2_df.head(5))
    # print(comdf1.head(5))

    return comdf1


def viz2yrsTempData(comdf1, y1, y2, lat, lon):
    fig = plt.figure(figsize=(20, 10))
    ax = fig.add_subplot(1, 1, 1)

    # Set axis ranges; by default this will put major ticks every 25.
    # ax.set_xlim(0, 200)
    ax.set_ylim(0, 50)

    # Change major ticks to show every 20.
    ax.xaxis.set_major_locator(MultipleLocator(20))
    ax.yaxis.set_major_locator(MultipleLocator(5))

    # grid
    ax.grid(which='major', color='#CCCCCC', linestyle='--')

    # random.shuffle: randomizing elements in a list, from https://www.tutorialspoint.com/How-to-randomize-the-items-of-a-list-in-Python
    colors = ['blue','orange','red','green']
    random.shuffle(colors)
    assignment = { 'y1_tmax': colors[0] , 'y2_tmax': colors[1], 'y1_tmin': colors[2], 'y2_tmin': colors[3] }
    
    plt.plot(comdf1['MD'],comdf1['y1_tmax'], label='Y1 max', color=colors[0])
    plt.plot(comdf1['MD'],comdf1['y2_tmax'], label='Y2 max', color=colors[1])

    plt.plot(comdf1['MD'],comdf1['y1_tmin'], label='Y1 min', color=colors[2])
    plt.plot(comdf1['MD'],comdf1['y2_tmin'], label='Y2 min', color=colors[3])

    plt.xlabel("Month-Date (MM-DD)")
    plt.ylabel("°C")
    plt.title(f"Min and max temps for {y1} and {y2}, for location {lat},{lon} from IMD Pune gridded weather dataset")

    # save to file
    filename = f"{cf.makeUID()}.png"
    # filename = f"temp2yrs_{y1}-{y2}_{lat}-{lon}.png"
    fig.savefig(os.path.join(vizFolder,filename), bbox_inches='tight')

    return filename, assignment