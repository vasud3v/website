#!/usr/bin/env python3
"""
Test complete workflow with proper output flushing
"""

import sys
import os

# Force unbuffered output
sys.stdout.reconfigure(line_buffering=True)
os.environ['PYTHONUNBUFFERED'] = '1'

from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

print("="*70, flush=True)
print("STARTING WORKFLOW TEST", flush=True)
print("="*70, flush=True)

print("\nImporting WorkflowManager...", flush=True)
from javgg.complete_workflow import WorkflowManager

print("Creating WorkflowManager instance...", flush=True)
workflow = WorkflowManager()

print("Starting workflow with max_videos=1...", flush=True)
workflow.run(max_videos=1)

print("\n✅ Workflow test complete!", flush=True)
