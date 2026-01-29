# Configuration Reference

## Required Settings

| Parameter | Type |         Description                      | Example                           |
| ---       |  --- |            ---                           |     ---                           |
| `api_url` |string| Base API URL without `/all-flights`.     | `https://api.com`                 |
| `api_key` |string|Header `Key` value required by the API.   | `HieGcY2nFreIsNLuo5EbXCwE7g0aRzTN`|
| `airports`|array |IATA codes to query. JSON array preferred.| `["AEP","EZE"]`                   |

## Optional Settings

| Parameter  | Type   |           Description             | Example                                |
|     ---    |  ---   |               ---                 |    ---                                 |
|`days_back` | integer| Days back from today (UTC, inclusive). `0` = only today. | `1`.            |
| `origin`   | string | `Origin` header sent to the API.  | `https://www.aeropuertosargentina.com` |
|`user_agent`| string | `User-Agent` header.              | `Mozilla/5.0`                          |
| `language` | string | `Accept-Language` header.         | `es-AR`                                |

## Configuration Examples

### Daily Incremental Sync
```json
{
  "api_url": "https://webaa-api-h4d5amdfcze7hthn.a02.azurefd.net/web-prod/v1/api-aa",
  "api_key": "HieGcY2nFreIsNLuo5EbXCwE7g0aRzTN",
  "airports": ["AEP", "EZE"],
  "days_back": 1
}
```

### Historical Backfill
```json
{
  "api_url": "https://webaa-api-h4d5amdfcze7hthn.a02.azurefd.net/web-prod/v1/api-aa",
  "api_key": "HieGcY2nFreIsNLuo5EbXCwE7g0aRzTN",
  "airports": ["AEP"],
  "days_back": 14,
  "language": "es-AR"
}
```

### Multi-airport Production Setup
```json
{
  "api_url": "https://webaa-api-h4d5amdfcze7hthn.a02.azurefd.net/web-prod/v1/api-aa",
  "api_key": "HieGcY2nFreIsNLuo5EbXCwE7g0aRzTN",
  "airports": ["AEP", "EZE", "COR", "MVD"],
  "days_back": 1,
  "origin": "https://www.aeropuertosargentina.com",
  "user_agent": "tap-airlines-arg/1.0"
}
```

## Environment Variables

| Config key  |      Env var            |
|     ---     |       ---               |
| `api_url`   |`TAP_AIRLINES_API_URL`   |
| `api_key`   |`TAP_AIRLINES_API_KEY`   |
| `airports`  |`TAP_AIRLINES_AIRPORTS`  |
| `days_back` |`TAP_AIRLINES_DAYS_BACK` |
| `origin`    |`TAP_AIRLINES_ORIGIN`.   |
| `user_agent`|`TAP_AIRLINES_USER_AGENT`|
| `language`  |`TAP_AIRLINES_LANGUAGE`  |

## Meltano-specific Configuration

- Set defaults in `meltano.yml`, then override per environment with `meltano config set tap-airlines-arg <key> <value>` or env vars.
- Use Meltano environments to keep secrets out of `meltano.yml`; CI/CD should inject `TAP_AIRLINES_API_KEY`.
- Catalog discovery: `uv run meltano --environment dev invoke tap-airlines-arg --discover`.

## Security Best Practices
- Never commit API keys or `.env` files.
- Prefer Meltano environments or a secrets manager to store `api_key`.
- Rotate keys regularly and revoke unused keys promptly. 
