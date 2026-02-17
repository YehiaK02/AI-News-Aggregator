"""
Quick verification script to test config file paths
Run this from the project root OR from the src/ directory
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

def test_config_paths():
    """Test that all config files can be found from src/ directory"""
    print("Testing config file paths from src/ directory...")
    print("=" * 70)

    # Change to src directory (simulating GitHub Actions workflow)
    import os
    original_dir = os.getcwd()

    try:
        script_dir = Path(__file__).parent
        src_dir = script_dir / 'src'
        os.chdir(src_dir)
        print(f"Working directory: {os.getcwd()}\n")

        # Test 1: FeedDiscoverer
        print("[1/3] Testing FeedDiscoverer config loading...")
        try:
            from feed_discovery import FeedDiscoverer
            discoverer = FeedDiscoverer()
            stats = discoverer.get_source_stats()
            print(f"[PASS] Loaded {stats['total_sources']} sources from sources.yaml")
        except Exception as e:
            print(f"[FAIL] FeedDiscoverer: {e}")
            return False

        # Test 2: ArticleClassifier
        print("\n[2/3] Testing ArticleClassifier config loading...")
        try:
            # We can't initialize without API key, but we can test file loading
            import yaml

            categories_path = Path("../config/categories.yaml")
            prompt_path = Path("../config/classification_prompt.txt")

            if not categories_path.exists():
                print(f"[FAIL] Categories file not found: {categories_path.absolute()}")
                return False

            if not prompt_path.exists():
                print(f"[FAIL] Classification prompt not found: {prompt_path.absolute()}")
                return False

            with open(categories_path) as f:
                categories = yaml.safe_load(f)
                print(f"[PASS] Loaded {len(categories.get('categories', {}))} categories")

            with open(prompt_path) as f:
                prompt = f.read()
                print(f"[PASS] Loaded classification prompt ({len(prompt)} chars)")
        except Exception as e:
            print(f"[FAIL] ArticleClassifier: {e}")
            return False

        # Test 3: Summarizer
        print("\n[3/3] Testing Summarizer config loading...")
        try:
            prompt_path = Path("../config/system_prompt.txt")

            if not prompt_path.exists():
                print(f"[FAIL] System prompt not found: {prompt_path.absolute()}")
                return False

            with open(prompt_path) as f:
                prompt = f.read()
                print(f"[PASS] Loaded system prompt ({len(prompt)} chars)")
        except Exception as e:
            print(f"[FAIL] Summarizer: {e}")
            return False

        print("\n" + "=" * 70)
        print("[SUCCESS] All config files load correctly from src/ directory!")
        print("=" * 70)
        return True

    finally:
        # Restore original directory
        os.chdir(original_dir)

if __name__ == "__main__":
    success = test_config_paths()
    sys.exit(0 if success else 1)
