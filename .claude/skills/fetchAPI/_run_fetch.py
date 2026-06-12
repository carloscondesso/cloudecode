import asyncio
import httpx
import csv
import io
import logging
import os
from datetime import datetime
from pathlib import Path

URLS = [
    "https://raw.githubusercontent.com/anshlambagit/AnshLambaYoutube/refs/heads/main/DBT_Masterclass/dim_customer.csv",
    "https://raw.githubusercontent.com/anshlambagit/AnshLambaYoutube/refs/heads/main/DBT_Masterclass/dim_store.csv",
    "https://raw.githubusercontent.com/anshlambagit/AnshLambaYoutube/refs/heads/main/DBT_Masterclass/dim_date.csv",
    "https://raw.githubusercontent.com/anshlambagit/AnshLambaYoutube/refs/heads/main/DBT_Masterclass/dim_product.csv",
    "https://raw.githubusercontent.com/anshlambagit/AnshLambaYoutube/refs/heads/main/DBT_Masterclass/fact_sales.csv",
    "https://raw.githubusercontent.com/anshlambagit/AnshLambaYoutube/refs/heads/main/DBT_Masterclass/fact_returns.csv",
]

BASE = Path(__file__).parent
timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

data_dir = BASE / "data" / timestamp
log_dir = BASE / "logs" / timestamp
data_dir.mkdir(parents=True, exist_ok=True)
log_dir.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    handlers=[
        logging.FileHandler(log_dir / "fetchAPI.log"),
        logging.StreamHandler(),
    ],
)
log = logging.getLogger(__name__)


async def fetch_one(client: httpx.AsyncClient, url: str) -> tuple[str, bytes | None, str | None]:
    filename = url.split("/")[-1]
    try:
        r = await client.get(url, follow_redirects=True, timeout=30)
        r.raise_for_status()
        log.info("SUCCESS  %s  (%d bytes)", url, len(r.content))
        return filename, r.content, None
    except Exception as exc:
        log.error("FAILED   %s  error=%s", url, exc)
        return filename, None, str(exc)


async def main():
    log.info("Starting fetchAPI skill — %d URLs", len(URLS))
    async with httpx.AsyncClient(verify=False) as client:
        results = await asyncio.gather(*[fetch_one(client, u) for u in URLS])

    success, failed = 0, 0
    for filename, content, err in results:
        if content is not None:
            (data_dir / filename).write_bytes(content)
            success += 1
        else:
            failed += 1

    log.info("Done — %d succeeded, %d failed", success, failed)
    log.info("Data saved to: %s", data_dir)
    log.info("Log saved to:  %s", log_dir / 'fetchAPI.log')


asyncio.run(main())
