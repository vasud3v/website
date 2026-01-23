@echo off
echo ========================================
echo JAVDatabase Enrichment - Batch Mode
echo ========================================
echo.
echo This will enrich all videos in batches of 5
echo Press Ctrl+C to stop at any time
echo.
pause

python enrich_batch.py --batch 5 --start 0

echo.
echo ========================================
echo Batch complete!
echo ========================================
pause
