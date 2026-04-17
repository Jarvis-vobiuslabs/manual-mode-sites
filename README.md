# Manual Mode Sites

Small "manual mode" lead discovery tool: scrape Google Maps for businesses **without websites**, and view them in a simple local web UI.

## What it does
- Searches Google Maps for terms (e.g. "mobile detailing Calgary")
- Opens listings
- Extracts: business name, phone (if visible), Google Maps URL, website (if present)
- Saves only **no-website** leads into `data/leads.json`

## Run the scraper

```bash
cd manual-mode-sites
python3 scripts/scrape_no_website.py --city "Calgary, AB" --term "mobile detailing" --limit 50
```

Outputs:
- `data/leads.json`

## View the leads

```bash
cd manual-mode-sites/app
python3 -m http.server 8088
```

Open:
- http://localhost:8088

## Notes
- This is intentionally separate from the outreach pipeline + Mission Control.
- No auto-send. No MC integration.
