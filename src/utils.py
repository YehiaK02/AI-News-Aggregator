"""
Utility functions for the AI News Aggregator
"""

import re
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def extract_date_from_text(text: str) -> Optional[str]:
    """
    Extract date from text using common patterns
    
    Args:
        text: Text to search for dates
        
    Returns:
        Date in YYYY-MM-DD format or None
    """
    # Pattern: YYYY-MM-DD
    pattern1 = r'\d{4}-\d{2}-\d{2}'
    match = re.search(pattern1, text)
    if match:
        return match.group(0)
    
    # Pattern: DD/MM/YYYY or MM/DD/YYYY
    pattern2 = r'\d{2}/\d{2}/\d{4}'
    match = re.search(pattern2, text)
    if match:
        try:
            date_str = match.group(0)
            # Assume MM/DD/YYYY format
            date_obj = datetime.strptime(date_str, '%m/%d/%Y')
            return date_obj.strftime('%Y-%m-%d')
        except ValueError:
            pass
    
    return None


def clean_text(text: str) -> str:
    """
    Clean text by removing extra whitespace and special characters
    
    Args:
        text: Text to clean
        
    Returns:
        Cleaned text
    """
    if not text:
        return ""
    
    # Remove extra whitespace
    text = re.sub(r'\s+', ' ', text)
    
    # Remove leading/trailing whitespace
    text = text.strip()
    
    return text


def truncate_text(text: str, max_length: int = 1000) -> str:
    """
    Truncate text to maximum length
    
    Args:
        text: Text to truncate
        max_length: Maximum length
        
    Returns:
        Truncated text
    """
    if len(text) <= max_length:
        return text
    
    return text[:max_length] + "..."


def extract_urls(text: str) -> list:
    """
    Extract all URLs from text
    
    Args:
        text: Text to search
        
    Returns:
        List of URLs
    """
    url_pattern = r'https?://[^\s<>"{}|\\^`\[\]]+'
    urls = re.findall(url_pattern, text)
    return list(set(urls))  # Remove duplicates


def is_within_timeframe(date_str: str, hours: int = 24) -> bool:
    """
    Check if a date string is within the specified timeframe
    
    Args:
        date_str: Date string (ISO format)
        hours: Number of hours to look back
        
    Returns:
        True if within timeframe, False otherwise
    """
    try:
        date_obj = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
        cutoff = datetime.now() - timedelta(hours=hours)
        return date_obj > cutoff
    except (ValueError, AttributeError):
        return False


def format_money(amount: int) -> str:
    """
    Format money amount for display
    
    Args:
        amount: Amount in dollars
        
    Returns:
        Formatted string (e.g., "$50M", "$1.5B")
    """
    if amount >= 1_000_000_000:
        return f"${amount / 1_000_000_000:.1f}B"
    elif amount >= 1_000_000:
        return f"${amount / 1_000_000:.0f}M"
    else:
        return f"${amount:,}"


def extract_money_amount(text: str) -> Optional[int]:
    """
    Extract dollar amounts from text
    
    Args:
        text: Text to search
        
    Returns:
        Amount in dollars or None
    """
    # Pattern: $X million, $X billion, $XM, $XB
    patterns = [
        (r'\$(\d+(?:\.\d+)?)\s*billion', 1_000_000_000),
        (r'\$(\d+(?:\.\d+)?)\s*million', 1_000_000),
        (r'\$(\d+(?:\.\d+)?)B', 1_000_000_000),
        (r'\$(\d+(?:\.\d+)?)M', 1_000_000),
    ]
    
    for pattern, multiplier in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            amount = float(match.group(1)) * multiplier
            return int(amount)
    
    return None


def validate_url(url: str) -> bool:
    """
    Validate if string is a valid URL
    
    Args:
        url: URL to validate
        
    Returns:
        True if valid URL
    """
    url_pattern = r'^https?://[^\s<>"{}|\\^`\[\]]+$'
    return bool(re.match(url_pattern, url))


class RateLimiter:
    """Simple rate limiter to avoid overwhelming APIs"""
    
    def __init__(self, max_calls: int, time_window: int):
        """
        Initialize rate limiter
        
        Args:
            max_calls: Maximum number of calls
            time_window: Time window in seconds
        """
        self.max_calls = max_calls
        self.time_window = time_window
        self.calls = []
    
    def can_proceed(self) -> bool:
        """Check if we can make another call"""
        now = datetime.now()
        
        # Remove old calls outside time window
        self.calls = [
            call_time for call_time in self.calls
            if (now - call_time).total_seconds() < self.time_window
        ]
        
        return len(self.calls) < self.max_calls
    
    def record_call(self):
        """Record a new call"""
        self.calls.append(datetime.now())


def safe_get(dictionary: Dict, *keys, default=None) -> Any:
    """
    Safely get nested dictionary values
    
    Args:
        dictionary: Dictionary to search
        *keys: Nested keys to access
        default: Default value if key not found
        
    Returns:
        Value or default
    """
    for key in keys:
        try:
            dictionary = dictionary[key]
        except (KeyError, TypeError, IndexError):
            return default
    return dictionary
