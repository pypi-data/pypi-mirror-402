# API Reference - Airports Argentina `/all-flights`

## Endpoint
- Method: `GET`
- URL: `{api_url}/all-flights` (e.g., `https://webaa-api-h4d5amdfcze7hthn.a02.azurefd.net/web-prod/v1/api-aa/all-flights`)

## Authentication and Headers
- Header `Key: <api_key>` (required)
- Header `Origin` (defaults to `https://www.aeropuertosargentina.com`)
- Header `User-Agent` (defaults to `Mozilla/5.0`)
- Header `Accept-Language` (defaults to `es-AR`)

## Request Parameters

| Name     | Type | Required | Description         | Example    |
| ---      | ---  | ---      |  ---                | ---        |
| `c`      |string| yes      | expects `900`       | `900`      |
| `idarpt` |string| yes      | Airport IATA code.  | `AEP`      |    
| `movtp`  |string| yes      | Mov type`A` or `D`  | `A`        |
| `f`      |string| yes      | Date in `DD-MM-YYYY`|`20-01-2026`|

## Response
- Returns a JSON array; each element is a flight object.
- Key fields: `id`, `stda/etda/atda` (times), `arpt`, `destorig`, `mov`, `nro`, `status`, `sector/termsec/gate/belt`, weather snippets (`sdtemp`, `sdphrase`), aircraft info (`acftype`, `matricula`), plus tap metadata (`x_fetched_at`, `x_airport_iata`, `x_movtp`, `x_date`).
- Unknown fields are preserved (`additionalProperties: true`).

## Known Limitations
- Single-page endpoint (no pagination).
- Subject to rate limiting (`429`) — retries are handled by the tap, but keep `days_back` conservative.
- Data freshness is tied to the airport's operational feed; historical depth is limited (recent days only).

## Changelog
- No public versioned changelog from the provider. Monitor responses and update the schema when new fields appear. 
