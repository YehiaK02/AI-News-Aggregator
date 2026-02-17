# Complete Setup Guide - AI News Aggregator

This guide walks you through the complete setup process step by step.

**Time required:** 30-45 minutes (one-time setup)

---

## 📋 Setup Checklist

- [ ] GitHub account created
- [ ] Google Cloud project created
- [ ] Google Sheets credentials obtained
- [ ] Groq API key obtained
- [ ] Tavily API key obtained
- [ ] Google Sheet created and configured
- [ ] GitHub repository created
- [ ] Secrets added to GitHub
- [ ] Test run successful
- [ ] Daily automation verified

---

## Step 1: Get Groq API Key (5 minutes)

**What:** Groq provides free AI inference for classification and summarization

**How:**

1. Go to https://console.groq.com
2. Sign up with email or Google account
3. Click "API Keys" in the left sidebar
4. Click "Create API Key"
5. Name it "AI News Aggregator"
6. Copy the key (starts with `gsk_...`)
7. **Save it** - you'll need it later

**Free Tier:**
- 14,400 requests per day
- No credit card required
- You'll use ~60 requests/day

---

## Step 2: Get Tavily API Key (5 minutes)

**What:** Tavily provides AI-powered web search for finding related sources

**How:**

1. Go to https://tavily.com
2. Sign up with email
3. Verify your email
4. Go to dashboard
5. Copy your API key
6. **Save it** - you'll need it later

**Free Tier:**
- 1,000 searches per month
- No credit card required
- You'll use ~300 searches/month

---

## Step 3: Set Up Google Sheets API (15 minutes)

**What:** Allows the script to write to your Google Sheet

### 3.1: Create Google Cloud Project

1. Go to https://console.cloud.google.com
2. Click "Select a project" → "New Project"
3. Name: "AI News Aggregator"
4. Click "Create"
5. Wait for project to be created (~30 seconds)

### 3.2: Enable Google Sheets API

1. In your project, click "APIs & Services" → "Enable APIs and Services"
2. Search for "Google Sheets API"
3. Click "Google Sheets API"
4. Click "Enable"
5. Wait for it to enable

### 3.3: Create Service Account

1. Go to "APIs & Services" → "Credentials"
2. Click "Create Credentials" → "Service Account"
3. Fill in:
   - Name: `ai-news-aggregator`
   - ID: (auto-generated)
   - Description: "Service account for AI News Aggregator"
4. Click "Create and Continue"
5. Skip optional steps (click "Continue" then "Done")

### 3.4: Create Service Account Key

1. Click on the service account you just created
2. Go to "Keys" tab
3. Click "Add Key" → "Create new key"
4. Choose "JSON"
5. Click "Create"
6. A JSON file will download - **SAVE THIS FILE**
7. Open the file in a text editor
8. Copy the **entire contents** - you'll need this as `GOOGLE_SHEETS_CREDENTIALS`

### 3.5: Get Service Account Email

1. In the JSON file, find the `client_email` field
2. Copy the email (looks like `ai-news-aggregator@project-id.iam.gserviceaccount.com`)
3. **Save this email** - you'll need it to share your Google Sheet

---

## Step 4: Create Google Sheet (5 minutes)

### 4.1: Create the Sheet

1. Go to https://sheets.google.com
2. Click "Blank" to create new sheet
3. Name it "AI News Aggregator" (top-left)

### 4.2: Create Tabs

Create 3 tabs (bottom of screen):

**Tab 1: Processed Articles**
- Rename "Sheet1" to "Processed Articles"
- Add headers in row 1:
  - A1: Date
  - B1: Source
  - C1: Category
  - D1: Title
  - E1: Summary
  - F1: Sources
  - G1: Source Count
  - H1: Confidence
  - I1: Processed At

**Tab 2: Review Queue**
- Click "+" to add new tab
- Name it "Review Queue"
- Add headers in row 1:
  - A1: Date
  - B1: Source
  - C1: Category
  - D1: Title
  - E1: Summary
  - F1: Confidence
  - G1: Reason
  - H1: URL

**Tab 3: Rejected Log**
- Click "+" to add new tab
- Name it "Rejected Log"
- Add headers in row 1:
  - A1: Date
  - B1: Source
  - C1: Title
  - D1: Rejection Reason
  - E1: URL

### 4.3: Share with Service Account

1. Click "Share" button (top-right)
2. Paste the service account email from Step 3.5
3. Give it "Editor" permissions
4. **Uncheck** "Notify people"
5. Click "Share"

### 4.4: Get Sheet ID

1. Look at the URL of your sheet
2. It looks like: `https://docs.google.com/spreadsheets/d/SHEET_ID_HERE/edit`
3. Copy the `SHEET_ID_HERE` part
4. **Save it** - you'll need this as `GOOGLE_SHEET_ID`

---

## Step 5: Set Up GitHub Repository (10 minutes)

### 5.1: Create Repository

**Option A: Fork This Repo (Easiest)**
1. Click "Fork" button (top-right of this page)
2. Choose your account
3. Click "Create fork"

**Option B: Create New Repo**
1. Go to https://github.com/new
2. Name: `ai-news-aggregator`
3. Choose "Public" (for unlimited Actions minutes)
4. Click "Create repository"
5. Upload all project files from the zip

### 5.2: Add Secrets

1. Go to your repository
2. Click "Settings" (top menu)
3. Click "Secrets and variables" → "Actions" (left sidebar)
4. Click "New repository secret"

**Add these 4 secrets:**

**Secret 1: GROQ_API_KEY**
- Name: `GROQ_API_KEY`
- Secret: Paste your Groq API key from Step 1
- Click "Add secret"

**Secret 2: TAVILY_API_KEY**
- Name: `TAVILY_API_KEY`
- Secret: Paste your Tavily API key from Step 2
- Click "Add secret"

**Secret 3: GOOGLE_SHEETS_CREDENTIALS**
- Name: `GOOGLE_SHEETS_CREDENTIALS`
- Secret: Paste the **entire JSON content** from Step 3.4
- Click "Add secret"

**Secret 4: GOOGLE_SHEET_ID**
- Name: `GOOGLE_SHEET_ID`
- Secret: Paste your Sheet ID from Step 4.4
- Click "Add secret"

---

## Step 6: Test the Workflow (5 minutes)

### 6.1: Manual Test Run

1. Go to "Actions" tab in your repository
2. Click "Daily AI News Discovery" (left sidebar)
3. Click "Run workflow" button (right side)
4. Click the green "Run workflow" button
5. Wait ~10 minutes for it to complete

### 6.2: Check Results

1. Click on the workflow run
2. Expand "Run article discovery workflow"
3. Check the logs - should see:
   - Articles discovered
   - Articles classified
   - Articles processed
   - "WORKFLOW COMPLETE"

4. Open your Google Sheet
5. Should see processed articles in "Processed Articles" tab

### 6.3: Troubleshooting

**If workflow fails:**

**Error: "GROQ_API_KEY not found"**
- Check secret name is exactly `GROQ_API_KEY`
- Verify you pasted the key correctly

**Error: "Invalid credentials JSON"**
- Re-copy the entire JSON file content
- Make sure you copied everything including `{` and `}`

**Error: "Permission denied" (Google Sheets)**
- Verify service account email has Editor access
- Check Sheet ID is correct
- Make sure all 3 tabs exist

**Error: "No articles found"**
- Check RSS feed URLs in `config/sources.yaml`
- Try running at a different time (more articles in morning)

---

## Step 7: Verify Daily Automation (Next Day)

1. Wait until tomorrow at 8 AM Cairo time
2. Check GitHub Actions tab - should see automatic run
3. Check Google Sheet - should see new articles

**To change schedule:**
- Edit `.github/workflows/daily-discovery.yml`
- Change cron schedule (see examples in README)

---

## 🎉 You're Done!

Your AI News Aggregator is now running automatically!

**What happens next:**
- Every day at 8 AM Cairo time, it automatically runs
- Discovers ~50 articles from 3 sources
- Filters to ~8-10 relevant articles
- Processes and summarizes them
- Saves to your Google Sheet

**You just:**
- Check your Google Sheet each morning
- Review the summaries
- Optionally check "Review Queue" tab

---

## 🔧 Customization

### Add More News Sources

1. Edit `config/sources.yaml`
2. Add new source with RSS feed URL
3. Commit changes

### Adjust Categories

1. Edit `config/categories.yaml`
2. Add keywords or change thresholds
3. Commit changes

### Change Processing Rules

1. Edit `config/classification_prompt.txt`
2. Modify instructions
3. Commit changes

---

## 💡 Tips

**Save time:**
- Star relevant GitHub notifications
- Set up Google Sheets mobile app for quick access
- Create a bookmark to your sheet

**Improve accuracy:**
- Review "Rejected Log" weekly
- Adjust categories if good articles are rejected
- Lower confidence threshold if too strict

**Scale up:**
- Add more news sources
- Run twice daily (morning and evening)
- Lower confidence threshold for more articles

---

## 📊 Expected Results

**Daily:**
- ~50 articles discovered
- ~8-10 processed and summarized
- ~3 in review queue
- ~40 rejected (filtered out)

**Weekly:**
- ~60 high-quality summaries
- ~20 for review
- ~280 filtered out

**Time saved:**
- Manual reading: ~2 hours/day
- With aggregator: ~10 minutes/day
- **Savings: ~10 hours/week**

---

## ❓ FAQ

**Q: Can I run it more than once a day?**
A: Yes! Edit the cron schedule in the workflow file.

**Q: Can I add more than 3 news sources?**
A: Yes! Add them to `config/sources.yaml`.

**Q: Will I hit the free tier limits?**
A: Very unlikely. Current usage is <1% of all free tiers.

**Q: Can I use a private repository?**
A: Yes, but you'll have 2,000 minutes/month limit (still plenty).

**Q: How do I stop it?**
A: Disable the workflow in GitHub Actions settings.

**Q: Can I customize the summary format?**
A: Yes! Edit `config/system_prompt.txt`.

---

## 🆘 Getting Help

**If you're stuck:**

1. Check the logs in GitHub Actions
2. Verify all secrets are set correctly
3. Review this guide step-by-step
4. Open an issue in the repository

---

**Setup complete! Enjoy your automated AI news aggregator!** 🎊
