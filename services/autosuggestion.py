from fastapi import FastAPI, APIRouter
from fastapi.responses import JSONResponse
import httpx
import time

suggester = APIRouter()

GENE_API_URL = "https://www.genenames.org/cgi-bin/search/suggest?query="
headers = headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.7049.52 Safari/537.36",
    "Accept": "application/json",
    }

SUGGESTERS = [
    "groupNameBlendSuggester", "pageTitleBlendSuggester", "symbolSuggester",
    "prevSymbolSuggester", "nameBlendSuggester", "aliasSymbolSuggester"
]

def extract_suggestions(data: dict, query: str) -> dict:
    suggest_data = data.get("suggest", {})
    result = {}

    for s in SUGGESTERS:
        query_data = suggest_data.get(s, {}).get(query, {}).get("suggestions", [])
        if s in {"groupNameBlendSuggester", "pageTitleBlendSuggester"}:
            result[s] = query_data
        else:
            result[s] = [item.get("term", "") for item in query_data]

    return result

@suggester.get("/suggest", response_class=JSONResponse)
async def search_api(query: str = ""):
    if not query or len(query) < 2:
        return {
            "results": {}, "total_displayed": 0,
            "total_available": 0, "response_time": 0
        }

    start_time = time.perf_counter()

    async with httpx.AsyncClient(timeout=5.0) as client:
        try:
            start_api = time.perf_counter()
            response = await client.get(f"{GENE_API_URL}{query}", headers=headers)
            data = response.json() if response.status_code == 200 else {}
            end_api = time.perf_counter()
            print("api", end_api - start_api)   
        except (httpx.RequestError, ValueError) as e:
            return {
                "results": {}, "total_displayed": 0,
                "total_available": 0, "response_time": round(time.perf_counter() - start_time, 2)
            }
    print("suggestor", round(time.perf_counter() - start_time, 2))
    results = extract_suggestions(data, query)
    max_per_category = 20
    limited_results = {k: v[:max_per_category] for k, v in results.items()}

    total_displayed = sum(len(v) for v in limited_results.values())
    total_available = sum(len(v) for v in results.values())
    response_time = round(time.perf_counter() - start_time, 2)

    return {
        "results": limited_results,
        "total_displayed": total_displayed,
        "total_available": total_available,
        "response_time": response_time,
        "categories": list(limited_results.keys()),
        "max_per_category": max_per_category
    }
