"""
Research Agent Module
Uses Tavily API to find related sources
"""

import os
import logging
from typing import List, Dict, Optional
from tavily import TavilyClient

from utils import clean_text, validate_url

logger = logging.getLogger(__name__)


class ResearchAgent:
    """Researches related sources using Tavily API"""
    
    def __init__(self, tavily_api_key: Optional[str] = None):
        """
        Initialize research agent
        
        Args:
            tavily_api_key: Tavily API key (or from environment)
        """
        api_key = tavily_api_key or os.getenv('TAVILY_API_KEY')
        if not api_key:
            raise ValueError("TAVILY_API_KEY must be provided or set in environment")
        
        self.client = TavilyClient(api_key=api_key)
    
    def research(
        self,
        query: str,
        max_results: int = 10
    ) -> List[Dict]:
        """
        Research a topic and find related sources
        
        Args:
            query: Search query (usually article title)
            max_results: Maximum number of results to return
            
        Returns:
            List of source dictionaries
        """
        try:
            logger.debug(f"Researching: {query}")
            
            # Search with Tavily
            response = self.client.search(
                query=query,
                max_results=max_results,
                search_depth="basic",
                include_answer=False,
                include_raw_content=False
            )
            
            sources = []
            
            for result in response.get('results', []):
                source = {
                    'url': result.get('url', ''),
                    'title': clean_text(result.get('title', '')),
                    'content': clean_text(result.get('content', '')),
                    'score': result.get('score', 0)
                }
                
                # Validate URL
                if validate_url(source['url']):
                    sources.append(source)
            
            logger.debug(f"Found {len(sources)} related sources")
            
            return sources
            
        except Exception as e:
            logger.error(f"Error researching topic: {e}")
            return []
    
    def get_source_urls(self, query: str, max_results: int = 10) -> List[str]:
        """
        Get just the URLs from research
        
        Args:
            query: Search query
            max_results: Maximum results
            
        Returns:
            List of URLs
        """
        sources = self.research(query, max_results)
        return [s['url'] for s in sources]
    
    def research_article(
        self,
        article: Dict,
        max_results: int = 10
    ) -> List[Dict]:
        """
        Research related sources for an article
        
        Args:
            article: Article dictionary with title
            max_results: Maximum results
            
        Returns:
            List of related sources
        """
        query = article.get('title', '')
        
        if not query:
            logger.warning("No title provided for research")
            return []
        
        return self.research(query, max_results)
