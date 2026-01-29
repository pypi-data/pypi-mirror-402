# Quickstart Guide

## Prerequisites
- Python 3.10+
- [uv](https://docs.astral.sh/uv/) installed

## Steps

1) Install dependencies
```bash
uv sync
```

2) Configure (defaults work, but you can override)
```bash
cat > config.local.json <<'EOF'
{
  "api_url": "https://webaa-api-h4d5amdfcze7hthn.a02.azurefd.net/web-prod/v1/api-aa",
  "api_key": "HieGcY2nFreIsNLuo5EbXCwE7g0aRzTN",
  "airports": ["AEP", "EZE"],
  "days_back": 1
}
EOF
```

3) Test connectivity and schema
```bash
uv run tap-airlines-arg --config config.local.json --test=schema
```

4) Run and write output
```bash
uv run tap-airlines-arg --config config.local.json --test=records > output/aerolineas_all_flights.jsonl
```

5) Verify output
```bash
head output/aerolineas_all_flights.jsonl
```

## Next Steps
- Full options and troubleshooting: `README.md`
- Configuration tables and env mapping: `CONFIGURATION.md`
- Development guide: `AGENTS.md`
