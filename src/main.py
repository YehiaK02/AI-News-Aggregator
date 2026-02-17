"""
Main Orchestrator
Coordinates the entire article discovery and processing workflow
"""

import os
import sys
import logging
from datetime import datetime
from typing import Dict, List

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
            
            logger.info("✅ All components initialized successfully\n")
            
        except Exception as e:
            logger.error(f"❌ Initialization failed: {e}")
            raise
    
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
            
            # Step 3: Process Tier 1 articles
            processed_count = self._process_tier1(classified['tier1'])
            
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
    
    def _process_tier1(self, tier1_articles: List[Dict]) -> int:
        """Step 3: Process Tier 1 articles (auto-process)"""
        logger.info("=" * 70)
        logger.info("STEP 3: PROCESSING TIER 1 ARTICLES")
        logger.info("=" * 70)
        
        if not tier1_articles:
            logger.info("ℹ️  No Tier 1 articles to process\n")
            return 0
        
        logger.info(f"📝 Processing {len(tier1_articles)} articles...\n")
        
        processed_count = 0
        
        for i, item in enumerate(tier1_articles, 1):
            article = item['article']
            category = item['category']
            confidence = item['confidence']
            
            logger.info(f"[{i}/{len(tier1_articles)}] {article['title'][:60]}...")
            logger.info(f"   Category: {category} | Confidence: {confidence:.2f}")
            
            try:
                # Fetch full article
                logger.info(f"   📥 Fetching full content...")
                full_article = self.fetcher.fetch(article['url'])
                
                # Research related sources
                logger.info(f"   🔍 Researching related sources...")
                sources = self.researcher.research_article(article, max_results=10)
                logger.info(f"   Found {len(sources)} related sources")
                
                # Generate summary
                logger.info(f"   📝 Generating summary...")
                summary = self.summarizer.summarize(full_article, sources)
                
                # Format for sheets
                sheet_data = self.summarizer.format_for_sheets(summary, category)
                sheet_data['confidence'] = confidence
                sheet_data['source'] = article.get('source_name', '')
                
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
