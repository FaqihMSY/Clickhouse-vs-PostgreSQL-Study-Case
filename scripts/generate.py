import os
import random
import sys
from datetime import date, timedelta


def main():
    rows = 5000000
    if len(sys.argv) > 1:
        rows = int(sys.argv[1])
    rng = random.Random(42)
    os.makedirs("data", exist_ok=True)

    with open("data/stations.csv", "w") as f:
        f.write("station_id,name,line_id\n")
        for i in range(1, 121):
            koridor = (i - 1) // 15 + 1
            f.write(f"{i},Stasiun {i},{koridor}\n")

    jenis_kartu = [None]
    with open("data/cards.csv", "w") as f:
        f.write("card_id,card_type\n")
        for i in range(1, 200001):
            r = rng.random()
            if r < 0.70:
                jenis_kartu.append("regular")
            elif r < 0.92:
                jenis_kartu.append("student")
            else:
                jenis_kartu.append("senior")
            f.write(f"{i},{jenis_kartu[i]}\n")

    days = []
    for d in range(182):
        days.append((date(2025, 1, 1) + timedelta(days=d)).isoformat())

    bobot_hari = []
    for d in range(181):
        if (date(2025, 1, 1) + timedelta(days=d)).weekday() >= 5:
            bobot_hari.append(0.55)
        else:
            bobot_hari.append(1.0)
    total_bobot = sum(bobot_hari)
    bobot_jam = [1, 1, 1, 1, 2, 5, 12, 25, 28, 15, 8, 8, 10, 8, 8, 10, 15, 26, 28, 16, 8, 5, 3, 2]

    trip_id = 0
    with open("data/trips.csv", "w") as f:
        f.write("trip_id,card_id,origin_id,dest_id,tap_in,tap_out,fare\n")
        for d in range(181):
            if d == 180:
                n = rows - trip_id
            else:
                n = round(rows * bobot_hari[d] / total_bobot)

            detik = []
            for jam in rng.choices(range(24), bobot_jam, k=n):
                detik.append(jam * 3600 + rng.randrange(3600))
            detik.sort()
            # print(d, n)

            baris = []
            for s in detik:
                trip_id += 1
                card = rng.randint(1, 200000)
                asal = rng.randint(1, 120)
                tujuan = (asal + rng.randint(0, 118)) % 120 + 1
                durasi = (5 + rng.randrange(40)) * 60

                hari_masuk, detik_masuk = divmod(s, 86400)
                tap_in = f"{days[d + hari_masuk]} {detik_masuk // 3600:02d}:{detik_masuk % 3600 // 60:02d}:{detik_masuk % 60:02d}"
                hari_keluar, detik_keluar = divmod(s + durasi, 86400)
                tap_out = f"{days[d + hari_keluar]} {detik_keluar // 3600:02d}:{detik_keluar % 3600 // 60:02d}:{detik_keluar % 60:02d}"

                if jenis_kartu[card] == "regular":
                    fare = 3500
                elif jenis_kartu[card] == "student":
                    fare = 2000
                else:
                    fare = 1500
                baris.append(f"{trip_id},{card},{asal},{tujuan},{tap_in},{tap_out},{fare}")
            f.write("\n".join(baris) + "\n")

    print(f"stations=120 cards=200000 trips={trip_id}")


main()
