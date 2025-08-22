from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig, CacheMode
import os

app = FastAPI()

# Optional shared secret (set on Railway)
C4A_SECRET = os.environ.get("C4A_SECRET", "")

class CrawlRequest(BaseModel):
    url: str
    config: Optional[Dict[str, Any]] = Field(default_factory=dict)

@app.post("/crawl")
async def crawl(req: CrawlRequest, x_c4a_secret: str = Header(default="")):
    if C4A_SECRET and x_c4a_secret != C4A_SECRET:
        raise HTTPException(status_code=401, detail="Unauthorized")

    browser_cfg = BrowserConfig(browser_type="chromium", headless=True, verbose=False)

    cache_mode = (req.config.get("cache_mode") or "bypass").lower()
    css_selector = req.config.get("css_selector")
    word_count_threshold = req.config.get("word_count_threshold", 10)
    screenshot = bool(req.config.get("screenshot", False))

    run_cfg = CrawlerRunConfig(
        cache_mode=CacheMode.BYPASS if cache_mode == "bypass" else CacheMode.DEFAULT,
        css_selector=css_selector,
        word_count_threshold=word_count_threshold,
        screenshot=screenshot,
    )

    async with AsyncWebCrawler(config=browser_cfg) as crawler:
        result = await crawler.arun(url=req.url, config=run_cfg)

    return {
        "success": bool(result.success),
        "url": result.url,
        "html": result.html,
        "cleaned_html": result.cleaned_html,
        "markdown": getattr(result, "markdown", None),
        "extracted_content": result.extracted_content,
        "error_message": result.error_message,
    }
