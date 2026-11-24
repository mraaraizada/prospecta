# What you actually need to provide

Three real credentials, all free-tier. Exact steps below.

## 1. Gemini API Key (~1 minute)

1. Go to [aistudio.google.com/apikey](https://aistudio.google.com/apikey).
2. Click **Create API key**.
3. Copy it into `.env` as `GEMINI_API_KEY`.

## 2. Brave Search API Key (~2 minutes)

This is the real discovery engine for 7 of the 8 platforms.

**Note:** Google's own Custom Search JSON API is confirmed **closed to new customers** (no workaround — billing doesn't unlock it), which is why this project uses Brave Search instead.

1. Go to [brave.com/search/api](https://brave.com/search/api/) and sign up for a free account.
2. Create a subscription on the **Free** plan (2,000 queries/month).
3. Go to your dashboard's API Keys section and copy your key.
4. Copy it into `.env` as `BRAVE_API_KEY`.

## 3. YouTube Data API Key (~2 minutes)

1. In the same Google Cloud project, enable the [YouTube Data API v3](https://console.cloud.google.com/apis/library/youtube.googleapis.com).
2. You can reuse the same API key from step 2 if it has both APIs enabled, or create a separate one.
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
