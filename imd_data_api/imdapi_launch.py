from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware # https://fastapi.tiangolo.com/tutorial/cors/
from fastapi.staticfiles import StaticFiles # static html files deploying
from brotli_asgi import BrotliMiddleware # https://github.com/fullonic/brotli-asgi
import os

app = FastAPI()

# allow cors - from https://fastapi.tiangolo.com/tutorial/cors/
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# enable Brotli compression. Better for json payloads, supported by most browsers. Fallback to gzip by default. from https://github.com/fullonic/brotli-asgi
app.add_middleware(BrotliMiddleware)


import api_users
import api_email
import api_data
import api_games

###########
# STATIC files, uploads etc

# create static folders if not existing

app.mount("/viz", StaticFiles(directory="viz", html = False), name="viz")
app.mount("/", StaticFiles(directory="html", html = True), name="static")


