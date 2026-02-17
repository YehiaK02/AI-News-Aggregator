"""
Article Classification Module
Uses Groq AI to classify articles into categories
"""

import os
import json
import yaml
from pathlib import Path
from typing import Dict, List, Optional
import logging
from groq import Groq

logger = logging.getLogger(__name__)


class ArticleClassifier:
    """Classifies articles using AI and category rules"""
    
    def __init__(
        self,
        groq_api_key: Optional[str] = None,
        categories_file: str = "../config/categories.yaml",
        prompt_file: str = "../config/classification_prompt.txt"
    ):
        """Initialize classifier"""
        api_key = groq_api_key or os.getenv('GROQ_API_KEY')
        if not api_key:
            raise ValueError("GROQ_API_KEY must be provided or set in environment")
        
        self.groq = Groq(api_key=api_key)
        self.categories = self._load_categories(categories_file)
        self.prompt_template = self._load_prompt(prompt_file)
    
    def _load_categories(self, filepath: str) -> Dict:
        """Load category definitions"""
        try:
            with open(filepath, 'r') as f:
                return yaml.safe_load(f)
        except Exception as e:
            logger.error(f"Error loading categories: {e}")
            return {}
    
    def _load_prompt(self, filepath: str) -> str:
        """Load classification prompt template"""
        try:
            with open(filepath, 'r') as f:
                return f.read()
        except Exception as e:
            logger.error(f"Error loading prompt: {e}")
            return ""
    
    def classify(self, article: Dict) -> Dict:
        """Classify a single article"""
        prompt = self.prompt_template.format(
            title=article.get('title', ''),
            summary=article.get('summary', ''),
            source=article.get('source_name', article.get('source', 'Unknown')),
            date=article.get('published', '')
        )
        
        try:
            response = self.groq.chat.completions.create(
                model="llama-3.1-70b-versatile",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,
                response_format={"type": "json_object"},
                max_tokens=500
            )
            
            result = json.loads(response.choices[0].message.content)
            result['article'] = article
            result = self._apply_rules(result, article)
            
            logger.debug(
                f"Classified '{article['title'][:50]}...' as "
                f"{result.get('category', 'rejected')} "
                f"(confidence: {result.get('confidence', 0):.2f})"
            )
            
            return result
            
        except json.JSONDecodeError as e:
            logger.error(f"Error parsing JSON response: {e}")
            return self._error_result(article, f"JSON parse error: {e}")
        except Exception as e:
            logger.error(f"Error classifying article: {e}")
            return self._error_result(article, str(e))
    
    def _apply_rules(self, result: Dict, article: Dict) -> Dict:
        """Apply rule-based enhancements to AI classification"""
        if result.get('category') == 'enterprise_strategy':
            text = article.get('title', '') + ' ' + article.get('summary', '')
            money = self._extract_money_amount(text)
            
            if money:
                min_amount = 50000000  # $50M
                if money < min_amount:
                    result['relevant'] = False
                    result['confidence'] = max(result['confidence'] - 0.3, 0)
                    result['reason'] += f" (Funding ${money:,} below threshold)"
        
        return result
    
    def _extract_money_amount(self, text: str) -> Optional[int]:
        """Extract dollar amounts from text"""
        import re
        patterns = [
            (r'\$(\d+(?:\.\d+)?)\s*billion', 1_000_000_000),
            (r'\$(\d+(?:\.\d+)?)\s*million', 1_000_000),
            (r'\$(\d+(?:\.\d+)?)B', 1_000_000_000),
            (r'\$(\d+(?:\.\d+)?)M', 1_000_000),
        ]
        
        for pattern, multiplier in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return int(float(match.group(1)) * multiplier)
        return None
    
    def _error_result(self, article: Dict, error: str) -> Dict:
        """Create error result"""
        return {
            'relevant': False,
            'category': None,
            'tier': None,
            'confidence': 0,
            'reason': f'Classification error: {error}',
            'key_signals': [],
            'article': article
        }
    
    def classify_batch(self, articles: List[Dict]) -> Dict[str, List[Dict]]:
        """Classify multiple articles and sort into tiers"""
        results = {
            'tier1': [],
            'tier2': [],
            'rejected': []
        }
        
        logger.info(f"\n🤖 Classifying {len(articles)} articles...")
        
        for i, article in enumerate(articles, 1):
            logger.info(f"   [{i}/{len(articles)}] {article['title'][:60]}...")
            
            classification = self.classify(article)
            
            if not classification['relevant']:
                results['rejected'].append(classification)
            elif classification['tier'] == 1 and classification['confidence'] >= 0.7:
                results['tier1'].append(classification)
                logger.info(f"      ✅ Tier 1: {classification['category']} ({classification['confidence']:.2f})")
            elif classification['tier'] == 2 and classification['confidence'] >= 0.6:
                results['tier2'].append(classification)
                logger.info(f"      ⚠️  Tier 2: {classification['category']} ({classification['confidence']:.2f})")
            else:
                results['rejected'].append(classification)
                logger.info(f"      ❌ Rejected ({classification['confidence']:.2f})")
        
        logger.info(f"\n📊 Classification Results:")
        logger.info(f"   ✅ Tier 1 (auto-process): {len(results['tier1'])}")
        logger.info(f"   ⚠️  Tier 2 (review): {len(results['tier2'])}")
        logger.info(f"   ❌ Rejected: {len(results['rejected'])}\n")
        
        return results
