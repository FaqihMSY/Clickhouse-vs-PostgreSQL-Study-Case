QUERIES = [
    {
        "id": "Q1", "title": "Perjalanan dan pendapatan per hari",
        "pg": "SELECT tap_in::date AS d, count(*) AS trips, sum(fare) AS revenue FROM trips GROUP BY 1 ORDER BY 1",
        "ch": "SELECT toDate(tap_in) AS d, count() AS trips, sum(fare) AS revenue FROM trips GROUP BY d ORDER BY d",
    },
    {
        "id": "Q2", "title": "10 stasiun asal tersibuk, Maret",
        "pg": """SELECT s.name, count(*) AS taps FROM trips t JOIN stations s ON s.station_id = t.origin_id
                 WHERE t.tap_in >= '2025-03-01' AND t.tap_in < '2025-04-01'
                 GROUP BY s.name ORDER BY taps DESC, s.name LIMIT 10""",
        "ch": """SELECT origin_name AS name, count() AS taps FROM trips
                 WHERE tap_in >= '2025-03-01' AND tap_in < '2025-04-01'
                 GROUP BY name ORDER BY taps DESC, name LIMIT 10""",
    },
    {
        "id": "Q3", "title": "Jumlah tap per jam per koridor",
        "pg": """SELECT s.line_id, EXTRACT(HOUR FROM t.tap_in)::int AS hr, count(*) AS taps
                 FROM trips t JOIN stations s ON s.station_id = t.origin_id GROUP BY 1, 2 ORDER BY 1, 2""",
        "ch": "SELECT line_id, toHour(tap_in) AS hr, count() AS taps FROM trips GROUP BY line_id, hr ORDER BY line_id, hr",
    },
    {
        "id": "Q4", "title": "Pendapatan per tipe kartu per bulan",
        "pg": """SELECT date_trunc('month', t.tap_in)::date AS month, c.card_type, sum(t.fare) AS revenue
                 FROM trips t JOIN cards c ON c.card_id = t.card_id GROUP BY 1, 2 ORDER BY 1, 2""",
        "ch": "SELECT toStartOfMonth(tap_in) AS month, card_type, sum(fare) AS revenue FROM trips GROUP BY month, card_type ORDER BY month, card_type",
    },
    {
        "id": "Q5", "title": "Kartu aktif unik per minggu",
        "pg": "SELECT date_trunc('week', tap_in)::date AS wk, count(DISTINCT card_id) AS active_cards FROM trips GROUP BY 1 ORDER BY 1",
        "ch": "SELECT toMonday(tap_in) AS wk, uniqExact(card_id) AS active_cards FROM trips GROUP BY wk ORDER BY wk",
    },
    {
        "id": "Q6", "title": "10 perjalanan terakhir satu kartu", "lookup": True,
        "pg": "SELECT trip_id, origin_id, dest_id, tap_in, fare FROM trips WHERE card_id = 12345 ORDER BY tap_in DESC LIMIT 10",
        "ch": "SELECT trip_id, origin_id, dest_id, tap_in, fare FROM trips WHERE card_id = 12345 ORDER BY tap_in DESC LIMIT 10",
    },
]
