# Rafael Valle's Personal Website

A static, SEO-friendly academic website that displays publications fetched from Google Scholar, with support for hand-curated entries.

## Overview

This repository contains:
- **Static HTML generation** from JSON data files
- **Google Scholar integration** to automatically fetch new publications
- **Hand-curation support** where your manual edits always take priority

## Files

| File | Description |
|------|-------------|
| `index.html` | The generated static website (SEO-friendly) |
| `data.json` | Your hand-curated publication data (source of truth) |
| `data_prefetched.json` | Combined data: your curated entries + new Scholar entries |
| `site.json` | Site structure: which publications to show, news items, display order |
| `fetch_scholar.py` | Fetches new publications from Google Scholar |
| `build_site.py` | Generates static `index.html` from JSON data |

## Quick Start

```bash
# Build the site with your curated data
python3 build_site.py --data data.json

# Start a local server to preview
python3 -m http.server 8000
# Visit http://localhost:8000
```

### Fetch new publications from Google Scholar

```bash
source /Users/rafaelvalle/VirtualEnvironments/dl-ml/venv/bin/activate
python3 fetch_scholar.py
```

## Common Tasks

### Update the site with existing data

If you've edited `data.json` or `site.json` and want to regenerate the site:

```bash
python3 build_site.py --data data.json
```

### Add a new publication manually

1. **Edit `data.json`** - Add your publication entry:
   ```json
   "MYPAPER": {
     "title": "My Paper Title",
     "authors": ["Author One", "Author Two", "Rafael Valle"],
     "venue": "Conference Name",
     "year": 2025,
     "links": {
       "arxiv": "https://arxiv.org/abs/...",
       "website": "https://project-page.com",
       "code": "https://github.com/..."
     },
     "media": {
       "type": "image",
       "src": "images/mypaper.png"
     },
     "abstract": "Paper abstract here...",
     "bibtex": "@article{...}"
   }
   ```

2. **Edit `site.json`** - Add the ID to the publications list:
   ```json
   "entries": [
     "MYPAPER",
     "FUGATTO",
     ...
   ]
   ```

3. **Rebuild the site**:
   ```bash
   python3 build_site.py --data data.json
   ```

### Fetch new publications from Google Scholar

This fetches your latest publications and adds any new ones not already in `data.json`:

```bash
# Activate your Python environment with scholarly installed
source /Users/rafaelvalle/VirtualEnvironments/dl-ml/venv/bin/activate

# Fetch from Google Scholar
python3 fetch_scholar.py
```

**What happens:**
- All entries from `data.json` are preserved exactly as-is
- New publications (matched by title) are added with placeholder fields
- Output is written to `data_prefetched.json`

**Quick review:** Open `data_prefetched.json` and look at the `_summary` section at the top:

```json
{
  "_summary": {
    "from_data_json": ["FUGATTO", "OMCAT", ...],
    "new_from_scholar": ["NEWPAPER1", "NEWPAPER2", ...],
    "all_ids": [...]
  },
  "publications": { ... }
}
```

- `from_data_json` - Your curated entries (preserved as-is)
- `new_from_scholar` - New entries to review and potentially add
- `all_ids` - Complete list of all publication IDs

**After fetching:**
1. Check `_summary.new_from_scholar` for new publication IDs
2. Find those entries in `publications` and copy to `data.json`
3. Curate them (add media, bibtex, website links, etc.)
4. Add IDs to `site.json`
5. Rebuild: `python3 build_site.py --data data.json`

### Add a news item

Edit `site.json` and add to the news section:

```json
{
  "id": "MYPAPER",
  "text": "Description of the news",
  "suffix": " - optional suffix with <a href='...'>links</a>"
}
```

### Mark a publication as "new"

Add the publication ID to `newBadgeIds` in `site.json`:

```json
"newBadgeIds": [
  "MYPAPER",
  "FUGATTO",
  ...
]
```

### Change publication display order

Edit the `entries` array in `site.json` under the publications section. Publications appear in the order listed.

### Preview with Google Scholar data

To see what the site looks like with all Scholar publications (including uncurated ones):

```bash
python3 build_site.py --data data_prefetched.json
python3 -m http.server 8000
```

## Media Types

The `media` field in publication entries supports several types:

### Image
```json
"media": {
  "type": "image",
  "src": "images/paper.png"
}
```

### YouTube video
```json
"media": {
  "type": "youtube",
  "src": "https://www.youtube.com/embed/VIDEO_ID"
}
```

### Image with audio sample
```json
"media": {
  "type": "image_audio",
  "image_src": "images/paper.png",
  "audio_src": "https://example.com/sample.wav",
  "audio_caption": "Optional caption for the audio"
}
```

### Image with multiple audio samples
```json
"media": {
  "type": "image_audio_multiple",
  "image_src": "images/paper.png",
  "audio_samples": [
    {"label": "Input", "src": "https://example.com/input.wav"},
    {"label": "Output", "src": "https://example.com/output.wav"}
  ]
}
```

### Image with YouTube video
```json
"media": {
  "type": "image_youtube",
  "image_src": "images/paper.png",
  "youtube_src": "https://www.youtube.com/embed/VIDEO_ID"
}
```

### SoundCloud embed
```json
"media": {
  "type": "soundcloud",
  "src": "https://w.soundcloud.com/player/?url=..."
}
```

## Configuration

Edit `site.json` to configure:

```json
{
  "config": {
    "ownerName": "Rafael Valle",
    "highlightColor": "deeppink"
  },
  ...
}
```

- `ownerName`: Your name (highlighted in author lists)
- `highlightColor`: CSS color for name highlighting

## Dependencies

- Python 3.x
- `scholarly` library (for Google Scholar fetching): `pip install scholarly`

## Deployment

The generated `index.html` is a static file that can be deployed anywhere:
- GitHub Pages (just push to the repo)
- Any static hosting service
- Local file system

## Troubleshooting

### Publications not showing up
- Check that the publication ID exists in `data.json`
- Check that the ID is listed in `site.json` under `entries`
- Rebuild with `python3 build_site.py --data data.json`

### Google Scholar fetch fails
- Scholar may rate-limit requests; wait and try again
- Check your internet connection
- Verify `SCHOLAR_ID` in `fetch_scholar.py` is correct

### Abstract/bibtex toggle not working
- Ensure `js/hidebib.js` exists and is loaded
- Check browser console for JavaScript errors
