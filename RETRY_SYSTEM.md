# JAVDatabase Smart Retry System

## Overview
Automatically retries videos not found in JAVDatabase every 2 days, up to 5 times (10 days total).

## How It Works

### Timeline Example: FNS-149

```
Day 0 (Jan 22, 2026)
├─ Video scraped from Jable ✅
├─ Uploaded to StreamWish ✅
├─ JAVDatabase lookup → 404 Not Found ❌
├─ Added to retry queue
└─ Next retry: Day 2 (Jan 24, 2026)

Day 2 (Jan 24, 2026) - RETRY #1
├─ Workflow starts
├─ Check retry queue → FNS-149 ready
├─ JAVDatabase lookup → Still not found ❌
├─ Retry count: 1/5
└─ Next retry: Day 4 (Jan 26, 2026)

Day 4 (Jan 26, 2026) - RETRY #2
├─ Workflow starts
├─ Check retry q