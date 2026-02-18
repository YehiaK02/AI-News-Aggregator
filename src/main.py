"""
Main Orchestrator
Coordinates the entire article discovery and processing workflow
"""

import os
import sys
import logging
import yaml
from datetime import datetime
from typing import Dict, List
from pathlib import Path

from feed_discovery import FeedDiscoverer
from article_classifier import ArticleClassifier
from article_fetcher import ArticleFetcher
from research_agent import ResearchAgent
from summarizer import Summarizer
from sheets_client import SheetsClient

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)


class ArticleProcessor:
    """Main workflow orchestrator"""
    
    def __init__(self):
        """Initialize all components"""
        logger.info("🚀 Initializing AI News Aggregator...\n")
        
        try:
            # Initialize components
            self.discoverer = FeedDiscoverer()
            self.classifier = ArticleClassifier()
            self.fetcher = ArticleFetcher()
            self.researcher = ResearchAgent()
            self.summarizer = Summarizer()
            self.sheets = SheetsClient()

            # Load duplicate detection config
            self._load_dedup_config()

            logger.info("✅ All components initialized successfully\n")
            
        except Exception as e:
            logger.error(f"❌ Initialization failed: {e}")
            raise
    
    def _load_dedup_config(self):
        """Load duplicate detection settings from sources.yaml"""
        try:
            with open("../config/sources.yaml", 'r') as f:
                config = yaml.safe_load(f)
            self.source_priority = config.get('source_priority', {})
            dedup = config.get('duplicate_detection', {})
            self.dedup_enabled = dedup.get('enabled', False)
            self.dedup_threshold = dedup.get('confidence_threshold', 0.8)
        except Exception as e:
            logger.warning(f"Could not load dedup config, disabling: {e}")
            self.source_priority = {}
            self.dedup_enabled = False
            self.dedup_threshold = 0.8

    def run(self):
        """Execute the complete workflow"""
        start_time = datetime.now()

        logger.info("=" * 70)
        logger.info("AI NEWS AGGREGATOR - DAILY WORKFLOW")
        logger.info("=" * 70)
        logger.info(f"Started at: {start_time.strftime('%Y-%m-%d %H:%M:%S')}\n")

        try:
            # Step 1: Discovery
            articles = self._discover_articles()

            if not articles:
                logger.warning("⚠️  No articles found. Exiting.")
                return

            # Step 2: Classification
            classified = self._classify_articles(articles)

            # Step 2.5: Duplicate detection & merging
            article_groups = self._detect_duplicates(classified['tier1'])

            # Step 3: Process article groups (with merged duplicates)
            processed_count = self._process_tier1(article_groups)

            # Step 4: Save Tier 2 for review
            self._save_tier2(classified['tier2'])

            # Step 5: Log rejected articles
            self._log_rejected(classified['rejected'])

            # Summary
            self._print_summary(start_time, classified, processed_count)

        except Exception as e:
            logger.error(f"❌ Workflow failed: {e}")
            raise
    
    def _discover_articles(self) -> List[Dict]:
        """Step 1: Discover articles from RSS feeds"""
        logger.info("=" * 70)
        logger.info("STEP 1: ARTICLE DISCOVERY")
        logger.info("=" * 70)
        
        # Get source stats
        stats = self.discoverer.get_source_stats()
        logger.info(f"📡 Configured sources: {stats['total_sources']}")
        logger.info(f"✅ Enabled: {stats['enabled_sources']}")
        
        for source_id, source_name in stats['sources'].items():
            logger.info(f"   - {source_name} ({source_id})")
        
        logger.info("")
        
        # Fetch articles
        articles = self.discoverer.fetch_recent_articles()
        
        logger.info("")
        return articles
    
    def _classify_articles(self, articles: List[Dict]) -> Dict:
        """Step 2: Classify articles with AI"""
        logger.info("=" * 70)
        logger.info("STEP 2: AI CLASSIFICATION")
        logger.info("=" * 70)
        
        classified = self.classifier.classify_batch(articles)
        
        return classified
    
    def _detect_duplicates(self, tier1_articles: List[Dict]) -> List[List[Dict]]:
        """Step 2.5: Detect and group duplicate articles"""
        if not self.dedup_enabled or not tier1_articles:
            # Return each article as its own group
            return [[item] for item in tier1_articles]

        logger.info("=" * 70)
        logger.info("STEP 2.5: DUPLICATE DETECTION")
        logger.info("=" * 70)

        groups = self.classifier.detect_duplicates(
            tier1_articles,
            self.source_priority,
            self.dedup_threshold
        )

        return groups

    def _process_tier1(self, article_groups: List[List[Dict]]) -> int:
        """Step 3: Process Tier 1 article groups (with merged duplicates)"""
        logger.info("=" * 70)
        logger.info("STEP 3: PROCESSING TIER 1 ARTICLES")
        logger.info("=" * 70)

        if not article_groups:
            logger.info("ℹ️  No Tier 1 articles to process\n")
            return 0

        logger.info(f"📝 Processing {len(article_groups)} article groups...\n")

        processed_count = 0

        for i, group in enumerate(article_groups, 1):
            primary_item = group[0]
            article = primary_item['article']
            category = primary_item['category']
            confidence = primary_item['confidence']
            duplicate_count = len(group)

            if duplicate_count > 1:
                logger.info(
                    f"[{i}/{len(article_groups)}] {article['title'][:60]}... "
                    f"(merged {duplicate_count} articles)"
                )
            else:
                logger.info(f"[{i}/{len(article_groups)}] {article['title'][:60]}...")
            logger.info(f"   Category: {category} | Confidence: {confidence:.2f}")

            try:
                # Fetch full article
                logger.info(f"   📥 Fetching full content...")
                full_article = self.fetcher.fetch(article['url'])

                # Collect duplicate URLs as additional sources
                duplicate_sources = []
                for dup_item in group[1:]:
                    dup_article = dup_item['article']
                    duplicate_sources.append({
                        'url': dup_article.get('url', ''),
                        'title': dup_article.get('title', ''),
                        'content': dup_article.get('summary', ''),
                    })

                # Research related sources
                logger.info(f"   🔍 Researching related sources...")
                research_sources = self.researcher.research_article(
                    article, max_results=10
                )
                logger.info(f"   Found {len(research_sources)} related sources")

                # Merge: duplicate URLs first, then research sources
                all_sources = duplicate_sources + research_sources
                if duplicate_sources:
                    logger.info(
                        f"   🔗 Merged {len(duplicate_sources)} duplicate article(s) "
                        f"as additional sources"
                    )

                # Generate summary
                logger.info(f"   📝 Generating summary...")
                summary = self.summarizer.summarize(full_article, all_sources)

                # Format for sheets
                sheet_data = self.summarizer.format_for_sheets(summary, category)
                sheet_data['confidence'] = confidence
                sheet_data['source'] = article.get('source_name', '')
                sheet_data['duplicate_count'] = duplicate_count

                # Save to Google Sheets
                logger.info(f"   💾 Saving to Google Sheets...")
                success = self.sheets.append_row(sheet_data)

                if success:
                    logger.info(f"   ✅ Successfully processed\n")
                    processed_count += 1
                else:
                    logger.error(f"   ❌ Failed to save to Sheets\n")

            except Exception as e:
                logger.error(f"   ❌ Error processing article: {e}\n")
                continue

        return processed_count
    
    def _save_tier2(self, tier2_articles: List[Dict]):
        """Step 4: Save Tier 2 articles for review"""
        if not tier2_articles:
            return
        
        logger.info("=" * 70)
        logger.info("STEP 4: SAVING TIER 2 FOR REVIEW")
        logger.info("=" * 70)
        
        logger.info(f"💾 Saving {len(tier2_articles)} articles to review queue...")
        
        success = self.sheets.save_to_review_tab(tier2_articles)
        
        if success:
            logger.info(f"✅ Review queue updated\n")
        else:
            logger.error(f"❌ Failed to update review queue\n")
    
    def _log_rejected(self, rejected_articles: List[Dict]):
        """Step 5: Log rejected articles"""
        if not rejected_articles:
            return
        
        logger.info("=" * 70)
        logger.info("STEP 5: LOGGING REJECTED ARTICLES")
        logger.info("=" * 70)
        
        logger.info(f"📋 Logging {len(rejected_articles)} rejected articles...")
        
        success = self.sheets.save_rejected_log(rejected_articles)
        
        if success:
            logger.info(f"✅ Rejected log updated\n")
        else:
            logger.error(f"❌ Failed to update rejected log\n")
    
    def _print_summary(
        self,
        start_time: datetime,
        classified: Dict,
        processed_count: int
    ):
        """Print final summary"""
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        logger.info("=" * 70)
        logger.info("WORKFLOW COMPLETE")
        logger.info("=" * 70)
        
        logger.info(f"\n📊 Final Results:")
        logger.info(f"   ✅ Processed: {processed_count} articles")
        logger.info(f"   ⚠️  For review: {len(classified['tier2'])} articles")
        logger.info(f"   ❌ Filtered out: {len(classified['rejected'])} articles")
        
        logger.info(f"\n⏱️  Execution Time: {duration:.1f} seconds")
        logger.info(f"💰 Total Cost: $0 (all free tier)\n")
        
        logger.info("=" * 70)
        logger.info("Check your Google Sheet for results!")
        logger.info("=" * 70)


def main():
    """Main entry point"""
    try:
        processor = ArticleProcessor()
        processor.run()
        
    except KeyboardInterrupt:
        logger.info("\n\n⚠️  Workflow interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"\n\n❌ Fatal error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
