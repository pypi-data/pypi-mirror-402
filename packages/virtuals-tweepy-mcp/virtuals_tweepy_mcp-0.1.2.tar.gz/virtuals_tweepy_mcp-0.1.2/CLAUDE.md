# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

A CLI tool (`vobs`) that interacts with X (Twitter) via Virtuals Protocol's GAME SDK enterprise API. The key insight is that Virtuals provides enterprise-level Twitter API access (35-50 calls/5 min) through `virtuals-tweepy`, which we use as a standalone library without the full agent framework.

## Development Commands

```bash
# Install dependencies and the vobs CLI command
uv sync

# Run CLI commands
uv run vobs <command>

# Or after installation, directly:
vobs <command>
```

There is no test suite or linter configured.

For long-running commands (like `monitor`), use tmux instead of running in background.

## Architecture

**Single-file CLI**: All functionality lives in `src/virtuals_observer/cli.py` (~900 lines).

**Command structure**: Each command is a `cmd_<name>(args)` function registered via argparse subparsers.

| Command | Function | Purpose |
|---------|----------|---------|
| `auth` | `cmd_auth` | OAuth flow via GAME SDK |
| `me` | `cmd_me` | Get authenticated user profile |
| `search` | `cmd_search` | Search tweets with Twitter query syntax |
| `timeline` | `cmd_timeline` | Get user's tweets |
| `user` | `cmd_user` | Get user profile info |
| `fetch` | `cmd_fetch` | Fetch specific tweet by URL/ID with media extraction |
| `post` | `cmd_post` | Post a tweet |
| `mentions` | `cmd_mentions` | Get your mentions |
| `home` | `cmd_home` | Get your home timeline |
| `monitor` | `cmd_monitor` | Real-time polling for new tweets |

**Key patterns**:
- `get_client()` initializes the `virtuals_tweepy.Client` with the access token
- State persistence at `~/.vobs_state.json` for monitor resume functionality
- Playwright integration for X Article content extraction (`fetch_article_content()`)
- Signal handlers for graceful shutdown in monitor command

## Environment Variables

Required in `.env`:
- `GAME_API_KEY` - For initial authentication
- `GAME_TWITTER_ACCESS_TOKEN` - For API calls (obtained via `vobs auth`)

## API Reference

See `docs/VIRTUALS_TWITTER_PLUGIN.md` for comprehensive Virtuals Twitter Plugin documentation including rate limits, search operators, and available client methods.
