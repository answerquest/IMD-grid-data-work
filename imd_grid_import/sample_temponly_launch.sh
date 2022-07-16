#!/bin/bash

export DB_SERVER='localhost'
export DB_PORT='5438'
export DB_DBNAME='imdgrid'
export DB_USER='username'
export DB_PW='password'

export BATCH_SIZE='100000'

export TEMP_START='1951'
export TEMP_END='2020'


python3 imd_temperature_import.py



