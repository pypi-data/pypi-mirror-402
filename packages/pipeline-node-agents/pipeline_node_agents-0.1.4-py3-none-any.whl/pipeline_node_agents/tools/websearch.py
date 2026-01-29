import time
from ddgs import DDGS

class WebSearcher:
    @staticmethod
    def duckduckgo_search(query: str, max_results: int = 5) -> dict:
        max_attempts = 5
        with DDGS() as ddgs:
            for attempt in range(max_attempts):
                try:
                    results = ddgs.text(
                        query=query,
                        max_results=max_results,
                        region='wt-wt',
                        backend='lite'
                    )

                    parsed_results = [
                        {
                            "title": r.get("title"),
                            "snippet": r.get("body"),
                            "url": r.get("href")
                        }
                        for r in results
                    ]

                    return parsed_results

                except Exception as e:
                    print(f"Retry due to: {e}")
                    time.sleep(1.2 * (attempt + 1))

            raise RuntimeError("DuckDuckGo search failed after retries")

if __name__ == "__main__":
    def main():
        results = WebSearcher.duckduckgo_search("best ski resorts", max_results=5)
        
        print("Search Results for 'best ski resorts':\n")
        for idx, result in enumerate(results, 1):
            print(f"{idx}. {result['title']}")
            print(f"   URL: {result['url']}")
            print(f"   Snippet: {result['snippet']}\n")
    
    main()

