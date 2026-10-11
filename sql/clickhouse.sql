CREATE TABLE stations (station_id UInt16, name String, line_id UInt8) ENGINE = MergeTree ORDER BY station_id;

CREATE TABLE cards (card_id UInt32, card_type LowCardinality(String)) ENGINE = MergeTree ORDER BY card_id;

CREATE TABLE trips_raw (
  trip_id UInt64, card_id UInt32, origin_id UInt16, dest_id UInt16,
  tap_in DateTime, tap_out DateTime, fare UInt32
) ENGINE = MergeTree ORDER BY trip_id;

CREATE TABLE trips (
  trip_id     UInt64,
  card_id     UInt32,
  card_type   LowCardinality(String),
  origin_id   UInt16,
  origin_name LowCardinality(String),
  line_id     UInt8,
  dest_id     UInt16,
  tap_in      DateTime,
  tap_out     DateTime,
  fare        UInt32
) ENGINE = MergeTree
PARTITION BY toYYYYMM(tap_in)
ORDER BY (origin_id, tap_in);
