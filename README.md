# AI News Aggregator

Automatically discovers, classifies, and summarizes AI news from your favorite sources using AI.

**Cost:** $0/month (100% free tier services)  
**Time saved:** ~10 hours/week  
**Processing:** Runs daily at 8 AM Cairo time automatically

---

## 🎯 What It Does

Every day at 8 AM Cairo time, this system:

1. **Discovers** new articles from 3 AI news websites (via RSS feeds)
2. **Classifies** them using AI to filter only relevant articles
3. **Researches** related sources for context
4. **Summarizes** each article comprehensively
5. **Organizes** everything in a Google Sheet by category

You wake up to 5-10 perfectly summarized, categorized AI news articles.

---

## 📊 Output

Your Google Sheet will have 3 tabs:

- **Processed Articles**: 5-10 high-quality summaries daily
- **Review Queue**: Articles that need human judgment
- **Rejected Log**: Filtered-out articles (for audit)

---

## 🛠️ Tech Stack

All services are **100% free**:

- **GitHub Actions**: Runs the workflow (unlimited for public repos)
- **Groq API**: AI classification & summarization (14,400 requests/day free)
- **Tavily API**: Web research (1,000 searches/month free)
- **Jina Reader**: Article fetching (unlimited free)
- **Google Sheets**: Storage (unlimited free)

---

## 🚀 Quick Start

### Prerequisites

- GitHub account
- Google account
- 30 minutes for setup

### Setup Steps

1. **Fork this repository** (or create a new one)

2. **Get API Keys** (all free):
   - Groq: https://console.groq.com
   - Tavily: https://tavily.com
   - Google Sheets: See SETUP_GUIDE.md

3. **Add GitHub Secrets**:
   
   Go to: Settings → Secrets and variables → Actions → New repository secret
   
   Add these 4 secrets:
   - `GROQ_API_KEY`
   - `TAVILY_API_KEY`
   - `GOOGLE_SHEETS_CREDENTIALS` (full JSON content)
   - `GOOGLE_SHEET_ID`

4. **Create Google Sheet** with 3 tabs:
   - Processed Articles
   - Review Queue
   - Rejected Log

5. **Test manually**:
   - Go to Actions tab
   - Click "Daily AI News Discovery"
   - Click "Run workflow"

6. **It runs automatically** every day at 8 AM Cairo time!

---

## 📁 Project Structure

```
ai-news-aggregator/
├── .github/workflows/       # GitHub Actions automation
├── config/                  # Configuration files
│   ├── categories.yaml      # Your category definitions
│   ├── classification_prompt.txt
│   ├── system_prompt.txt
│   └── sources.yaml         # RSS feed URLs
├── src/                     # Python source code
│   ├── main.py              # Main orchestrator
│   ├── feed_discovery.py    # RSS fetcher
│   ├── article_classifier.py
│   ├── article_fetcher.py
│   ├── research_agent.py
│   ├── summarizer.py
│   ├── sheets_client.py
│   └── utils.py
├── requirements.txt
└── README.md
```

---

## ⚙️ Customization

### Change Schedule

Edit `.github/workflows/daily-discovery.yml`:

```yaml
schedule:
  - cron: '0 6 * * *'  # 8 AM Cairo
```

Examples:
- `'0 6,18 * * *'` - Twice daily (8 AM & 8 PM)
- `'0 */6 * * *'` - Every 6 hours

### Add News Sources

Edit `config/sources.yaml`:

```yaml
new_source:
  name: "New Source Name"
  url: "https://newssite.com/feed/"
  enabled: true
  priority: high
```

### Adjust Categories

Edit `config/categories.yaml` to add/modify categories and keywords.

### Change Confidence Thresholds

In `config/categories.yaml`:

```yaml
scoring:
  tier_1_threshold: 0.7  # Change to 0.8 for stricter filtering
  tier_2_threshold: 0.6
```

---

## 🔍 How It Works

### Discovery (RSS Feeds)
- Connects to 3 news sites
- Fetches last 24 hours of articles
- ~50 articles discovered daily

### Classification (Groq AI)
- AI reads title + summary
- Matches against your category definitions
- Scores confidence (0-100%)
- Filters to ~8-10 relevant articles

### Processing (For Each Relevant Article)
1. Fetch full content (Jina Reader)
2. Research 10 related sources (Tavily)
3. Synthesize comprehensive summary (Groq)
4. Save to Google Sheets

### Total Time: ~10 minutes per day

---

## 💰 Cost Breakdown

| Service | Usage | Free Tier | Cost |
|---------|-------|-----------|------|
| GitHub Actions | 10 min/day | Unlimited (public) | $0 |
| Groq | 60 req/day | 14,400/day | $0 |
| Tavily | 10 searches/day | 1,000/month | $0 |
| Jina Reader | 10 req/day | Unlimited | $0 |
| Google Sheets | 10 writes/day | Unlimited | $0 |
| **TOTAL** | | | **$0/month** |

---

## 🐛 Troubleshooting

### Workflow fails

1. Check GitHub Actions logs
2. Verify all secrets are set correctly
3. Test API keys manually

### No articles found

1. Check RSS feed URLs in `config/sources.yaml`
2. Verify feeds are accessible
3. Check timeframe setting

### Articles miscategorized

1. Review `config/categories.yaml`
2. Adjust keywords and thresholds
3. Check classification prompt

### Google Sheets errors

1. Verify service account has edit access to sheet
2. Check sheet ID is correct
3. Ensure sheet tabs exist

---

## 📖 Full Documentation

See `SETUP_GUIDE.md` for detailed step-by-step setup instructions.

---

## 🤝 Contributing

This is a personal project, but feel free to fork and customize for your needs!

---

## 📄 License

MIT License - Use freely!

---

## 🙏 Acknowledgments

Built using:
- [Groq](https://groq.com) - Fast AI inference
- [Tavily](https://tavily.com) - AI search API
- [Jina Reader](https://jina.ai) - Clean article extraction
- [Google Sheets API](https://developers.google.com/sheets)

---

## 📧 Questions?

Open an issue or check the setup guide for detailed instructions.

**Happy news aggregating!** 🎉
