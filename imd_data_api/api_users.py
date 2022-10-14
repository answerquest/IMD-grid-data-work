# api_users.py

from typing import Optional, List
from pydantic import BaseModel
from fastapi.responses import FileResponse
from fastapi import HTTPException, Header
import secrets, random

from imdapi_launch import app
import commonfuncs as cf
import dbconnect
from api_email import sendEmail


class emailOTP_payload(BaseModel):
    email: str
    
@app.post("/API/emailOTP", tags=["users"])
def emailOTP(r: emailOTP_payload, X_Forwarded_For: Optional[str] = Header(None)):
    
    email = r.email
    # to do: validation

    # check if its a new user or existing one
    s1 = f"""select userid from users where email = '{email}'"""
    userid = dbconnect.makeQuery(s1, output='oneValue')

    if not userid:
        i1 = f"""insert into users (email) values ('{email}') """
        i1Count = dbconnect.execSQL(i1)
        # get the userid, from https://dba.stackexchange.com/a/3284/188594
        s2 = f"""select currval(pg_get_serial_sequence('users', 'userid'))"""
        userid = dbconnect.makeQuery(s2, output='oneValue')


    otp = random.randint(1000,9999)
    
    i2 = f"""insert into sessions (userid, otp) values ({userid},{otp})"""
    i2Count = dbconnect.execSQL(i2)

    content = f"""<h2>OTP: {otp}</h2>
    <p>For IMD data game login</p>
    
    <br><br>
    <p><small>This is an auto-generated message</small></p>"""

    textContent = f"OTP: {otp} for IMD data site login"
    subject = f"OTP: {otp} for IMD data site login"
    status = sendEmail(content=textContent, subject=subject, recipients=email, cc=None, html=content)
    
    returnD = {'email_sent' : True, 'userid':userid }
    return returnD



class verifyOTP_payload(BaseModel):
    userid: int
    otp: int
    
@app.post("/API/verifyOTP", tags=["users"])
def verifyOTP(r: verifyOTP_payload, X_Forwarded_For: Optional[str] = Header(None)):
    userid = r.userid 
    otp = r.otp

    s1 = f"""select count(*) from sessions where userid={userid} and otp={otp}"""
    c1 = dbconnect.makeQuery(s1, output="oneValue")

    if not c1:
        raise HTTPException(status_code=401, detail="Unauthorized")
        return

    if not X_Forwarded_For: X_Forwarded_For = 'local'
    token = secrets.token_urlsafe(50)

    u1 = f"""update sessions
    set token = '{token}', ipadrr = '{X_Forwarded_For}', verified_at = CURRENT_TIMESTAMP
    where userid = {userid} and otp = {otp}
    """
    u1Count = dbconnect.execSQL(u1)

    s2 = f"select email, userid from users where userid = {userid}"
    row = dbconnect.makeQuery(s2, output='oneJson')

    returnD = {'logged_in':True, 'token': token, 'profile':row }
    return returnD



@app.get("/API/authenticate", tags=["users"])
def authenticate(x_access_token: str = Header(...)):
    cf.logmessage("authenticate get api call")
    s1 = f"""select t1.email, t1.userid
    from users as t1
    left join sessions as t2
    on t1.userid = t2.userid
    where t2.token = '{x_access_token}'
    """
    row = dbconnect.makeQuery(s1, output='oneJson')

    if row:
        returnD = {'logged_in':True, 'profile':row }
        return returnD
    else:
        raise HTTPException(status_code=401, detail="Unauthorized")
    
