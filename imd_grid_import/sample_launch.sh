#!/bin/bash


export DB_SERVER='localhost'
export DB_PORT='5438'
export DB_DBNAME='imdgrid'
export DB_USER='username'
export DB_PW='password'

export BATCH_SIZE='100000'

export TEMP_START='1951'
export TEMP_END='2020'
export TEMP_DISABLE='N'

export RAIN_START='1901'
export RAIN_END='2021'


python3 imd_import.py


# dockerized postgresql : change the username, password, persistent volume paths as per your setup
d="
docker run --name imdgrid -d -p "5438:5432" \
-e POSTGRES_USER=username \
-e POSTGRES_PASS=password \
-e POSTGRES_DBNAME=postgres,imdgrid \
-v "/fullpath/data":/var/lib/postgresql \
-v "/fullpath/pg_wal":/opt/postgres/pg_wal \
-e DEFAULT_ENCODING="UTF8" \
-e DEFAULT_COLLATION="en_US.UTF-8" \
-e DEFAULT_CTYPE="en_US.UTF-8" \
-e PASSWORD_AUTHENTICATION="md5" \
-e POSTGRES_INITDB_WALDIR=/opt/postgres/pg_wal \
-e POSTGRES_MULTIPLE_EXTENSIONS=postgis \
-e ALLOW_IP_RANGE='0.0.0.0/0' \
kartoza/postgis:14-3.2
"

