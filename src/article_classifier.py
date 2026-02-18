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
                model="llama-3.3-70b-versatile",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,
                response_format={"type": "json_object"},
                max_tokens=500
            )
            
            raw = response.choices[0].message.content
            result = json.loads(raw)

            # Normalize keys — ensure expected fields exist with defaults
            result = {
                'relevant': result.get('relevant', False),
                'category': result.get('category'),
                'tier': result.get('tier'),
                'confidence': float(result.get('confidence', 0)),
                'reason': result.get('reason', ''),
                'key_signals': result.get('key_signals', []),
                'article': article
            }

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
    
    def _is_duplicate(self, title1: str, title2: str, threshold: float = 0.8) -> bool:
        """Check if two articles are about the same news event using Groq"""
        prompt = (
            "Are these two article titles about the same news event?\n\n"
            f"Title 1: {title1}\n"
            f"Title 2: {title2}\n\n"
            "Consider them the same event if they're reporting on the same:\n"
            "- Product launch/announcement\n"
            "- Funding round/acquisition\n"
            "- Partnership/deal\n"
            "- Research release\n\n"
            "Respond ONLY with JSON:\n"
            '{{"same_event": true/false, "confidence": 0.0-1.0, '
            '"reason": "brief explanation"}}'
        )

        try:
            response = self.groq.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,
                response_format={"type": "json_object"},
                max_tokens=150
            )

            raw = response.choices[0].message.content
            result = json.loads(raw)

            same = result.get('same_event', False)
            confidence = float(result.get('confidence', 0))

            if same and confidence >= threshold:
                logger.debug(
                    f"Duplicate detected ({confidence:.2f}): "
                    f"'{title1[:40]}...' ~ '{title2[:40]}...'"
                )
                return True
            return False

        except Exception as e:
            logger.warning(f"Duplicate check failed, treating as unique: {e}")
            return False

    def detect_duplicates(
        self,
        tier1_articles: List[Dict],
        source_priority: Dict[str, int],
        threshold: float = 0.8
    ) -> List[List[Dict]]:
        """Detect duplicate articles and group them together"""
        if not tier1_articles:
            return []

        groups = []
        processed = set()

        logger.info(f"\n🔍 Checking {len(tier1_articles)} articles for duplicates...")

        for i, article1 in enumerate(tier1_articles):
            if i in processed:
                continue

            group = [article1]

            for j, article2 in enumerate(tier1_articles[i + 1:], i + 1):
                if j in processed:
                    continue

                title1 = article1['article'].get('title', '')
                title2 = article2['article'].get('title', '')

                if self._is_duplicate(title1, title2, threshold):
                    group.append(article2)
                    processed.add(j)

            groups.append(group)

        # Select primary for each group and log results
        result_groups = []
        for group in groups:
            # Sort by source priority (lower = better), then by summary length (longer = better)
            group.sort(key=lambda x: (
                source_priority.get(x['article'].get('source', ''), 999),
                -len(x['article'].get('summary', ''))
            ))
            result_groups.append(group)

            if len(group) > 1:
                primary = group[0]['article']
                dup_titles = [g['article']['title'][:50] for g in group[1:]]
                logger.info(
                    f"   🔗 Found {len(group)} duplicates: "
                    f"Primary: '{primary['title'][:50]}...' "
                    f"({primary.get('source', 'unknown')})"
                )
                for title in dup_titles:
                    logger.info(f"      ↳ Duplicate: '{title}...'")

        unique_count = sum(1 for g in result_groups if len(g) == 1)
        merged_count = sum(1 for g in result_groups if len(g) > 1)
        logger.info(f"\n📊 Duplicate Detection Results:")
        logger.info(f"   Unique articles: {unique_count}")
        logger.info(f"   Merged groups: {merged_count}")
        logger.info(f"   Total articles after merging: {len(result_groups)}\n")

        return result_groups

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

            relevant = classification.get('relevant', False)
            tier = classification.get('tier')
            confidence = classification.get('confidence', 0)
            category = classification.get('category', 'unknown')

            if not relevant:
                results['rejected'].append(classification)
            elif tier == 1 and confidence >= 0.7:
                results['tier1'].append(classification)
                logger.info(f"      ✅ Tier 1: {category} ({confidence:.2f})")
            elif tier == 2 and confidence >= 0.6:
                results['tier2'].append(classification)
                logger.info(f"      ⚠️  Tier 2: {category} ({confidence:.2f})")
            else:
                results['rejected'].append(classification)
                logger.info(f"      ❌ Rejected ({confidence:.2f})")
        
        logger.info(f"\n📊 Classification Results:")
        logger.info(f"   ✅ Tier 1 (auto-process): {len(results['tier1'])}")
        logger.info(f"   ⚠️  Tier 2 (review): {len(results['tier2'])}")
        logger.info(f"   ❌ Rejected: {len(results['rejected'])}\n")
        
        return results
