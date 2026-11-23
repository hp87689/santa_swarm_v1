"""Lightweight public research discovery: metadata only, no web code executed."""
import json
import urllib.parse
import urllib.request
from pathlib import Path

TOPICS = [
    "addition chains optimization", "arithmetic circuit synthesis",
    "straight line program optimization", "e-graphs arithmetic rewriting",
    "integer multiplication chains", "register allocation expression DAG",
    "program superoptimization", "integer arithmetic expression search",
]


def request_json(url):
    req = urllib.request.Request(url, headers={
        "User-Agent": "SantaSwarmResearch/0.1 (research metadata; public competition)",
        "Accept": "application/json",
    })
    with urllib.request.urlopen(req, timeout=12) as res:
        return json.load(res)


def gather(seed=0):
    topic = TOPICS[seed % len(TOPICS)]
    results = []
    try:
        q = urllib.parse.urlencode({"query": topic, "rows": 4, "select": "DOI,title,URL,published"})
        data = request_json("https://api.crossref.org/works?" + q)
        for item in data.get("message", {}).get("items", []):
            results.append({"type": "paper", "title": " ".join(item.get("title", [])[:1])[:180],
                            "url": item.get("URL", "")[:300], "doi": item.get("DOI", "")[:100]})
    except Exception as err:
        results.append({"type": "status", "note": f"Crossref unavailable: {type(err).__name__}"})
    try:
        q = urllib.parse.urlencode({"q": "arithmetic circuit optimizer", "per_page": 4})
        data = request_json("https://api.github.com/search/repositories?" + q)
        for item in data.get("items", [])[:4]:
            results.append({"type": "repository", "title": item.get("full_name", "")[:160],
                            "url": item.get("html_url", "")[:300],
                            "description": (item.get("description") or "")[:200],
                            "license": (item.get("license") or {}).get("spdx_id", "unknown")})
    except Exception as err:
        results.append({"type": "status", "note": f"GitHub research unavailable: {type(err).__name__}"})
    result = {"topic": topic, "sources": results, "note": "Metadata is untrusted; follow licenses and Kaggle rules."}
    Path("logs").mkdir(exist_ok=True)
    Path("logs/research.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    return result
