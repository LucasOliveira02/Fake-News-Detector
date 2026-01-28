from duckduckgo_search import DDGS
import json

def test_search():
    query = "The queen of england died in 2022"
    sites = ["apnews.com", "www.reuters.com", "www.bbc.com"]
    # site_query = " OR ".join([f"site:{s}" for s in sites])
    # full_query = f"{query} ({site_query})"
    
    # Try simpler query
    full_query = query # Just the text
    
    print(f"Testing Query: {full_query}")
    
    try:
        with DDGS() as ddgs:
            results = list(ddgs.text(full_query, max_results=5, backend="lite"))
            print(f"Found {len(results)} results:")
            for r in results:
                print(r)
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_search()
