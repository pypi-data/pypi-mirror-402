import asyncio
import time
import aiohttp
from statistics import mean

async def worker(session, url, results):
    start = time.perf_counter()
    try:
        async with session.get(url) as resp:
            await resp.read()
            ok = resp.status < 500
    except Exception:
        ok = False
    elapsed = time.perf_counter() - start
    results.append((ok, elapsed))

async def run(url: str, workers: int, requests: int, timeout: int):
    results = []
    conn = aiohttp.TCPConnector(limit=workers)
    timeout_cfg = aiohttp.ClientTimeout(total=timeout)

    async with aiohttp.ClientSession(connector=conn, timeout=timeout_cfg) as session:
        tasks = []
        for _ in range(requests):
            tasks.append(worker(session, url, results))
        await asyncio.gather(*tasks)

    ok = sum(1 for r, _ in results if r)
    times = [t for _, t in results]
    return {
        "total": len(results),
        "ok": ok,
        "fail": len(results) - ok,
        "avg_ms": round(mean(times) * 1000, 2) if times else 0,
        "p95_ms": round(sorted(times)[int(0.95 * len(times))] * 1000, 2) if times else 0,
    }