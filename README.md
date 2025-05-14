# News Agent
Generate a real-time, 800-word executive briefing from live news articles using Cerebras Inference and GNews.

News Agent is a simple agent that pulls the latest news on any topic and uses a Cerebras Inference to extract structured article summaries and generate a polished report with citations.

## Features
* Live news via GNews — searches the last 24 hours.
* Strict JSON extraction — ensures clean metadata (title, URL, publisher, etc.).
* 800-word executive briefing — with inline citations and a reference list.
* Fast inference — generates the briefing in ~3 seconds.

## Example Output

```bash
$ python news_agent.py
Topic: Apple Vision Pro
🔍  Fetching news on “Apple Vision Pro”…

*** 24-Hour News Briefing ***

Apple has once again made waves with the second-generation Vision Pro headset [1][2]...

*** References ***
[1] Apple reveals Vision Pro 2 — TechCrunch (2025-05-05T09:30:00Z) — https://...
[2] ...
⏱  Completed in 3.2 seconds
```

## QuickStart

1. Clone the repo
```bash
git clone https://github.com/your-org/news-agent.git
cd news-agent
```

2. Install dependencies
```bash
pip install requests cerebras-cloud-sdk
```

3. Configure API keys
Get your API keys for [Cerebras](https://inference.cerebras.ai/) and [GNews](https://gnews.io/), then configure them as such: 
```bash
export CEREBRAS_API_KEY="cb-xxxxxxxx"
export GNEWS_API_KEY="gnews-xxxxxxxx"
```
4. Run the agent
```bash
python news_agent.py
```
