CREATE TABLE stations (
  station_id integer PRIMARY KEY,
  name       text NOT NULL,
  line_id    smallint NOT NULL
);

CREATE TABLE cards (
  card_id   integer PRIMARY KEY,
  card_type text NOT NULL
);

CREATE TABLE trips (
  trip_id   bigint PRIMARY KEY,
  card_id   integer NOT NULL REFERENCES cards(card_id),
  origin_id integer NOT NULL REFERENCES stations(station_id),
  dest_id   integer NOT NULL REFERENCES stations(station_id),
  tap_in    timestamp NOT NULL,
  tap_out   timestamp NOT NULL,
  fare      integer NOT NULL
);
