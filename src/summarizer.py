"""
Summarizer Module
Uses Groq AI to generate comprehensive article summaries
"""

import os
import logging
from typing import Dict, List, Optional
from pathlib import Path
from groq import Groq

from utils import clean_text

logger = logging.getLogger(__name__)


class Summarizer:
    """Generates article summaries using Groq AI"""
    
    def __init__(
        self,
        groq_api_key: Optional[str] = None,
        system_prompt_file: str = "../config/system_prompt.txt"
    ):
        """
        Initialize summarizer
        
        Args:
            groq_api_key: Groq API key (or from environment)
            system_prompt_file: Path to system prompt template
        """
        # Initialize Groq
        api_key = groq_api_key or os.getenv('GROQ_API_KEY')
        if not api_key:
            raise ValueError("GROQ_API_KEY must be provided or set in environment")
        
        self.groq = Groq(api_key=api_key)
        
        # Load system prompt
        self.system_prompt = self._load_prompt(system_prompt_file)
    
    def _load_prompt(self, filepath: str) -> str:
        """Load system prompt template"""
        try:
            with open(filepath, 'r') as f:
                return f.read()
        except Exception as e:
            logger.error(f"Error loading system prompt: {e}")
            return ""
    
    def summarize(
        self,
        article: Dict,
        related_sources: List[Dict]
    ) -> Dict:
        """
        Generate comprehensive summary for an article
        
        Args:
            article: Main article with title, content, url
            related_sources: List of related sources from research
            
        Returns:
            Summary dictionary with formatted output
        """
        try:
            # Build context from main article and sources
            context = self._build_context(article, related_sources)
            
            logger.debug(f"Generating summary for: {article.get('title', 'Unknown')[:50]}...")
            
            # Call Groq for summarization
            response = self.groq.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": context}
                ],
                temperature=0.3,  # Slightly higher for more natural writing
                max_tokens=2000
            )
            
            summary_text = response.choices[0].message.content
            
            # Parse the formatted output
            parsed = self._parse_summary(summary_text)
            
            # Add metadata
            parsed['original_url'] = article.get('url', '')
            parsed['source_count'] = len(related_sources)
            
            logger.debug(f"Summary generated successfully")
            
            return parsed
            
        except Exception as e:
            logger.error(f"Error generating summary: {e}")
            raise
    
    def _build_context(
        self,
        article: Dict,
        related_sources: List[Dict]
    ) -> str:
        """
        Build context from article and sources for summarization
        
        Args:
            article: Main article
            related_sources: Related sources
            
        Returns:
            Formatted context string
        """
        context_parts = []
        
        # Main article
        context_parts.append("=== MAIN ARTICLE ===\n")
        context_parts.append(f"Title: {article.get('title', 'Unknown')}\n")
        context_parts.append(f"URL: {article.get('url', '')}\n")
        context_parts.append(f"Date: {article.get('date', '')}\n")
        context_parts.append(f"\nContent:\n{article.get('content', '')[:5000]}\n")
        
        # Related sources
        if related_sources:
            context_parts.append("\n=== RELATED SOURCES ===\n")
            
            for i, source in enumerate(related_sources[:10], 1):
                context_parts.append(f"\nSource {i}:\n")
                context_parts.append(f"URL: {source.get('url', '')}\n")
                context_parts.append(f"Title: {source.get('title', '')}\n")
                context_parts.append(f"Content: {source.get('content', '')[:1000]}\n")
        
        context_parts.append("\n=== YOUR TASK ===\n")
        context_parts.append(
            "Synthesize the main article and related sources into a "
            "comprehensive summary following the exact format specified in "
            "your system prompt. Focus on enterprise implications, technical "
            "details, and competitive context."
        )
        
        return ''.join(context_parts)
    
    def _parse_summary(self, summary_text: str) -> Dict:
        """
        Parse the formatted summary output
        
        Args:
            summary_text: Raw summary text from AI
            
        Returns:
            Parsed dictionary
        """
        result = {
            'date': '',
            'title': '',
            'summary': '',
            'sources': []
        }
        
        # Split into sections
        lines = summary_text.split('\n')
        
        current_section = None
        summary_lines = []
        
        for line in lines:
            line = line.strip()
            
            # Detect sections
            if line.startswith('Date:'):
                result['date'] = line.replace('Date:', '').strip()
            elif line.startswith('Title:'):
                current_section = 'title'
            elif line.startswith('Summary:'):
                current_section = 'summary'
            elif line.startswith('Links:') or line.startswith('Sources:'):
                current_section = 'links'
            elif line.startswith('http'):
                result['sources'].append(line)
            elif current_section == 'title' and line:
                result['title'] = line
            elif current_section == 'summary' and line:
                summary_lines.append(line)
        
        # Join summary paragraphs
        result['summary'] = '\n\n'.join(summary_lines)
        
        return result
    
    def format_for_sheets(self, summary: Dict, category: str = '') -> Dict:
        """
        Format summary data for Google Sheets
        
        Args:
            summary: Parsed summary
            category: Article category
            
        Returns:
            Formatted row data
        """
        return {
            'date': summary.get('date', ''),
            'title': summary.get('title', ''),
            'summary': summary.get('summary', ''),
            'sources': '\n'.join(summary.get('sources', [])),
            'source_count': len(summary.get('sources', [])),
            'category': category,
            'original_url': summary.get('original_url', '')
        }
