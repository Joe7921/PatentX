import asyncio
import httpx
import sys

async def main():
    async with httpx.AsyncClient(base_url="http://127.0.0.1:8000") as client:
        # Start server in background? No, server is not running. Let's just write this to test manually if I could.
        pass
