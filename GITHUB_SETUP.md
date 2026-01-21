# GitHub Repository Setup Instructions

## Step 1: Create New Repository on GitHub

1. Go to https://github.com/new
2. Fill in the details:
   - **Repository name:** `jav-video-scraper-integrated` (or your preferred name)
   - **Description:** `Automated JAV video scraper with JAVDatabase integration and StreamWish upload`
   - **Visibility:** Private (recommended) or Public
   - **DO NOT** initialize with README, .gitignore, or license (we already have these)
3. Click "Create repository"

## Step 2: Push to GitHub

After creating the repository, run these commands:

```bash
# Add the remote repository
git remote add origin https://github.com/YOUR_USERNAME/jav-video-scraper-integrated.git

# Rename branch to main (if needed)
git branch -M main

# Push to GitHub
git push -u origin main
```

Replace `YOUR_USERNAME` with your GitHub username.

## Step 3: Configure GitHub Secrets

1. Go to your repository on GitHub
2. Click **Settings** → **Secrets and variables** → **Actions**
3. Click **New repository secret**
4. Add these secrets:

   **Secret 1:**
   - Name: `STREAMWISH_API_KEY`
   - Value: Your StreamWish API key

   **Secret 2:**
   - Name: `LULUSTREAM_API_KEY`
   - Value: Your LuluStream API key

## Step 4: Enable GitHub Actions

1. Go to **Actions** tab in your repository
2. If prompted, click **I understand my workflows, go ahead and enable them**
3. The workflow will run automatically every 6 hours

## Step 5: Manual Workflow Run (Optional)

To test immediately:
1. Go to **Actions** tab
2. Click on **Integrated Jable + JAVDatabase Scraper 24/7**
3. Click **Run workflow** → **Run workflow**
4. Select action: `scrape`
5. Click **Run workflow**

## Repository Structure

```
jav-video-scraper-integrated/
├── README.md                       # Main documentation
├── LICENSE                         # MIT License
├── .gitignore                      # Git ignore rules
├── GITHUB_SETUP.md                 # This file
│
├── jable/                          # Main scraper
│   ├── run_continuous.py           # Main workflow
│   ├── jable_scraper.py            # Jable scraper
│   ├── javdb_integration.py        # JAVDatabase integration
│   ├── upload_all_hosts.py         # Upload manager
│   ├── streamwish_folders.py       # Folder management
│   └── requirements.txt            # Python dependencies
│
├── javdatabase/                    # Metadata scraper
│   ├── integrated_pipeline.py      # Orchestrator
│   ├── scrape_single.py            # Single video scraper
│   ├── merge_single.py             # Data merger
│   ├── scrape_clean.py             # Clean scraper
│   └── requirements.txt            # Python dependencies
│
└── .github/workflows/
    └── integrated_scraper.yml      # GitHub Actions workflow
```

## Monitoring

### View Workflow Runs
- Go to **Actions** tab
- Click on a workflow run to see details
- Check logs for each step

### Check Databases
- `jable/database/videos_complete.json` - Jable data
- `database/combined_videos.json` - Merged data
- `javdatabase/database/stats.json` - Statistics

### View Statistics
The workflow displays statistics in the GitHub Actions summary:
- Total videos processed
- JAVDatabase coverage
- Success rates

## Troubleshooting

### Workflow Not Running
1. Check if GitHub Actions is enabled
2. Verify secrets are set correctly
3. Check workflow file syntax

### Upload Failures
1. Verify API keys are correct
2. Check rate limits
3. Review error logs in Actions

### JAVDatabase Enrichment Failing
- Check if video exists on JAVDatabase
- Verify network connectivity
- Review error logs

## Local Development

### Setup
```bash
# Clone repository
git clone https://github.com/YOUR_USERNAME/jav-video-scraper-integrated.git
cd jav-video-scraper-integrated

# Install dependencies
cd jable
pip install -r requirements.txt

cd ../javdatabase
pip install -r requirements.txt

# Create .env file
cd ../jable
cp .env.example .env
# Edit .env and add your API keys
```

### Run Locally
```bash
cd jable
python run_continuous.py
```

### Run Tests
```bash
# Integration tests
python javdatabase/test_integration.py

# Change verification
python test_changes.py
```

## Security Notes

1. **Never commit API keys** - Always use GitHub Secrets
2. **Keep repository private** if it contains sensitive data
3. **Review logs** before making repository public
4. **Rotate API keys** periodically

## Support

For issues:
1. Check existing issues in the repository
2. Review documentation
3. Create a new issue with:
   - Clear description
   - Steps to reproduce
   - Error logs
   - Environment details

---

**Ready to push!** Follow Step 1 and Step 2 above to create and push to GitHub.
