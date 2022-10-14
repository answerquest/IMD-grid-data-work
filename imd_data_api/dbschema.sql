-- Postgres DB schema

-- Orig data tables

DROP TABLE IF EXISTS imd_data;
CREATE TABLE imd_data(
    sr SERIAL PRIMARY KEY,
    year1 INT NULL,
    month1 INT NULL,
    data JSONB DEFAULT '{}' NOT NULL,
    geometry GEOMETRY(POINT,4326) NOT NULL
);
CREATE INDEX imd_data_i1 ON imd_data (year1);
CREATE INDEX imd_data_i2 ON imd_data (month1);
CREATE INDEX imd_data_i3 ON imd_data (year1, month1);
CREATE INDEX imd_data_geom1 ON imd_data USING GIST (geometry);


DROP TABLE IF EXISTS grid;
CREATE TABLE grid(
    sr SERIAL PRIMARY KEY,
    geometry GEOMETRY(POINT,4326) NOT NULL
);
CREATE INDEX grid_geom1 ON grid USING GIST (geometry);



DROP TABLE IF EXISTS imd_temp_data;
CREATE TABLE imd_temp_data(
    sr SERIAL PRIMARY KEY,
    year1 INT NULL,
    month1 INT NULL,
    data JSONB DEFAULT '{}' NOT NULL,
    geometry GEOMETRY(POINT,4326) NOT NULL
);
CREATE INDEX imd_temp_data_i1 ON imd_temp_data (year1);
CREATE INDEX imd_temp_data_i2 ON imd_temp_data (month1);
CREATE INDEX imd_temp_data_i3 ON imd_temp_data (year1, month1);
CREATE INDEX imd_temp_data_geom1 ON imd_temp_data USING GIST (geometry);


DROP TABLE IF EXISTS temp_grid;
CREATE TABLE temp_grid(
    sr SERIAL PRIMARY KEY,
    geometry GEOMETRY(POINT,4326) NOT NULL
);
CREATE INDEX temp_grid_geom1 ON temp_grid USING GIST (geometry);


---------------------------------------

-- Game and api related tables

DROP TABLE IF EXISTS users;
CREATE TABLE users (
    userid SERIAL PRIMARY KEY,
    email VARCHAR(50) NOT NULL,
    name VARCHAR(50) NOT NULL,
    verified BOOLEAN DEFAULT FALSE NOT NULL,
    created TIMESTAMP(0) DEFAULT CURRENT_TIMESTAMP NOT NULL,
    verified_on TIMESTAMP(0) NULL
);


DROP TABLE IF EXISTS games;
CREATE TABLE games (
    gameid SERIAL PRIMARY KEY,
    userid INT NOT NULL,
    y1 INT NOT NULL,
    y2 INT NOT NULL,
    location GEOMETRY(POINT,4326) NOT NULL,
    assignment JSONB DEFAULT '{}' NOT NULL,
    filename VARCHAR(50) NULL,
    answer JSONB DEFAULT '{}' NOT NULL,
    reasoning JSONB DEFAULT '{}' NOT NULL,
    score INT NULL,
    afterthoughts JSONB DEFAULT '{}' NOT NULL,
    created TIMESTAMP(0) DEFAULT CURRENT_TIMESTAMP NOT NULL,
    answered TIMESTAMP(0) NULL,
    post_ans TIMESTAMP(0) NULL
);


DROP TABLE IF EXISTS misc;
CREATE TABLE misc (
    topic VARCHAR(50) NOT NULL PRIMARY KEY,
    data JSONB DEFAULT '{}' NOT NULL,
    updated TIMESTAMP(0) DEFAULT CURRENT_TIMESTAMP NOT NULL
);


DROP TABLE IF EXISTS sessions;
CREATE TABLE sessions (
    sid SERIAL PRIMARY KEY,
    userid INT NOT NULL,
    otp SMALLINT NOT NULL,
    token VARCHAR(100) NULL,
    ipadrr VARCHAR(200) NULL,
    created TIMESTAMP(0) DEFAULT CURRENT_TIMESTAMP NOT NULL,
    verified_at TIMESTAMP(0) NULL
);
CREATE INDEX sessions_i1 ON sessions (userid, otp);

