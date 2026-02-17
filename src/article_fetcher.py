"""
Article Fetcher Module
Uses Jina Reader to fetch clean article content
"""

import requests
import logging
from typing import Dict, Optional
from utils import clean_text, extract_date_from_text

logger = logging.getLogger(__name__)


class ArticleFetcher:
    """Fetches clean article content using Jina Reader"""
    
    def __init__(self):
        """Initialize article fetcher"""
        self.jina_base_url = "https://r.jina.ai/"
    
    def fetch(self, url: str) -> Dict:
        """
        Fetch clean article content from URL
        
        Args:
            url: Article URL
            
        Returns:
            Dictionary with title, content, date, etc.
        """
        try:
            logger.debug(f"Fetching article: {url}")
            
            # Use Jina Reader to get clean content
            jina_url = f"{self.jina_base_url}{url}"
            
            response = requests.get(jina_url, timeout=30)
            response.raise_for_status()
            
            content = response.text
            
            # Extract metadata
            article = {
                'url': url,
                'title': self._extract_title(content),
                'date': self._extract_date(content),
                'content': clean_text(content),
                'raw_content': content
            }
            
            logger.debug(f"Successfully fetched article: {article['title'][:50]}...")
            
            return article
            
        except requests.Timeout:
            logger.error(f"Timeout fetching article: {url}")
            raise
        except requests.RequestException as e:
            logger.error(f"Error fetching article {url}: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error fetching {url}: {e}")
            raise
    
    def _extract_title(self, content: str) -> str:
        """
        Extract title from markdown content
        
        Args:
            content: Article content
            
        Returns:
            Title or "Untitled"
        """
        lines = content.split('\n')
        
        # Look for markdown h1 heading
        for line in lines[:20]:  # Check first 20 lines
            if line.startswith('# '):
                return clean_text(line.replace('# ', ''))
        
        return "Untitled"
    
    def _extract_date(self, content: str) -> Optional[str]:
        """
        Extract publication date from content
        
        Args:
            content: Article content
            
        Returns:
            Date in YYYY-MM-DD format or None
        """
        # Check first 1000 characters for date
        snippet = content[:1000]
        return extract_date_from_text(snippet)
    
    def fetch_batch(self, urls: list) -> Dict[str, Dict]:
        """
        Fetch multiple articles
        
        Args:
            urls: List of URLs
            
        Returns:
            Dictionary mapping URL to article data
        """
        results = {}
        
        for url in urls:
            try:
                article = self.fetch(url)
                results[url] = article
            except Exception as e:
                logger.error(f"Failed to fetch {url}: {e}")
                results[url] = {
                    'url': url,
                    'error': str(e)
                }
        
        return results
