import asyncio
from app.agents.scraper_agent import ScraperAgent
from app.models.schemas import ScrapeRequest

async def run_tests():
    print("\n=== Starting Scraping Tests ===")
    scraper = ScraperAgent()
    
    test_urls = [
        ("https://www.bct.gov.tn", "BCT"),
        ("https://www.ins.tn", "INS"),
        ("https://www.tunisieindustrie.nat.tn", "Tunisie Industrie")
    ]
    
    for url, source in test_urls:
        print(f"\nTesting URL: {url}")
        request = ScrapeRequest(url=url)
        
        try:
            result = await scraper.scrape(request)
            
            if result.content:
                print(f"✅ Success! Method: {result.metadata.get('method')}")
                print(f"Source: {source}")
                if result.content.structured_data:
                    print("Sample data:", list(result.content.structured_data.items())[:2])
            else:
                print(f"❌ Failed: {result.metadata.get('error', 'Unknown error')}")
                
        except Exception as e:
            print(f"⚠️ Critical error: {str(e)}")
    
    print("\n=== Tests completed ===")

if __name__ == "__main__":
    asyncio.run(run_tests())