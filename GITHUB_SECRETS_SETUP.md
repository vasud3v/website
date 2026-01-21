# GitHub Actions Secrets Setup Guide

## 🔐 Required Secrets

You need to add these secrets to your GitHub repository for the automated workflow to work.

---

## 📍 Where to Add Secrets

1. Go to your repository: https://github.com/vasud3v/main-scraper
2. Click **Settings** (top menu)
3. In the left sidebar, click **Secrets and variables** → **Actions**
4. Click **New repository secret** button

---

## 🔑 Secrets to Add

### Secret 1: STREAMWISH_API_KEY

**Name:** `STREAMWISH_API_KEY`  
**Value:** `31637q4gsnt23yyvd0or6`

**Steps:**
1. Click "New repository secret"
2. Name: `STREAMWISH_API_KEY`
3. Secret: `31637q4gsnt23yyvd0or6`
4. Click "Add secret"

---

### Secret 2: LULUSTREAM_API_KEY

**Name:** `LULUSTREAM_API_KEY`  
**Value:** `229747ohh6h2cd4t2gh3ep`

**Steps:**
1. Click "New repository secret"
2. Name: `LULUSTREAM_API_KEY`
3. Secret: `229747ohh6h2cd4t2gh3ep`
4. Click "Add secret"

---

## ✅ Verification

After adding both secrets, you should see:

```
Repository secrets (2)
├── LULUSTREAM_API_KEY     Updated X seconds ago
└── STREAMWISH_API_KEY     Updated X seconds ago
```

---

## 🚀 Enable GitHub Actions

After adding secrets:

1. Go to **Actions** tab: https://github.com/vasud3v/main-scraper/actions
2. If you see a message about workflows, click **"I understand my workflows, go ahead and enable them"**
3. The workflow will now run automatically every 6 hours

---

## 🧪 Test the Workflow (Optional)

To test immediately:

1. Go to **Actions** tab
2. Click on **"Integrated Jable + JAVDatabase Scraper 24/7"**
3. Click **"Run workflow"** button (right side)
4. Select:
   - Branch: `main`
   - Action: `scrape`
   - Max videos: (leave empty or enter a number)
5. Click **"Run workflow"**
6. Wait a few seconds and refresh - you'll see the workflow running

---

## 📊 Monitor Workflow

### View Running Workflow
1. Go to Actions tab
2. Click on the running workflow
3. Click on the job name to see live logs

### Check Results
After workflow completes:
- Check `jable/database/videos_complete.json` for Jable data
- Check `database/combined_videos.json` for merged data
- Check `javdatabase/database/stats.json` for statistics

---

## 🔒 Security Notes

### ⚠️ Important Security Information

1. **Never commit .env file** - It's already in .gitignore
2. **Keep secrets private** - Don't share them publicly
3. **Rotate keys periodically** - Update secrets if compromised
4. **Use repository secrets** - Not environment variables in workflow file

### What's Protected
- ✅ Secrets are encrypted by GitHub
- ✅ Secrets are not visible in logs
- ✅ Secrets are only available during workflow execution
- ✅ Only repository admins can view/edit secrets

---

## 🛠️ Troubleshooting

### Workflow Not Starting
- ✅ Check if secrets are added correctly
- ✅ Verify GitHub Actions is enabled
- ✅ Check workflow file syntax

### Upload Failures
- ✅ Verify API keys are correct (no extra spaces)
- ✅ Check if API keys are still valid
- ✅ Review error logs in Actions tab

### Rate Limit Errors
- ✅ Workflow will automatically fallback to LuluStream
- ✅ Wait for rate limit to reset (usually 24 hours)
- ✅ Check `database/rate_limit.json` for details

---

## 📝 Quick Copy-Paste

For easy setup, here are your values:

```
Secret Name: STREAMWISH_API_KEY
Secret Value: 31637q4gsnt23yyvd0or6

Secret Name: LULUSTREAM_API_KEY
Secret Value: 229747ohh6h2cd4t2gh3ep
```

---

## 🎯 Next Steps After Setup

1. ✅ Add both secrets
2. ✅ Enable GitHub Actions
3. ✅ Run test workflow (optional)
4. ✅ Monitor first run
5. ✅ Check databases for results

---

## 📞 Support

If you encounter issues:
1. Check Actions logs for error messages
2. Verify secrets are added correctly
3. Ensure API keys are still valid
4. Review workflow file for syntax errors

---

**Setup Time:** ~2 minutes  
**Status:** Ready to deploy  
**Next:** Add secrets and enable Actions!
