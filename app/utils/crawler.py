import aiohttp
import asyncio
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from typing import Set, List
import logging

logger = logging.getLogger(__name__)

class WebsiteCrawler:
    def __init__(self, base_url: str, max_pages: int = 100):
        self.base_url = base_url
        self.max_pages = max_pages
        self.domain = urlparse(base_url).netloc
        self.visited_urls: Set[str] = set()
        self.found_urls: Set[str] = set()
        
    async def crawl(self) -> List[str]:
        """Crawl website and return list of all pages"""
        async with aiohttp.ClientSession() as session:
            await self._crawl_page(session, self.base_url)
        
        return list(self.found_urls)[:self.max_pages]
    
    async def _crawl_page(self, session: aiohttp.ClientSession, url: str):
        """Recursively crawl a single page"""
        if url in self.visited_urls or len(self.found_urls) >= self.max_pages:
            return
            
        self.visited_urls.add(url)
        
        try:
            async with session.get(url, timeout=10) as response:
                if response.status == 200:
                    self.found_urls.add(url)
                    
                    # Only crawl HTML pages
                    content_type = response.headers.get('content-type', '')
                    if 'text/html' in content_type:
                        html = await response.text()
                        await self._extract_links(session, html, url)
                        
        except Exception as e:
            logger.error(f"Error crawling {url}: {e}")
    
    async def _extract_links(self, session: aiohttp.ClientSession, html: str, base_url: str):
        """Extract and crawl links from HTML"""
        soup = BeautifulSoup(html, 'html.parser')
        
        for link in soup.find_all('a', href=True):
            href = link['href']
            full_url = urljoin(base_url, href)
            
            # Only crawl same domain links
            if urlparse(full_url).netloc == self.domain:
                # Remove fragments and query params for deduplication
                clean_url = full_url.split('#')[0].split('?')[0]
                
                if clean_url not in self.visited_urls and len(self.found_urls) < self.max_pages:
                    await self._crawl_page(session, clean_url)