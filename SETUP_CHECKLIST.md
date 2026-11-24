# What you actually need to provide

Three real credentials, all free-tier. Exact steps below.

## 1. Gemini API Key (~1 minute)

1. Go to [aistudio.google.com/apikey](https://aistudio.google.com/apikey).
2. Click **Create API key**.
3. Copy it into `.env` as `GEMINI_API_KEY`.

## 2. Serper.dev API Key (~1 minute)

This is the real discovery engine for 7 of the 8 platforms (a real,
ToS-compliant reseller of Google search results — see
`app/platforms/search_provider.py` for why Google's own Custom Search API
couldn't be used: it's closed to new customers as of this project's
development).

1. Go to [serper.dev](https://serper.dev) and sign up (Google sign-in works, no credit card).
2. Your API key is shown immediately on the dashboard.
3. Copy it into `.env` as `SERPER_API_KEY`.

Free tier: 2,500 queries total.

## 3. YouTube Data API Key (~2 minutes)

1. Go to the [Google Cloud Console](https://console.cloud.google.com/apis/library/youtube.googleapis.com) and enable the **YouTube Data API v3** for a project (create one if you don't have one).
2. Go to **APIs & Services → Credentials → + Create Credentials → API key** (use this direct path — not the "Create Credentials" guided wizard, which defaults to OAuth/service-account flows you don't need here).
3. Copy it into `.env` as `YOUTUBE_API_KEY`.

Free tier: 10,000 quota units/day (a search call costs 100 units, so ~100 searches/day).

---

After filling in `.env`, run:

```bash
uvicorn app.main:app --host 0.0.0.0 --port 4000
```

Then test with the spec's own example:

```bash
curl -X POST http://localhost:4000/prospect-discovery \
  -H "Content-Type: application/json" \
  -d '{"query": "Football lovers in Washington DC in USA"}'
```
