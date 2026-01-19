#!/usr/bin/env python3
"""
Railway startup script - ensures PORT variable is properly read
Based on Railway best practices: https://station.railway.com/questions/run-a-uvicorn-python-app-on-railway-0181b041
"""
import os
import uvicorn

if __name__ == "__main__":
    # Railway sets PORT environment variable
    port = int(os.getenv("PORT", 8000))
    host = "0.0.0.0"

    print(f"Starting uvicorn server on {host}:{port}")
    print(f"PORT environment variable: {os.getenv('PORT', 'not set')}")

    uvicorn.run(
        "app.main:app",
        host=host,
        port=port,
        workers=2,  # Use 2 workers for production
        log_level="info"
    )
