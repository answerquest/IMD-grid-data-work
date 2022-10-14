# api_games.py

from typing import Optional, List
from pydantic import BaseModel
from fastapi.responses import FileResponse
from fastapi import HTTPException, Header, File, UploadFile, Form
import os, json, random

from imdapi_launch import app
import commonfuncs as cf
import dbconnect
from api_data import fetch2yrsTempData, viz2yrsTempData

root = os.path.dirname(__file__)
vizFolder = os.path.join(root,'viz')

################

@app.get("/API/randomYears", tags=["game"])
def decideYears(minGap:int, maxGap: Optional[int]=70 ):
    g = random.randint(minGap, maxGap)
    x = random.randint(1950+g,2020)
    y1, y2 = x-g, x
    returnD = {'y1':y1, 'y2':y2}
    # print(returnD)
    return returnD


################

class gameStart_payload(BaseModel):
    y1: int
    y2: int
    lat: float
    lon: float
    
@app.post("/API/gameStart", tags=["game"])
def gameStart(r: gameStart_payload, x_access_token: str = Header(...)):
    cf.logmessage("gameStart api call")
    
    # get userid
    s1 = f"select userid from sessions where token='{x_access_token}'"
    userid = dbconnect.makeQuery(s1, output='oneValue')
    if not userid:
        raise HTTPException(status_code=401, detail="Unauthorized")
        return

    comdf1 = fetch2yrsTempData(r.y1,r.y2,r.lat,r.lon)

    # make viz
    filename, assignment = viz2yrsTempData(comdf1, r.y1, r.y2, r.lat, r.lon)

    # to do : encrypt assignment
    
    # 2022-09-11: not getting into enryption complexities for now. 
    # we'll hold the assignment in DB, let the user submit theirs and directly compare for scoring.

    i1 = f"""insert into games (userid, y1, y2, location, filename, assignment ) values 
    ({userid}, {r.y1}, {r.y2}, ST_POINT({r.lon},{r.lat}), '{filename}', '{json.dumps(assignment)}' )
    """
    i1Count = dbconnect.execSQL(i1)

    # get the gameid, from https://dba.stackexchange.com/a/3284/188594
    s2 = f"""select currval(pg_get_serial_sequence('games', 'gameid'))"""
    gameid = dbconnect.makeQuery(s2, output='oneValue')

    returnD = { 'processed': True, 'gameid':gameid, 'graph':filename}
    return returnD


################

class gameSubmit_payload(BaseModel):
    gameid: int
    y1_tmax: str
    y2_tmax: str
    y1_tmin: str
    y2_tmin: str
    reasoning: Optional[str] = ''

@app.post("/API/gameSubmit", tags=["game"])
def gameSubmit(r: gameSubmit_payload, x_access_token: str = Header(...)):
    cf.logmessage("gameSubmit api call")

    # to do: auth the token, verify if the game is correct
    # get userid
    s1 = f"select userid from sessions where token='{x_access_token}'"
    userid = dbconnect.makeQuery(s1, output='oneValue')
    if not userid:
        raise HTTPException(status_code=401, detail="Unauthorized")
        return

    s2 = f"select * from games where gameid = {r.gameid}"
    grow = dbconnect.makeQuery(s2, output='oneJson', fillna=False)
    
    # check if game already finished
    if grow.get('answered', False):
        raise HTTPException(status_code=400, detail="Game already completed")
        return

    answer = { 'y1_tmax': r.y1_tmax, 'y2_tmax': r.y2_tmax, 'y1_tmin': r.y1_tmin, 'y2_tmin': r.y2_tmin }
    cf.logmessage(f"answer: {answer}")

    reasoning = {'text': r.reasoning }
    assignment = grow.get('assignment')
    print('assignment:',type(assignment), assignment)

    minMaxSwitchCount = 0
    correctCount = 0

    if answer == assignment:
        cf.logmessage(f"All correct!")
        score = 100
    
    else:
        # calculcate score
        # +25 for every correct color
        # penalties : if you mistook a min line for a max or vice versa, then -25

        score = 0
        if answer['y1_tmax'] == assignment['y1_tmax']:
            score += 25
            correctCount += 1
        elif answer['y1_tmax'] in (assignment['y1_tmin'], assignment['y2_tmin'] ):
            score -= 20
            minMaxSwitchCount += 1

        if answer['y2_tmax'] == assignment['y2_tmax']:
            score += 25
            correctCount += 1
        elif answer['y2_tmax'] in (assignment['y1_tmin'], assignment['y2_tmin'] ):
            score -= 20
            minMaxSwitchCount += 1

        if answer['y1_tmin'] == assignment['y1_tmin']:
            score += 25
            correctCount += 1
        elif answer['y1_tmin'] in (assignment['y1_tmax'], assignment['y2_tmax'] ):
            score -= 20
            minMaxSwitchCount += 1
        
        if answer['y2_tmin'] == assignment['y2_tmin']:
            score += 25
            correctCount += 1
        elif answer['y2_tmin'] in (assignment['y1_tmax'], assignment['y2_tmax'] ):
            score -= 20
            minMaxSwitchCount += 1


    u1 = f"""update games
    set answer = '{json.dumps(answer)}', reasoning = '{json.dumps(reasoning)}', score={score},
    answered = CURRENT_TIMESTAMP
    where gameid = {r.gameid}
    """
    u1Count = dbconnect.execSQL(u1)

    returnD = {'evaluated': True, 'gameid': r.gameid, 'score': score, 
        'correctCount':correctCount,  'minMaxSwitchCount': minMaxSwitchCount,
        'correct_answer': assignment
    }
    return returnD



class afterthought_payload(BaseModel):
    gameid: int
    afterthought: str

@app.post("/API/afterthought", tags=["game"])
def afterthought(r: afterthought_payload, x_access_token: str = Header(...)):
    cf.logmessage("afterthought api call")

    # to do: auth the token, verify if the game is correct
    # get userid
    s1 = f"select userid from sessions where token='{x_access_token}'"
    userid = dbconnect.makeQuery(s1, output='oneValue')
    if not userid:
        raise HTTPException(status_code=401, detail="Unauthorized")
        return

    afterthoughts = { 'text': r.afterthought }
    u1 = f"""update games 
    set afterthoughts = '{json.dumps(afterthoughts)}', post_ans = CURRENT_TIMESTAMP
    where gameid = {r.gameid} and userid = {userid}
    """
    u1Count = dbconnect.execSQL(u1)

    returnD = {'afterthought_saved': True}

