#!/usr/bin/env python3
import argparse, asyncio, json, re
from datetime import datetime
from pathlib import Path
from urllib.parse import quote

from playwright.async_api import async_playwright

OUT = Path(__file__).resolve().parents[1] / "data" / "leads.json"

PHONE_RE = re.compile(r"(\+?1[\s-]?)?(\(?\d{3}\)?[\s-]?\d{3}[\s-]?\d{4})")

async def scrape(city: str, term: str, limit: int):
    query = f"{term} {city}".strip()
    maps_url = f"https://www.google.com/maps/search/{quote(query)}"

    leads = []
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page(viewport={"width": 1280, "height": 900})
        await page.goto(maps_url, wait_until="domcontentloaded")
        await page.wait_for_timeout(2500)

        # Scroll results panel
        results_selector = 'div[role="feed"]'
        for _ in range(12):
            await page.mouse.wheel(0, 1800)
            await page.wait_for_timeout(900)

        # Collect listing URLs as plain strings (avoid ElementHandle invalidation on navigation)
        hrefs = await page.eval_on_selector_all(
            'a[href^="https://www.google.com/maps/place"]',
            'els => Array.from(new Set(els.map(e => e.href).filter(Boolean)))'
        )

        seen = set()
        for href in hrefs:
            if not href or href in seen:
                continue
            seen.add(href)
            # open listing
            await page.goto(href, wait_until="domcontentloaded")
            await page.wait_for_timeout(2000)

            name = ""
            try:
                h1 = await page.query_selector('h1')
                if h1:
                    name = (await h1.inner_text()).strip()
            except: pass

            # website button
            website = ""
            try:
                wbtn = await page.query_selector('a[data-item-id="authority"]')
                if wbtn:
                    website = (await wbtn.get_attribute('href')) or ""
            except: pass

            # phone
            phone = ""
            try:
                pbtn = await page.query_selector('button[data-item-id^="phone:"]')
                if pbtn:
                    txt = (await pbtn.inner_text()).strip()
                    m = PHONE_RE.search(txt)
                    if m:
                        phone = m.group(0)
            except: pass

            if website:
                continue  # we only keep no-website

            leads.append({
                "name": name,
                "phone": phone,
                "city": city,
                "term": term,
                "maps_url": href,
                "added_at": datetime.utcnow().isoformat() + "Z",
            })
            if len(leads) >= limit:
                break

        await browser.close()

    return leads

def merge_unique(existing, new):
    seen = {(x.get('name',''), x.get('phone',''), x.get('maps_url','')) for x in existing}
    for x in new:
        key = (x.get('name',''), x.get('phone',''), x.get('maps_url',''))
        if key not in seen:
            existing.append(x)
            seen.add(key)
    return existing

async def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--city', required=True)
    ap.add_argument('--term', required=True)
    ap.add_argument('--limit', type=int, default=50)
    args = ap.parse_args()

    OUT.parent.mkdir(parents=True, exist_ok=True)
    existing = json.loads(OUT.read_text()) if OUT.exists() else []

    new = await scrape(args.city, args.term, args.limit)
    merged = merge_unique(existing, new)
    OUT.write_text(json.dumps(merged, indent=2))
    print(f"Saved {len(new)} new leads. Total: {len(merged)} -> {OUT}")

if __name__ == '__main__':
    asyncio.run(main())
