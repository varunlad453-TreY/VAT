#!/usr/bin/env python3
"""
Backend mirror for ingest_vendor_docs.py
"""
import sys
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from scripts.ingest_vendor_docs import main, run_ingestion_pipeline

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
