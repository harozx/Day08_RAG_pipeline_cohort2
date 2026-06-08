import asyncio
from crawl4ai import AsyncWebCrawler
async def test():
    async with AsyncWebCrawler() as c:
        r = await c.arun('https://tuoitre.vn/dj-thai-hoang-bi-bat-vi-tang-tru-ma-tuy-20230425105653423.htm', css_selector=".detail-content")
        print("markdown len:", len(r.markdown.raw_markdown))
asyncio.run(test())
