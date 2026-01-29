# Pakt - Plex-Trakt Sync Tool

Python CLI/web app that syncs watched status and ratings between Plex and Trakt using batch API operations.

## Architecture

- **sync.py** - SyncEngine with 4-phase sync (fetch, index, compare, apply)
- **cli.py** - Click-based CLI
- **web/app.py** - FastAPI endpoints
- **web/templates/index.html** - Single-page web UI
- **trakt.py** - Async Trakt API client with VIP limit handling
- **plex.py** - PlexAPI wrapper with media metadata extraction
- **config.py** - Pydantic settings with env file support
- **scheduler.py** - APScheduler-based automatic sync
- **tray.py** - pystray system tray integration (Windows)

## Implemented Features

- CLI commands: sync, login, logout, setup, status, libraries, serve, clear-cache
- Web UI with tabbed interface (Sync, Stats, Settings views)
- Batch API operations for Trakt (single calls for all watched/ratings)
- Batch episode fetch from Plex (searchEpisodes() instead of per-show calls)
- Bidirectional sync: movies watched, movie ratings, episode watched, episode ratings
- Library selection (CLI and web UI)
- File logging to ~/.config/pakt/sync.log
- OAuth device flow for Trakt auth
- Progress reporting to web UI console
- **Collection sync** (Plex → Trakt) with full media metadata:
  - Resolution (4K, 1080p, 720p, etc.)
  - HDR type (Dolby Vision, HDR10, HDR10+, HLG)
  - Audio codec (Atmos, TrueHD, DTS-X, DTS-HD MA, etc.)
  - Best quality version scoring when multiple versions exist
- **Watchlist sync** (bidirectional):
  - Plex → Trakt watchlist
  - Trakt → Plex watchlist (uses Plex Discover for items not in library)
- **Scheduled sync** via APScheduler:
  - Configurable interval (hours)
  - Enable/disable via web UI
  - Automatic startup with server
- **System tray icon** (Windows, optional):
  - Double-click to open web UI
  - Right-click menu: Open Web UI, Sync Now, Exit
  - `pakt serve --tray` or `--no-tray` flags
- **Trakt VIP/Free account handling**:
  - Detects VIP status via `/users/settings` endpoint
  - Free users limited to 100 items in collection/watchlist
  - Warns and skips sync if at limit (prevents HTTP 420 errors)
  - Catches `TraktAccountLimitError` gracefully with upgrade URL
  - API endpoint `/api/trakt/account` returns VIP status and limits

## Trakt Account Limits (Jan 2025)

Free users have 100 item limit on:
- Collection (movies + shows combined)
- Watchlist
- Personal lists (2 lists max, 100 items each)

VIP users have unlimited. Sync will:
1. Check limits before attempting collection/watchlist sync
2. Skip sync with warning if already at limit
3. Catch HTTP 420 errors and log upgrade URL

## Current State

All features implemented including VIP handling. Ready for testing.

## Next Steps

1. Test collection sync with real data (VIP and non-VIP)
2. Test watchlist sync bidirectionally
3. Test scheduler functionality
4. Show ratings sync (currently only episode ratings, not show-level)
5. Add VIP status indicator to web UI

## Testing

```bash
pip install -e .              # Basic install
pip install -e ".[tray]"      # With system tray support
pakt serve                    # Web UI at http://localhost:8080
pakt serve --tray             # With system tray icon
pakt sync --dry-run
```
