import os, sys, json, requests
from datetime import datetime, timedelta, timezone
import cerebras.cloud.sdk as cb
from cerebras.cloud.sdk import Cerebras

MODEL_ID   = "llama-4-scout-17b-16e-instruct"   
GNEWS_URL  = "https://gnews.io/api/v4/search"
MAX_ARTS   = 5
BRIEF_WORDS = 800                               
MAX_TOKENS  = int(BRIEF_WORDS * 1.5)            

def date(dt: datetime) -> str:
    return dt.strftime("%Y-%m-%dT%H:%M:%SZ")

def fetch_articles(query: str, api_key: str):
    now, since = datetime.now(timezone.utc), datetime.now(timezone.utc) - timedelta(hours=24)
    params = {
        "q": query,
        "lang": "en",
        "from": date(since),
        "to": date(now),
        "sortby": "publishedAt",
        "max": MAX_ARTS,
        "apikey": api_key,
    }
    r = requests.get(GNEWS_URL, params=params, timeout=10)
    if r.status_code == 403:
        raise RuntimeError("GNews 403 – activate your key via the email link.")
    r.raise_for_status()
    return r.json().get("articles", [])

def main():
    ck, gk = os.getenv("CEREBRAS_API_KEY"), os.getenv("GNEWS_API_KEY")
    if not ck or not gk:
        print("Set CEREBRAS_API_KEY and GNEWS_API_KEY in your environment."); sys.exit(1)

    topic = input("Topic: ").strip()
    if not topic:
        print("No query supplied – exiting."); return

    start = datetime.now(timezone.utc)
    print(f"Fetching news on “{topic}”…", flush=True)
    try:
        raw_articles = fetch_articles(topic, gk)
    except Exception as e:
        print("News fetch failed:", e); return
    if not raw_articles:
        print("No recent articles found."); return

    schema = {
        "type": "object",
        "properties": {
            "title":            {"type": "string"},
            "url":              {"type": "string"},
            "publisher":        {"type": "string"},
            "publication_date": {"type": "string"},
            "summary":          {"type": "string"},
        },
        "required": ["title", "url", "publisher", "publication_date", "summary"],
        "additionalProperties": False,
    }

    client = Cerebras(api_key=ck)
    structured = []

    for art in raw_articles:
        prompt = (
            "Return JSON with keys title, url, publisher, publication_date, summary.\n\n"
            f"Article title: {art.get('title','')}\n"
            f"URL: {art.get('url','')}\n"
            f"Publisher: {art.get('source',{}).get('name','')}\n"
            f"Publication date: {art.get('publishedAt','')}\n"
            f"Text: {art.get('content') or art.get('description','')}"
        )
        try:
            resp = client.chat.completions.create(
                model=MODEL_ID,
                messages=[
                    {"role": "system", "content": "Extract structured data from news articles."},
                    {"role": "user", "content": prompt},
                ],
                response_format={
                    "type": "json_schema",
                    "json_schema": {
                        "name":   "article_schema",
                        "strict": True,
                        "schema": schema,
                    },
                },
            )
            structured.append(json.loads(resp.choices[0].message.content))
        except (cb.APIStatusError, json.JSONDecodeError) as e:
            print("Skip article –", e)

    if not structured:
        print("No article JSON extracted – aborting."); return

    summaries = "\n".join(
        f"{i}. {a['title']} — {a['publisher']} ({a['publication_date']}): {a['summary']}"
        for i, a in enumerate(structured, 1)
    )

    print(summaries)

    brief_prompt = (
        f"Write an {BRIEF_WORDS}-word executive briefing on “{topic}” based on these "
        f"{len(structured)} articles from the last 24 hours. "
        "Use [1], [2], … for citations. Maintain a neutral tone.\n\n"
        + summaries
    )

    print(brief_prompt)

    try:
        briefing = client.chat.completions.create(
            model=MODEL_ID,
            messages=[
                {"role": "system", "content": "Create an executive news briefing."},
                {"role": "user", "content": brief_prompt},
            ],
            max_tokens=MAX_TOKENS,
        ).choices[0].message.content.strip()
    except cb.APIStatusError as e:
        print("Briefing generation failed:", e); return

    print("\n*** 24-Hour News Briefing ***\n")
    print(briefing)
    print("\n*** References ***")
    for i, a in enumerate(structured, 1):
        print(f"[{i}] {a['title']} — {a['publisher']} "
              f"({a['publication_date']}) — {a['url']}")

    elapsed = (datetime.now(timezone.utc) - start).total_seconds()
    print(f"Completed in {elapsed:.1f} seconds")

if __name__ == "__main__":
    main()