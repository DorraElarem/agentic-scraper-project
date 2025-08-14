import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)
BASE_URL = "http://testserver"

def test_system_status():
    response = client.get(f"{BASE_URL}/system/status")
    assert response.status_code == 200

def test_scrape_endpoint():
    response = client.get("/")
    assert response.status_code == 200
    assert "status" in response.json()

def test_task_creation():
    test_data = {
        "urls": ["https://www.bct.gov.tn"],
        "mode": "auto"
    }
    response = client.post("/tasks", json=test_data)
    assert response.status_code in [200, 201]
    data = response.json()
    assert "task_id" in data
    assert "status" in data

@pytest.mark.asyncio
async def test_async_scraping():
    from app.agents.scraper_agent import ScraperAgent, ScrapeRequest
    scraper = ScraperAgent()
    request = ScrapeRequest(url="https://www.example.com")
    result = await scraper.scrape(request)
    assert result.url == "https://www.example.com"
    assert result.status_code in [200, 500]