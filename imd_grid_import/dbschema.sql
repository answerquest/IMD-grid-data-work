-- Postgres DB schema

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
