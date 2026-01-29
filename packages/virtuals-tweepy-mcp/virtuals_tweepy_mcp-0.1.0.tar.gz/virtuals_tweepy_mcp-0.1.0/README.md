# Virtuals Observer

A CLI tool to interact with X (Twitter) using Virtuals Protocol's GAME SDK enterprise API.

## Features

- Search tweets by keywords, hashtags, or advanced queries
- Fetch any user's timeline
- Get user profile information
- View your mentions and home timeline
- Fetch individual tweets with full media/video URLs
- Extract X Article content (long-form posts)
- Post tweets
- Higher rate limits than standard Twitter API (35-50 calls/5 min)

## Installation

```bash
# Clone the repo
git clone git@github.com:kyoungrok0517/virtuals-observer.git
cd virtuals-observer

# Install with uv (installs `vobs` command)
uv sync
```

## Setup

### 1. Get GAME API Key

1. Register at [GAME Console](https://console.game.virtuals.io/)
2. Create a new project
3. Generate an API key

### 2. Configure Environment

Create a `.env` file:

```env
GAME_API_KEY=your-api-key-here
```

### 3. Authenticate with Twitter

```bash
uv run vobs auth
```

This opens a browser for OAuth. After authorizing, add the token to `.env`:

```env
GAME_API_KEY=your-api-key-here
GAME_TWITTER_ACCESS_TOKEN=apx-your-token-here
```

## CLI Usage

### Verify Authentication

```bash
uv run vobs me
```

Output:
```
Username:    @yourhandle
Name:        Your Name
Followers:   1,234
Following:   567
Tweets:      890
```

### Search Tweets

```bash
# Search by keyword
uv run vobs search "bitcoin"

# Search by hashtag
uv run vobs search "#AI"

# Search with operators
uv run vobs search "from:elonmusk crypto"

# Limit results
uv run vobs search "#DeFi" -n 20
```

### Get User Timeline

```bash
# Get user's recent tweets
uv run vobs timeline VitalikButerin

# Exclude retweets
uv run vobs timeline elonmusk --no-retweets

# Limit results
uv run vobs timeline jack -n 5
```

### Get User Info

```bash
uv run vobs user elonmusk
```

Output:
```
Username:    @elonmusk
Name:        Elon Musk
Followers:   150,000,000
Following:   500
Tweets:      30,000
Location:    Mars
```

### View Your Mentions

```bash
uv run vobs mentions
uv run vobs mentions -n 20
```

### View Home Timeline

```bash
uv run vobs home
uv run vobs home -n 50
```

### Fetch a Tweet

```bash
# Fetch by URL or ID
uv run vobs fetch https://x.com/user/status/123456789

# Output as JSON
uv run vobs fetch https://x.com/user/status/123456789 --json

# Skip auto-fetching X Article content
uv run vobs fetch https://x.com/user/status/123456789 --no-article
```

The fetch command extracts:
- Tweet text, author, metrics (likes, retweets, etc.)
- Media URLs (images, videos with quality variants)
- Entity URLs (expanded links, article links)
- X Article content (auto-detected and fetched via Playwright)

### Post a Tweet

```bash
# With confirmation prompt
uv run vobs post "Hello world!"

# Skip confirmation
uv run vobs post "Hello world!" -y
```

## Search Query Syntax

The search command supports Twitter's advanced search operators:

| Operator | Example | Description |
|----------|---------|-------------|
| Keyword | `crypto` | Contains word |
| Phrase | `"bitcoin price"` | Exact phrase |
| Hashtag | `#DeFi` | Has hashtag |
| `from:` | `from:elonmusk` | Tweets by user |
| `to:` | `to:VitalikButerin` | Replies to user |
| `-` | `bitcoin -scam` | Exclude term |
| `OR` | `ETH OR BTC` | Either term |
| `has:media` | `news has:media` | Has images/videos |
| `has:links` | `crypto has:links` | Contains URLs |
| `min_faves:` | `AI min_faves:100` | Minimum likes |
| `min_retweets:` | `news min_retweets:50` | Minimum RTs |
| `lang:` | `bitcoin lang:en` | Language filter |

### Example Queries

```bash
# High-engagement AI tweets
uv run vobs search "#AI min_faves:100 -is:retweet lang:en"

# News with links from specific accounts
uv run vobs search "(from:Reuters OR from:AP) crypto has:links"

# Discussions about multiple topics
uv run vobs search "(ethereum OR solana) DeFi -scam"
```

## Rate Limits

- **Tier 1 (Default)**: 50 calls / 5 minutes
- **Tier 2 (Elevated)**: Higher limits (requires Virtuals approval)

## Documentation

See [docs/VIRTUALS_TWITTER_PLUGIN.md](docs/VIRTUALS_TWITTER_PLUGIN.md) for comprehensive API documentation.

## License

MIT
