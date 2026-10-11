import json
import os
import pprint
import subprocess
import sys
import time
from decimal import Decimal
from pathlib import Path
from statistics import median

import clickhouse_connect
import psycopg

from queries import QUERIES

ROOT = Path(__file__).resolve().parent.parent
HOST = os.environ.get("DB_HOST", "localhost")


def ambil_angka(x, angka):
    if isinstance(x, bool):
        return
    if isinstance(x, (int, float, Decimal)):
        angka.append(float(x))
    elif isinstance(x, dict):
        for v in x.values():
            ambil_angka(v, angka)
    elif isinstance(x, (list, tuple)):
        for v in x:
            ambil_angka(v, angka)


def main():
    target = sys.argv[1] if len(sys.argv) > 1 else None
    keys = [target] if target else ["pg", "ch"]

    for key in keys:
        print(f"\n=== {key} ===", flush=True)
        if key == "pg":
            service = "postgres"
        elif key == "ch":
            service = "clickhouse"
        if target is None:
            subprocess.run(["docker", "compose", "up", "-d", service], check=True, cwd=ROOT)

        for attempt in range(40):
            try:
                if key == "pg":
                    print(f"connect postgres host={HOST} user=bench password=bench", flush=True)
                    conn = psycopg.connect(host=HOST, port=55432, user="bench", password="bench", dbname="transit", autocommit=True)
                elif key == "ch":
                    client = clickhouse_connect.get_client(host=HOST, port=58123, username="bench", password="bench",
                                                           database="transit", send_receive_timeout=900)
                break
            except Exception:
                time.sleep(3)

        out = {"db": key, "reads": {}}

        if key == "pg":
            cur = conn.cursor()
            cur.execute("DROP TABLE IF EXISTS trips, cards, stations")
            cur.execute((ROOT / "sql" / "postgres.sql").read_text(encoding="utf-8"))
            cur.execute("COPY stations FROM '/data/stations.csv' CSV HEADER")
            cur.execute("COPY cards FROM '/data/cards.csv' CSV HEADER")
            t0 = time.perf_counter()
            cur.execute("COPY trips FROM '/data/trips.csv' CSV HEADER")
            cur.execute("CREATE INDEX ON trips (tap_in)")
            cur.execute("CREATE INDEX ON trips (card_id, tap_in)")
            cur.execute("ANALYZE")
            load_s = time.perf_counter() - t0
            cur.execute("SELECT pg_table_size('trips'), pg_indexes_size('trips')")
            heap, index = cur.fetchone()
            out["load"] = {"load_s": load_s, "heap_bytes": heap, "index_bytes": index, "size_bytes": heap + index}
        elif key == "ch":
            for t in ["trips", "trips_raw", "cards", "stations"]:
                client.command(f"DROP TABLE IF EXISTS {t}")
            for stmt in (ROOT / "sql" / "clickhouse.sql").read_text(encoding="utf-8").split(";\n"):
                if stmt.strip():
                    client.command(stmt)
            for tabel, nama_file in [("stations", "stations.csv"), ("cards", "cards.csv")]:
                with open(ROOT / "data" / nama_file, "rb") as f:
                    client.raw_insert(tabel, insert_block=f.read(), fmt="CSVWithNames")
            t0 = time.perf_counter()
            with open(ROOT / "data" / "trips.csv", "rb") as f:
                client.raw_insert("trips_raw", insert_block=f.read(), fmt="CSVWithNames")
            client.command("""
                INSERT INTO trips
                SELECT t.trip_id, t.card_id, c.card_type, t.origin_id, so.name, so.line_id, t.dest_id, t.tap_in, t.tap_out, t.fare
                FROM trips_raw t JOIN cards c ON c.card_id = t.card_id JOIN stations so ON so.station_id = t.origin_id
                ORDER BY t.origin_id, t.tap_in""", settings={"max_execution_time": 600})
            client.command("OPTIMIZE TABLE trips FINAL")
            load_s = time.perf_counter() - t0
            client.command("DROP TABLE trips_raw")
            size = client.query("SELECT sum(bytes_on_disk) FROM system.parts WHERE database = 'transit' AND table = 'trips' AND active").result_rows[0][0]
            out["load"] = {"load_s": load_s, "size_bytes": int(size)}
        print("load:", out["load"], flush=True)

        for q in QUERIES:
            waktu_ukur, hasil = [], None
            for _ in range(6):
                t0 = time.perf_counter()
                if key == "pg":
                    cur = conn.cursor()
                    cur.execute(q["pg"])
                    hasil = cur.fetchall()
                elif key == "ch":
                    hasil = client.query(q["ch"]).result_rows
                # print(hasil[:2])
                waktu_ukur.append(time.perf_counter() - t0)

            if q.get("lookup"):
                fp = {"rows": len(hasil)}
            else:
                angka = []
                ambil_angka(hasil, angka)
                total = 0
                for a in angka:
                    total += a
                fp = {"rows": len(hasil), "sum": total}

            out["reads"][q["id"]] = {"median_s": median(waktu_ukur[1:]), "first_s": waktu_ukur[0], **fp}
            print(q["id"], f"median={out['reads'][q['id']]['median_s']:.4f}s rows={len(hasil)}", flush=True)

        waktu_update = []
        for trip_id in [100000, 900000, 1700000, 2500000, 3300000]:
            t0 = time.perf_counter()
            if key == "pg":
                conn.execute(f"UPDATE trips SET fare = 4000 WHERE trip_id = {trip_id}")
            elif key == "ch":
                client.command(f"ALTER TABLE trips UPDATE fare = 4000 WHERE trip_id = {trip_id}", settings={"mutations_sync": 1})
            waktu_update.append(time.perf_counter() - t0)
        out["update_median_s"] = median(waktu_update)
        print("update 1 baris median:", round(out["update_median_s"], 4), "s", flush=True)

        try:
            if key == "pg":
                conn.close()
            elif key == "ch":
                client.close()
        except Exception:
            pass

        (ROOT / "results").mkdir(exist_ok=True)
        (ROOT / "results" / f"{key}.json").write_text(json.dumps(out, indent=2))
        if target is None:
            try:
                subprocess.run(["docker", "compose", "stop", service], check=True, cwd=ROOT)
            except Exception:
                pass

    hasilDbms = []
    for k in ["pg", "ch"]:
        p = ROOT / "results" / f"{k}.json"
        if p.exists():
            hasilDbms.append(json.loads(p.read_text()))
    print("\n=== cek hasil sama antar DBMS ===")
    for q in QUERIES:
        fps = set()
        for r in hasilDbms:
            fps.add((r["reads"][q["id"]]["rows"], r["reads"][q["id"]].get("sum")))
        print(q["id"], "sama" if len(fps) == 1 else f"BEDA: {fps}")


if __name__ == "__main__":
    main()
