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
    country: str = "in",
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
    
    url = "https://newsapi.org/v2/top-headlines"
    params = {
        "apiKey": api_key,
        "country": country,
        "category": category,
        "pageSize": min(page_size, 100)  # NewsAPI max is 100
    }
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url, params=params)
            response.raise_for_status()
            data = response.json()
        
        if data.get("status") != "ok":
            raise HTTPException(status_code=400, detail=data.get("message", "NewsAPI error"))
        
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
        
        return NewsResponse(
            articles=articles,
            total_results=data.get("totalResults", len(articles))
        )
        
    except httpx.HTTPError as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch news: {str(e)}")