"""
RSS Feed Discovery Module
Fetches articles from configured RSS feeds
"""

import feedparser
import yaml
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


class FeedDiscoverer:
    """Discovers and fetches articles from RSS feeds"""
    
    def __init__(self, config_path: str = "../config/sources.yaml"):
        """Initialize feed discoverer"""
        self.config_path = Path(config_path)
        self.sources = self._load_sources()
        self.settings = self._load_settings()
    
    def _load_sources(self) -> Dict:
        """Load RSS feed sources from config"""
        try:
            with open(self.config_path, 'r') as f:
                config = yaml.safe_load(f)
                return config.get('sources', {})
        except FileNotFoundError:
            logger.error(f"Config file not found: {self.config_path}")
            return {}
        except yaml.YAMLError as e:
            logger.error(f"Error parsing config: {e}")
            return {}
    
    def _load_settings(self) -> Dict:
        """Load settings from config"""
        try:
            with open(self.config_path, 'r') as f:
                config = yaml.safe_load(f)
                return config.get('settings', {})
        except:
            return {
                'fetch_hours': 24,
                'max_articles_per_source': 50,
                'timeout_seconds': 30
            }
    
    def fetch_recent_articles(self, hours: Optional[int] = None) -> List[Dict]:
        """Fetch articles from all enabled RSS feeds"""
        if hours is None:
            hours = self.settings.get('fetch_hours', 24)
        
        cutoff = datetime.now() - timedelta(hours=hours)
        all_articles = []
        
        logger.info(f"🔍 Fetching articles from last {hours} hours...")
        
        for source_id, source_config in self.sources.items():
            if not source_config.get('enabled', True):
                logger.info(f"⏭️  Skipping disabled source: {source_id}")
                continue
            
            try:
                articles = self._fetch_from_source(source_id, source_config, cutoff)
                all_articles.extend(articles)
                logger.info(f"✅ {source_config['name']}: Found {len(articles)} articles")
            except Exception as e:
                logger.error(f"❌ Error fetching from {source_config['name']}: {e}")
                continue
        
        logger.info(f"\n📊 Total articles discovered: {len(all_articles)}")
        return all_articles
    
    def _fetch_from_source(self, source_id: str, source_config: Dict, cutoff: datetime) -> List[Dict]:
        """Fetch articles from a single RSS feed"""
        url = source_config['url']
        timeout = self.settings.get('timeout_seconds', 30)
        
        logger.debug(f"Fetching RSS from: {url}")
        feed = feedparser.parse(url)
        
        if feed.bozo:
            logger.warning(f"Feed parse warning for {source_id}: {feed.bozo_exception}")
        
        articles = []
        max_articles = self.settings.get('max_articles_per_source', 50)
        
        for entry in feed.entries[:max_articles]:
            try:
                pub_date = self._parse_date(entry)
                if pub_date is None or pub_date < cutoff:
                    continue
                
                article = {
                    'title': entry.get('title', 'Untitled').strip(),
                    'url': entry.get('link', ''),
                    'summary': entry.get('summary', entry.get('description', '')).strip(),
                    'published': pub_date.isoformat(),
                    'source': source_id,
                    'source_name': source_config['name'],
                    'author': entry.get('author', ''),
                }
                articles.append(article)
            except Exception as e:
                logger.debug(f"Error parsing entry: {e}")
                continue
        
        return articles
    
    def _parse_date(self, entry) -> Optional[datetime]:
        """Parse publication date from feed entry"""
        if hasattr(entry, 'published_parsed') and entry.published_parsed:
            try:
                return datetime(*entry.published_parsed[:6])
            except:
                pass
        
        if hasattr(entry, 'updated_parsed') and entry.updated_parsed:
            try:
                return datetime(*entry.updated_parsed[:6])
            except:
                pass
        
        return None
    
    def get_source_stats(self) -> Dict:
        """Get statistics about configured sources"""
        enabled = sum(1 for s in self.sources.values() if s.get('enabled', True))
        return {
            'total_sources': len(self.sources),
            'enabled_sources': enabled,
            'disabled_sources': len(self.sources) - enabled,
            'sources': {name: config['name'] for name, config in self.sources.items() if config.get('enabled', True)}
        }
