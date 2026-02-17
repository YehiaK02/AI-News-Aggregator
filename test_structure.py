"""
Test Script for AI News Aggregator
Tests all imports, dependencies, and basic structure
"""

import sys
import os
from pathlib import Path

# Add src directory to path (for running from project root)
sys.path.insert(0, str(Path(__file__).parent / 'src'))

# Set UTF-8 encoding for Windows
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

def test_imports():
    """Test all module imports"""
    print("=" * 70)
    print("TEST 1: Module Imports")
    print("=" * 70)

    tests = []

    # Test core modules
    try:
        from feed_discovery import FeedDiscoverer
        print("[PASS] feed_discovery.FeedDiscoverer")
        tests.append(True)
    except Exception as e:
        print(f"[FAIL] feed_discovery.FeedDiscoverer: {e}")
        tests.append(False)

    try:
        from article_classifier import ArticleClassifier
        print("[PASS] article_classifier.ArticleClassifier")
        tests.append(True)
    except Exception as e:
        print(f"[FAIL] article_classifier.ArticleClassifier: {e}")
        tests.append(False)

    try:
        from article_fetcher import ArticleFetcher
        print("[PASS] article_fetcher.ArticleFetcher")
        tests.append(True)
    except Exception as e:
        print(f"[FAIL] article_fetcher.ArticleFetcher: {e}")
        tests.append(False)

    try:
        from research_agent import ResearchAgent
        print("[PASS] research_agent.ResearchAgent")
        tests.append(True)
    except Exception as e:
        print(f"[FAIL] research_agent.ResearchAgent: {e}")
        tests.append(False)

    try:
        from summarizer import Summarizer
        print("[PASS] summarizer.Summarizer")
        tests.append(True)
    except Exception as e:
        print(f"[FAIL] summarizer.Summarizer: {e}")
        tests.append(False)

    try:
        from sheets_client import SheetsClient
        print("[PASS] sheets_client.SheetsClient")
        tests.append(True)
    except Exception as e:
        print(f"[FAIL] sheets_client.SheetsClient: {e}")
        tests.append(False)

    try:
        import utils
        print("[PASS] utils module")
        tests.append(True)
    except Exception as e:
        print(f"[FAIL] utils module: {e}")
        tests.append(False)

    print()
    return all(tests)


def test_dependencies():
    """Test all package dependencies"""
    print("=" * 70)
    print("TEST 2: Package Dependencies")
    print("=" * 70)

    dependencies = [
        'feedparser',
        'requests',
        'dateutil',
        'groq',
        'tavily',
        'google.auth',
        'googleapiclient',
        'yaml'
    ]

    tests = []
    for dep in dependencies:
        try:
            __import__(dep)
            print(f"[PASS] {dep}")
            tests.append(True)
        except ImportError as e:
            print(f"[FAIL] {dep}: Not installed")
            tests.append(False)

    print()
    return all(tests)


def test_config_files():
    """Test configuration files exist"""
    print("=" * 70)
    print("TEST 3: Configuration Files")
    print("=" * 70)

    config_files = [
        'config/sources.yaml',
        'config/categories.yaml',
        'config/classification_prompt.txt',
        'config/system_prompt.txt'
    ]

    tests = []
    for config_file in config_files:
        path = Path(__file__).parent / config_file
        if path.exists():
            print(f"[PASS] {config_file}")
            tests.append(True)
        else:
            print(f"[FAIL] {config_file}: Not found")
            tests.append(False)

    print()
    return all(tests)


def test_initialization():
    """Test that classes can be initialized (without API keys)"""
    print("=" * 70)
    print("TEST 4: Class Initialization (Mock)")
    print("=" * 70)

    tests = []

    # Test FeedDiscoverer (doesn't require API key)
    try:
        from feed_discovery import FeedDiscoverer
        discoverer = FeedDiscoverer()
        stats = discoverer.get_source_stats()
        print(f"[PASS] FeedDiscoverer initialized")
        print(f"       Found {stats['total_sources']} configured sources")
        tests.append(True)
    except Exception as e:
        print(f"[FAIL] FeedDiscoverer: {e}")
        tests.append(False)

    # Test ArticleFetcher (doesn't require API key)
    try:
        from article_fetcher import ArticleFetcher
        fetcher = ArticleFetcher()
        print(f"[PASS] ArticleFetcher initialized")
        print(f"       Jina base URL: {fetcher.jina_base_url}")
        tests.append(True)
    except Exception as e:
        print(f"[FAIL] ArticleFetcher: {e}")
        tests.append(False)

    # Test utils functions
    try:
        from utils import clean_text, validate_url, extract_date_from_text

        # Test clean_text
        result = clean_text("  Test   text  ")
        assert result == "Test text"

        # Test validate_url
        assert validate_url("https://example.com") == True
        assert validate_url("not a url") == False

        print(f"[PASS] Utils functions working")
        tests.append(True)
    except Exception as e:
        print(f"[FAIL] Utils functions: {e}")
        tests.append(False)

    # Test classes that require API keys (just check they error properly)
    try:
        from article_classifier import ArticleClassifier
        from research_agent import ResearchAgent
        from summarizer import Summarizer
        from sheets_client import SheetsClient

        print(f"[PASS] API-dependent classes can be imported")
        print(f"       (ArticleClassifier, ResearchAgent, Summarizer, SheetsClient)")
        print(f"       Note: These require API keys to initialize")
        tests.append(True)
    except Exception as e:
        print(f"[FAIL] API-dependent classes: {e}")
        tests.append(False)

    print()
    return all(tests)


def test_workflow_structure():
    """Test the main workflow structure"""
    print("=" * 70)
    print("TEST 5: Workflow Structure")
    print("=" * 70)

    try:
        # Import main to check structure
        sys.path.insert(0, str(Path(__file__).parent / 'src'))

        # Read main.py and check key components
        main_path = Path(__file__).parent / 'src' / 'main.py'
        with open(main_path, 'r') as f:
            main_content = f.read()

        # Check for key classes and methods
        checks = [
            ('ArticleProcessor class', 'class ArticleProcessor'),
            ('__init__ method', 'def __init__(self)'),
            ('run method', 'def run(self)'),
            ('_discover_articles', 'def _discover_articles'),
            ('_classify_articles', 'def _classify_articles'),
            ('_process_tier1', 'def _process_tier1'),
            ('_save_tier2', 'def _save_tier2'),
            ('_log_rejected', 'def _log_rejected'),
            ('main function', 'def main()'),
        ]

        all_found = True
        for name, pattern in checks:
            if pattern in main_content:
                print(f"[PASS] {name}")
            else:
                print(f"[FAIL] {name}")
                all_found = False

        print()
        return all_found

    except Exception as e:
        print(f"[FAIL] Error reading main.py: {e}")
        print()
        return False


def test_github_workflow():
    """Test GitHub Actions workflow exists"""
    print("=" * 70)
    print("TEST 6: GitHub Actions Workflow")
    print("=" * 70)

    workflow_path = Path(__file__).parent / '.github' / 'workflows' / 'daily-discovery.yml'

    if workflow_path.exists():
        with open(workflow_path, 'r') as f:
            content = f.read()

        checks = [
            ('Schedule defined', 'schedule:'),
            ('Manual trigger', 'workflow_dispatch'),
            ('Python setup', 'setup-python'),
            ('Install dependencies', 'pip install'),
            ('Run main.py', 'python main.py'),
            ('Environment variables', 'GROQ_API_KEY'),
        ]

        all_found = True
        for name, pattern in checks:
            if pattern in content:
                print(f"[PASS] {name}")
            else:
                print(f"[FAIL] {name}")
                all_found = False

        print()
        return all_found
    else:
        print("[FAIL] Workflow file not found")
        print()
        return False


def main():
    """Run all tests"""
    print("\n")
    print("=" * 70)
    print(" " * 15 + "AI NEWS AGGREGATOR - STRUCTURE TEST")
    print("=" * 70)
    print()

    results = []

    results.append(("Module Imports", test_imports()))
    results.append(("Package Dependencies", test_dependencies()))
    results.append(("Configuration Files", test_config_files()))
    results.append(("Class Initialization", test_initialization()))
    results.append(("Workflow Structure", test_workflow_structure()))
    results.append(("GitHub Workflow", test_github_workflow()))

    # Print summary
    print("=" * 70)
    print("SUMMARY")
    print("=" * 70)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for name, result in results:
        status = "[PASS]" if result else "[FAIL]"
        print(f"{status} - {name}")

    print()
    print(f"Total: {passed}/{total} tests passed")

    if passed == total:
        print()
        print("SUCCESS: All tests passed! Your project structure is correct.")
        print()
        print("Next steps:")
        print("1. Install dependencies: pip install -r requirements.txt")
        print("2. Set up API keys (GROQ_API_KEY, TAVILY_API_KEY)")
        print("3. Set up Google Sheets credentials")
        print("4. Add GitHub secrets")
        print("5. Run: cd src && python main.py")
        return 0
    else:
        print()
        print("WARNING: Some tests failed. Please review the errors above.")
        print()
        print("To install dependencies, run: pip install -r requirements.txt")
        return 1


if __name__ == "__main__":
    sys.exit(main())
