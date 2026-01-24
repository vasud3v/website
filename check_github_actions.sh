#!/bin/bash

# Script to check GitHub Actions workflow runs
# This helps diagnose why the workflow isn't running

echo "=========================================="
echo "CHECKING GITHUB ACTIONS WORKFLOW RUNS"
echo "=========================================="
echo ""

REPO="vasud3v/main-scraper"
WORKFLOW_NAME="integrated_scraper.yml"

echo "Repository: $REPO"
echo "Workflow: $WORKFLOW_NAME"
echo "Current time: $(date -u '+%Y-%m-%d %H:%M:%S UTC')"
echo ""

# Check if gh CLI is installed
if ! command -v gh &> /dev/null; then
    echo "❌ GitHub CLI (gh) is not installed"
    echo ""
    echo "To install:"
    echo "  Windows: winget install GitHub.cli"
    echo "  Or download from: https://cli.github.com/"
    echo ""
    echo "After installing, authenticate with: gh auth login"
    exit 1
fi

# Check if authenticated
if ! gh auth status &> /dev/null; then
    echo "❌ Not authenticated with GitHub CLI"
    echo ""
    echo "Please run: gh auth login"
    exit 1
fi

echo "✅ GitHub CLI is installed and authenticated"
echo ""

echo "=========================================="
echo "RECENT WORKFLOW RUNS (Last 10)"
echo "=========================================="
gh run list --repo "$REPO" --workflow "$WORKFLOW_NAME" --limit 10 --json databaseId,status,conclusion,createdAt,updatedAt,event,displayTitle | \
    jq -r '.[] | "\(.databaseId) | \(.status) | \(.conclusion // "N/A") | \(.event) | \(.createdAt) | \(.displayTitle)"' | \
    while IFS='|' read -r id status conclusion event created title; do
        echo "Run ID: $id"
        echo "  Status: $status"
        echo "  Conclusion: $conclusion"
        echo "  Event: $event"
        echo "  Created: $created"
        echo "  Title: $title"
        echo ""
    done

echo "=========================================="
echo "CHECKING FOR QUEUED/IN-PROGRESS RUNS"
echo "=========================================="
ACTIVE_RUNS=$(gh run list --repo "$REPO" --workflow "$WORKFLOW_NAME" --status in_progress,queued --limit 5 --json databaseId,status,createdAt)
ACTIVE_COUNT=$(echo "$ACTIVE_RUNS" | jq '. | length')

if [ "$ACTIVE_COUNT" -eq 0 ]; then
    echo "❌ No active runs found"
    echo ""
    echo "This explains why no new runs are starting:"
    echo "  - Last run completed 7+ hours ago"
    echo "  - No runs currently active"
    echo "  - Cron schedule should have triggered multiple runs by now"
    echo ""
    echo "Possible causes:"
    echo "  1. GitHub Actions cron delays/skips (most likely)"
    echo "  2. Workflow is disabled"
    echo "  3. GitHub Actions quota exhausted"
else
    echo "✅ Found $ACTIVE_COUNT active run(s):"
    echo "$ACTIVE_RUNS" | jq -r '.[] | "  Run \(.databaseId): \(.status) (created \(.createdAt))"'
fi

echo ""
echo "=========================================="
echo "CHECKING WORKFLOW STATUS"
echo "=========================================="
WORKFLOW_INFO=$(gh api "repos/$REPO/actions/workflows/$WORKFLOW_NAME" 2>/dev/null)

if [ $? -eq 0 ]; then
    STATE=$(echo "$WORKFLOW_INFO" | jq -r '.state')
    echo "Workflow state: $STATE"
    
    if [ "$STATE" = "disabled_manually" ]; then
        echo "❌ Workflow is DISABLED"
        echo ""
        echo "To enable:"
        echo "  gh workflow enable $WORKFLOW_NAME --repo $REPO"
    elif [ "$STATE" = "active" ]; then
        echo "✅ Workflow is ACTIVE"
    fi
else
    echo "⚠️ Could not fetch workflow info"
fi

echo ""
echo "=========================================="
echo "RECOMMENDATIONS"
echo "=========================================="
echo ""
echo "1. IMMEDIATE: Manually trigger the workflow to test the fix"
echo "   Command: gh workflow run $WORKFLOW_NAME --repo $REPO -f action=scrape"
echo ""
echo "2. Monitor the run:"
echo "   Command: gh run watch --repo $REPO"
echo ""
echo "3. If successful, consider changing cron to run more frequently"
echo "   Edit: .github/workflows/integrated_scraper.yml"
echo "   Change: cron: '*/30 * * * *' to cron: '*/15 * * * *'"
echo ""
echo "=========================================="
