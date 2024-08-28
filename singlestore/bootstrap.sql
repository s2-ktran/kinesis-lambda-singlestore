CREATE DATABASE IF NOT EXISTS vehicle_db PARTITIONS 4;
USE vehicle_db;

CREATE TABLE vehicle_data (
    vehicle_id VARCHAR(50),
    ts datetime(6),
    lambda_ts datetime(6),
    kinesis_ts datetime(6),
    location_lat FLOAT,
    location_long FLOAT,
    speed FLOAT,
    battery_level FLOAT,
    maintenance_status VARCHAR(100),
    passenger_count FLOAT,
    s2_ts datetime(6) DEFAULT CURRENT_TIMESTAMP(6)
);

DROP TABLE vehicle_data;

SELECT COUNT(*) FROM vehicle_data;

SELECT 
    kinesis_ts,
    lambda_ts, 
    s2_ts,
    TIMESTAMPDIFF(MICROSECOND, kinesis_ts, s2_ts) / 1000 AS delta_ms,
    TIMESTAMPDIFF(MICROSECOND, lambda_ts, s2_ts) / 1000 AS lambda_ms
FROM vehicle_data
ORDER BY timestamp DESC;