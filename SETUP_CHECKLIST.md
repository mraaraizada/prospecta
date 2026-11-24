# What you actually need to provide

Three real credentials, all free-tier. Exact steps below.

## 1. Gemini API Key (~1 minute)

1. Go to [aistudio.google.com/apikey](https://aistudio.google.com/apikey).
2. Click **Create API key**.
3. Copy it into `.env` as `GEMINI_API_KEY`.

## 2. Google Custom Search API Key + Search Engine ID (~5 minutes)

This is the real discovery engine for 7 of the 8 platforms.

**A. Create a Programmable Search Engine:**
1. Go to [programmablesearchengine.google.com](https://programmablesearchengine.google.com/).
2. Click **Add** → give it any name.
3. Under "What to search?", choose **Search the entire web**.
4. Create it, then go to its **Setup** page and copy the **Search engine ID** (this is `cx`) into `.env` as `GOOGLE_CSE_ID`.

**B. Get an API key and enable the Custom Search API:**
1. Go to the [Google Cloud Console](https://console.cloud.google.com/apis/library/customsearch.googleapis.com) and enable the **Custom Search API** for a project (create one if you don't have one).
2. Go to **APIs & Services → Credentials → Create Credentials → API key**.
3. Copy it into `.env` as `GOOGLE_CSE_API_KEY`.

Free tier: 100 queries/day.

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
