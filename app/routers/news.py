import os
from datetime import datetime, timezone
from typing import List, Optional

import httpx
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter()


class NewsArticle(BaseModel):
    title: str
    description: Optional[str]
    url: str
    source: str
    published_at: str
    url_to_image: Optional[str]


class NewsResponse(BaseModel):
    articles: List[NewsArticle]
    total_results: int


@router.get("/news", response_model=NewsResponse)
async def get_news(
    category: str = "general",
    page_size: int = 20
):
    """
    Fetch latest news from NewsAPI.org
    Categories: business, entertainment, general, health, science, sports, technology
    """
    api_key = os.getenv("NEWSAPI_KEY")
    if not api_key:
        raise HTTPException(status_code=500, detail="NewsAPI key not configured")
    
    # Map category to match NewsAPI categories
    valid_categories = ["business", "entertainment", "general", "health", "science", "sports", "technology"]
    if category not in valid_categories:
        category = "general"
    
    # Try multiple approaches for better results
    attempts = [
        # First try: category only (no country filter)
        {
            "apiKey": api_key,
            "category": category,
            "pageSize": min(page_size, 100)
        },
        # Fallback: general news without any filters
        {
            "apiKey": api_key,
            "pageSize": min(page_size, 100)
        }
    ]
    
    url = "https://newsapi.org/v2/top-headlines"
    
    for i, params in enumerate(attempts):
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(url, params=params)
                response.raise_for_status()
                data = response.json()
            
            if data.get("status") != "ok":
                print(f"NewsAPI attempt {i+1} failed: {data.get('message')}")
                continue
            
            # If we get results, process them
            if data.get("totalResults", 0) > 0:
                articles = []
                for article in data.get("articles", []):
                    # Skip articles with removed/null content
                    if not article.get("title") or article.get("title") == "[Removed]":
                        continue
                        
                    articles.append(NewsArticle(
                        title=article["title"],
                        description=article.get("description"),
                        url=article["url"],
                        source=article["source"]["name"],
                        published_at=article["publishedAt"],
                        url_to_image=article.get("urlToImage")
                    ))
                
                print(f"NewsAPI success on attempt {i+1}, got {len(articles)} articles")
                return NewsResponse(
                    articles=articles,
                    total_results=data.get("totalResults", len(articles))
                )
            else:
                print(f"NewsAPI attempt {i+1} returned 0 results")
                
        except Exception as e:
            print(f"NewsAPI attempt {i+1} error: {str(e)}")
            continue
    
    # If all attempts fail, return empty but valid response
    print("All NewsAPI attempts failed, returning empty response")
    return NewsResponse(articles=[], total_results=0)