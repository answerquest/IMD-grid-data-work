# emailFunctions.py
# as per https://docs.python.org/3/library/email.examples.html
import smtplib
from email.message import EmailMessage
from email.headerregistry import Address
from email.utils import make_msgid
import pandas as pd
import json, os

from typing import Optional, List
from pydantic import BaseModel
from fastapi.responses import FileResponse
from fastapi import HTTPException, Header, File, UploadFile, Form

import commonfuncs as cf
from imdapi_launch import app
# from api_users import authenticate, findRole


def makeAddress(emails):
    # have to split "name@domain.com" into Address("name","name","domain.com"), and if multiple then have to string them together into tuple 
    if type(emails) == str:
        holder = emails.strip().split('@')
        if len(holder) != 2:
            cf.logmessage("makeAddress: Invalid email id:",emails)
            return os.environ.get('EMAIL_SENDER','')
        return Address(holder[0],holder[0],holder[1])
    elif type(emails) == list:
        collector = []
        for oneEmail in emails:
            holder = oneEmail.strip().split('@')
            if len(holder) != 2:
                cf.logmessage("makeAddress: Invalid email id:",oneEmail)
                continue
            collector.append(Address(holder[0],holder[0],holder[1]))
        # after for loop:
        if len(collector): return tuple(collector)
    # default
    return os.environ.get('EMAIL_SENDER','')


def sendEmail(content, subject, recipients, cc=None, html=None):
    '''
    Emailing function. 
    '''
    # from https://docs.python.org/3/library/email.examples.html
    msg = EmailMessage()
    msg['Subject'] = subject
    msg['From'] = makeAddress(os.environ.get('EMAIL_SENDER',''))
    msg['To'] = makeAddress(recipients)
    if cc: msg['Cc'] = makeAddress(cc)
    msg.set_content(content)
    
    # adding html formatted body: from https://stackoverflow.com/a/58322776/4355695
    if html:
        msg.add_alternative(f"<!DOCTYPE html><html><body>{html}</body></html>", subtype = 'html')

    cf.logmessage('to:',msg['To'])
    # cf.logmessage('cc:',msg['Cc'])
    # cf.logmessage('subject:',msg['Subject'])
    # cf.logmessage(content)
    
    # login to server and send the actual email
    # try:    
    server = smtplib.SMTP_SSL(os.environ.get('EMAIL_SERVER',''), os.environ.get('EMAIL_PORT',''))  # We are specifying TLS here
    server.ehlo()
    server.login(os.environ.get('EMAIL_SENDER',''),os.environ.get('EMAIL_PW',''))
    status = server.send_message(msg)
    server.close()
    return status
    # except:
    #     return {'exception':True}
    


# class emailTestReq(BaseModel):
#     recipients: List[str]
#     subject: str
#     content: str
#     cc: Optional[str] = None

# @app.post("/API/emailTest", tags=["email"])
# def emailTest(req: emailTestReq, x_access_key: Optional[str] = Header(None)):
#     cf.logmessage("emailTest api call")
#     username, role = authenticate(x_access_key, allowed_roles=['admin'])
    
#     status = sendEmail(req.content, req.subject, req.recipients, req.cc)
#     cf.logmessage(f"Email status: {status}")
#     return {'message':'success', 'status':status}