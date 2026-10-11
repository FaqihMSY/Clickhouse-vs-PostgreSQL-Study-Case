# ClickHouse vs PostgreSQL

```bash
docker compose --profile tools run --rm py scripts/generate.py
docker compose up -d postgres
docker compose --profile tools run --rm py scripts/run.py pg
docker compose stop postgres
```

```bash
pip install -r requirements.txt
python scripts/generate.py
python scripts/run.py        
```