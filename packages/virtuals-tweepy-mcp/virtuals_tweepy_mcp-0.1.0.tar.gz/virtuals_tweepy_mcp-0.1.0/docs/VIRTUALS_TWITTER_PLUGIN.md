# Virtuals Twitter Plugin - Comprehensive Documentation

This document provides complete documentation for using the Virtuals GAME SDK Twitter Plugin to interact with X (Twitter) via their enterprise API.

## Table of Contents

1. [Overview](#overview)
2. [Installation](#installation)
3. [Authentication](#authentication)
4. [Quick Start](#quick-start)
5. [API Reference](#api-reference)
6. [Search Query Syntax](#search-query-syntax)
7. [Rate Limits](#rate-limits)
8. [Error Handling](#error-handling)
9. [Examples](#examples)

---

## Overview

The Virtuals Twitter Plugin provides programmatic access to X (Twitter) through Virtuals Protocol's enterprise API endpoint. It wraps `virtuals_tweepy`, a fork of the popular Tweepy library, offering:

- **Higher rate limits** than standard Twitter API (35-50 calls per 5 minutes)
- **Full Twitter API v2 coverage** (search, timelines, posting, engagement)
- **OAuth 2.0 with PKCE** authentication
- **Tweepy-compatible interface**

---

## Installation

### Option 1: pip (Recommended)

```bash
# Install the Twitter plugin
pip install twitter_plugin_gamesdk

# Or install the underlying tweepy wrapper directly
pip install virtuals-tweepy
```

### Option 2: From Source

```bash
git clone https://github.com/game-by-virtuals/game-python.git
cd game-python/plugins/twitter
pip install -e .

# Or with Poetry
poetry install
```

### Dependencies

```
python >= 3.9
virtuals-tweepy
python-dotenv
```

---

## Authentication

### Step 1: Get a GAME API Key

1. Register at [GAME Console](https://console.game.virtuals.io/)
2. Create a new project
3. Generate an API key

### Step 2: Generate Twitter Access Token

Run the authentication command:

```bash
poetry run twitter-plugin-gamesdk auth -k <YOUR_GAME_API_KEY>

# Or if installed via pip:
python -m twitter_plugin_gamesdk auth -k <YOUR_GAME_API_KEY>
```

This initiates OAuth 2.0 with PKCE flow:
1. A URL will be displayed - open it in your browser
2. Authorize the application with your X account
3. You'll receive an access token in format: `apx-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx`

### Step 3: Store Credentials

Create a `.env` file:

```env
# Required - Virtuals GAME Twitter Access Token
GAME_TWITTER_ACCESS_TOKEN=apx-your-token-here

# Alternative authentication methods (optional)
TWITTER_BEARER_TOKEN=your-bearer-token
TWITTER_API_KEY=your-api-key
TWITTER_API_SECRET_KEY=your-api-secret
TWITTER_ACCESS_TOKEN=your-access-token
TWITTER_ACCESS_TOKEN_SECRET=your-access-token-secret
```

---

## Quick Start

### Using TwitterPlugin (High-level wrapper)

```python
import os
from dotenv import load_dotenv
from twitter_plugin_gamesdk.twitter_plugin import TwitterPlugin

load_dotenv()

# Initialize plugin
options = {
    "credentials": {
        "game_twitter_access_token": os.environ.get("GAME_TWITTER_ACCESS_TOKEN")
    }
}
twitter_plugin = TwitterPlugin(options)

# Get the underlying client
client = twitter_plugin.twitter_client

# Post a tweet
response = client.create_tweet(text="Hello from Virtuals!")
print(f"Tweet posted: https://twitter.com/i/status/{response.data['id']}")
```

### Using virtuals_tweepy Client Directly

```python
import os
from dotenv import load_dotenv
from virtuals_tweepy import Client

load_dotenv()

# Initialize client with GAME token
client = Client(
    game_twitter_access_token=os.environ.get("GAME_TWITTER_ACCESS_TOKEN")
)

# Get your own profile
me = client.get_me()
print(f"Logged in as: @{me.data.username}")
```

---

## API Reference

### Tweet Management

#### `create_tweet()`

Create a new tweet with optional media, polls, and reply settings.

```python
response = client.create_tweet(
    text="Your tweet content",                    # Tweet text (up to 280 chars)
    media_ids=None,                               # List of media IDs to attach
    poll_options=None,                            # List of poll options (2-4 choices)
    poll_duration_minutes=None,                   # Poll duration (5-10080 minutes)
    quote_tweet_id=None,                          # Tweet ID to quote
    in_reply_to_tweet_id=None,                    # Tweet ID to reply to
    reply_settings=None,                          # "everyone", "mentionedUsers", "following"
    exclude_reply_user_ids=None,                  # User IDs to exclude from reply thread
    place_id=None,                                # Location place ID
    for_super_followers_only=False,               # Restrict to super followers
    user_auth=True
)
print(response.data)  # {'id': '1234567890', 'text': 'Your tweet content'}
```

#### `delete_tweet(id)`

Delete an existing tweet.

```python
client.delete_tweet(id="1234567890")
```

#### `upload_media(media, media_type)`

Upload media and get a media ID for attachment.

```python
# Upload from file
with open("image.png", "rb") as f:
    media_data = f.read()
media_id = client.upload_media(media=media_data, media_type="image/png")

# Use in tweet
client.create_tweet(text="Check this out!", media_ids=[media_id])
```

Supported media types:
- Images: `image/png`, `image/jpeg`, `image/gif`, `image/webp`
- Videos: `video/mp4`

---

### Search & Discovery

#### `search_recent_tweets(query, **params)`

Search tweets from the last 7 days.

```python
response = client.search_recent_tweets(
    query="#Bitcoin",                              # Search query (required)
    max_results=10,                                # 10-100 results per page
    tweet_fields=["created_at", "public_metrics"], # Additional fields
    expansions=["author_id"],                      # Expand referenced objects
    user_fields=["username", "verified"]           # Fields for expanded users
)

for tweet in response.data:
    print(f"@{tweet.author_id}: {tweet.text}")
```

#### `search_all_tweets(query, **params)`

Search the complete history of public tweets (requires elevated access).

```python
response = client.search_all_tweets(
    query="from:elonmusk crypto",
    max_results=100,
    start_time="2024-01-01T00:00:00Z",            # ISO 8601 format
    end_time="2024-12-31T23:59:59Z"
)
```

#### `get_tweet(id, **params)`

Get a single tweet by ID.

```python
response = client.get_tweet(
    id="1234567890",
    tweet_fields=["created_at", "public_metrics", "entities"],
    expansions=["author_id", "attachments.media_keys"],
    media_fields=["url", "preview_image_url"]
)
print(response.data)
```

#### `get_tweets(ids, **params)`

Get multiple tweets by IDs (up to 100).

```python
response = client.get_tweets(
    ids=["1234567890", "0987654321"],
    tweet_fields=["created_at", "public_metrics"]
)
```

---

### Timelines

#### `get_home_timeline(**params)`

Get your home timeline (tweets from accounts you follow).

```python
response = client.get_home_timeline(
    max_results=50,
    tweet_fields=["created_at", "public_metrics"],
    user_auth=True
)
```

#### `get_users_tweets(id, **params)`

Get tweets from any user by their user ID.

```python
# First, get user ID from username
user = client.get_user(username="elonmusk")
user_id = user.data.id

# Then get their tweets
response = client.get_users_tweets(
    id=user_id,
    max_results=10,
    tweet_fields=["created_at", "public_metrics"],
    exclude=["retweets", "replies"]               # Optional: exclude RTs/replies
)

for tweet in response.data:
    print(f"{tweet.created_at}: {tweet.text}")
```

#### `get_users_mentions(id, **params)`

Get tweets mentioning a specific user.

```python
response = client.get_users_mentions(
    id=user_id,
    max_results=50,
    tweet_fields=["created_at", "author_id"]
)
```

---

### Engagement

#### Likes

```python
# Like a tweet
client.like(tweet_id="1234567890")

# Unlike a tweet
client.unlike(tweet_id="1234567890")

# Get users who liked a tweet
likers = client.get_liking_users(id="1234567890")

# Get tweets a user has liked
liked = client.get_liked_tweets(id=user_id, max_results=100)
```

#### Retweets

```python
# Retweet
client.retweet(tweet_id="1234567890")

# Undo retweet
client.unretweet(source_tweet_id="1234567890")

# Get users who retweeted
retweeters = client.get_retweeters(id="1234567890")
```

#### Replies

```python
# Reply to a tweet
client.create_tweet(
    text="Great point!",
    in_reply_to_tweet_id="1234567890"
)

# Quote tweet
client.create_tweet(
    text="This is important:",
    quote_tweet_id="1234567890"
)

# Hide/unhide a reply to your tweet
client.hide_reply(id="1234567890")
client.unhide_reply(id="1234567890")

# Get quote tweets of a tweet
quotes = client.get_quote_tweets(id="1234567890")
```

---

### User Operations

#### User Lookup

```python
# Get your own profile
me = client.get_me(user_fields=["public_metrics", "description", "created_at"])
print(f"Followers: {me.data.public_metrics['followers_count']}")

# Get user by username
user = client.get_user(
    username="elonmusk",
    user_fields=["public_metrics", "description", "verified"]
)

# Get user by ID
user = client.get_user(id="44196397")

# Get multiple users
users = client.get_users(
    usernames=["elonmusk", "jack", "satlobal"],
    user_fields=["public_metrics"]
)
```

#### Following & Followers

```python
# Follow a user
client.follow_user(target_user_id="44196397")

# Unfollow
client.unfollow_user(target_user_id="44196397")

# Get followers of a user
followers = client.get_users_followers(
    id=user_id,
    max_results=100,
    user_fields=["public_metrics", "verified"]
)

# Get accounts a user follows
following = client.get_users_following(
    id=user_id,
    max_results=100
)
```

#### Muting & Blocking

```python
# Mute a user
client.mute(target_user_id="44196397")
client.unmute(target_user_id="44196397")

# Get muted users
muted = client.get_muted()

# Get blocked users
blocked = client.get_blocked()
```

---

### Bookmarks

```python
# Bookmark a tweet
client.bookmark(tweet_id="1234567890")

# Remove bookmark
client.remove_bookmark(tweet_id="1234567890")

# Get bookmarked tweets
bookmarks = client.get_bookmarks(max_results=100)
```

---

### Analytics

```python
# Count recent tweets matching query
counts = client.get_recent_tweets_count(
    query="#Bitcoin",
    granularity="day"                             # "minute", "hour", or "day"
)

# Count all tweets (requires elevated access)
counts = client.get_all_tweets_count(
    query="from:elonmusk",
    granularity="day",
    start_time="2024-01-01T00:00:00Z"
)
```

---

## Search Query Syntax

The search methods accept standard Twitter search operators:

### Basic Operators

| Operator | Example | Description |
|----------|---------|-------------|
| Keyword | `crypto` | Tweets containing "crypto" |
| Phrase | `"bitcoin price"` | Exact phrase match |
| Hashtag | `#DeFi` | Tweets with hashtag |
| Mention | `@elonmusk` | Tweets mentioning user |
| OR | `bitcoin OR ethereum` | Either term |
| AND | `bitcoin AND ethereum` | Both terms (default) |
| NOT / `-` | `bitcoin -scam` | Exclude term |

### User Operators

| Operator | Example | Description |
|----------|---------|-------------|
| `from:` | `from:elonmusk` | Tweets by user |
| `to:` | `to:elonmusk` | Replies to user |
| `retweets_of:` | `retweets_of:elonmusk` | Retweets of user's tweets |

### Content Operators

| Operator | Example | Description |
|----------|---------|-------------|
| `is:retweet` | `bitcoin is:retweet` | Only retweets |
| `-is:retweet` | `bitcoin -is:retweet` | Exclude retweets |
| `is:reply` | `crypto is:reply` | Only replies |
| `is:quote` | `news is:quote` | Only quote tweets |
| `has:media` | `announcement has:media` | Has images/videos |
| `has:images` | `meme has:images` | Has images |
| `has:videos` | `tutorial has:videos` | Has videos |
| `has:links` | `news has:links` | Contains URLs |
| `has:hashtags` | `crypto has:hashtags` | Contains hashtags |
| `has:mentions` | `discussion has:mentions` | Contains mentions |

### Engagement Operators

| Operator | Example | Description |
|----------|---------|-------------|
| `min_retweets:` | `bitcoin min_retweets:100` | Minimum retweets |
| `min_faves:` | `crypto min_faves:500` | Minimum likes |
| `min_replies:` | `news min_replies:50` | Minimum replies |

### Location & Language

| Operator | Example | Description |
|----------|---------|-------------|
| `lang:` | `bitcoin lang:en` | Tweet language |
| `place:` | `concert place:NYC` | Place name |
| `place_country:` | `news place_country:US` | Country code |

### Time Operators (for `search_all_tweets`)

| Operator | Example | Description |
|----------|---------|-------------|
| `until:` | `bitcoin until:2024-01-01` | Before date |
| `since:` | `bitcoin since:2023-01-01` | After date |

### Complex Query Examples

```python
# High-engagement crypto tweets with images
query = "#Bitcoin has:images min_faves:100 -is:retweet lang:en"

# News from specific accounts
query = "(from:Reuters OR from:AP) crypto -is:retweet"

# Discussions mentioning multiple terms
query = "(ethereum OR solana) DeFi -scam min_replies:10"

# Recent announcements with links
query = "announcement has:links from:VitalikButerin"
```

---

## Rate Limits

### Tier 1 (Default)

- **50 calls per 5 minutes** (free with GAME_API_KEY)
- Suitable for most use cases
- No approval required

### Tier 2 (Elevated)

- **Higher rate limits** (contact Virtuals for specifics)
- Requires approval from Virtuals team via Discord
- For high-volume applications

### Handling Rate Limits

```python
# Enable automatic rate limit handling
client = Client(
    game_twitter_access_token=token,
    wait_on_rate_limit=True                       # Auto-wait when rate limited
)
```

---

## Error Handling

```python
from virtuals_tweepy import TweepyException, BadRequest, Unauthorized, Forbidden, NotFound, TooManyRequests

try:
    response = client.create_tweet(text="Hello!")
except BadRequest as e:
    print(f"Bad request: {e}")                    # 400 - Invalid parameters
except Unauthorized as e:
    print(f"Unauthorized: {e}")                   # 401 - Auth failed
except Forbidden as e:
    print(f"Forbidden: {e}")                      # 403 - Not allowed
except NotFound as e:
    print(f"Not found: {e}")                      # 404 - Resource missing
except TooManyRequests as e:
    print(f"Rate limited: {e}")                   # 429 - Too many requests
except TweepyException as e:
    print(f"Twitter API error: {e}")              # Generic API error
```

---

## Examples

### Example 1: Search and Analyze Tweets

```python
import os
from dotenv import load_dotenv
from virtuals_tweepy import Client

load_dotenv()
client = Client(game_twitter_access_token=os.environ.get("GAME_TWITTER_ACCESS_TOKEN"))

# Search for trending topic
response = client.search_recent_tweets(
    query="#AI lang:en -is:retweet min_faves:50",
    max_results=100,
    tweet_fields=["created_at", "public_metrics", "author_id"],
    expansions=["author_id"],
    user_fields=["username", "verified", "public_metrics"]
)

# Build user lookup dict
users = {u.id: u for u in response.includes.get("users", [])}

# Analyze results
for tweet in response.data:
    author = users.get(tweet.author_id)
    metrics = tweet.public_metrics
    print(f"@{author.username} ({author.public_metrics['followers_count']} followers)")
    print(f"  {tweet.text[:100]}...")
    print(f"  Likes: {metrics['like_count']}, RTs: {metrics['retweet_count']}")
    print()
```

### Example 2: Monitor Mentions and Auto-Reply

```python
import os
from dotenv import load_dotenv
from virtuals_tweepy import Client

load_dotenv()
client = Client(game_twitter_access_token=os.environ.get("GAME_TWITTER_ACCESS_TOKEN"))

# Get my user ID
me = client.get_me()
my_id = me.data.id

# Get recent mentions
mentions = client.get_users_mentions(
    id=my_id,
    max_results=10,
    tweet_fields=["created_at", "author_id", "conversation_id"]
)

# Reply to each mention
for mention in mentions.data or []:
    # Create reply
    client.create_tweet(
        text=f"Thanks for the mention! I'll get back to you soon.",
        in_reply_to_tweet_id=mention.id
    )
    print(f"Replied to tweet {mention.id}")
```

### Example 3: Post Tweet with Media

```python
import os
import requests
from dotenv import load_dotenv
from virtuals_tweepy import Client

load_dotenv()
client = Client(game_twitter_access_token=os.environ.get("GAME_TWITTER_ACCESS_TOKEN"))

# Upload from local file
with open("chart.png", "rb") as f:
    media_id = client.upload_media(media=f.read(), media_type="image/png")

# Or upload from URL
image_url = "https://example.com/image.png"
image_data = requests.get(image_url).content
media_id = client.upload_media(media=image_data, media_type="image/png")

# Post tweet with media
response = client.create_tweet(
    text="Check out this chart!",
    media_ids=[media_id]
)
print(f"Posted: https://twitter.com/i/status/{response.data['id']}")
```

### Example 4: Track User Activity

```python
import os
from dotenv import load_dotenv
from virtuals_tweepy import Client

load_dotenv()
client = Client(game_twitter_access_token=os.environ.get("GAME_TWITTER_ACCESS_TOKEN"))

# Get user
target = client.get_user(
    username="VitalikButerin",
    user_fields=["public_metrics", "created_at", "description"]
)

print(f"User: @{target.data.username}")
print(f"Followers: {target.data.public_metrics['followers_count']:,}")
print(f"Following: {target.data.public_metrics['following_count']:,}")
print(f"Tweets: {target.data.public_metrics['tweet_count']:,}")

# Get their recent tweets
tweets = client.get_users_tweets(
    id=target.data.id,
    max_results=10,
    tweet_fields=["created_at", "public_metrics"],
    exclude=["retweets"]
)

print(f"\nRecent tweets:")
for tweet in tweets.data:
    metrics = tweet.public_metrics
    print(f"  [{metrics['like_count']} likes] {tweet.text[:80]}...")
```

### Example 5: Create a Poll

```python
import os
from dotenv import load_dotenv
from virtuals_tweepy import Client

load_dotenv()
client = Client(game_twitter_access_token=os.environ.get("GAME_TWITTER_ACCESS_TOKEN"))

response = client.create_tweet(
    text="What's your favorite blockchain?",
    poll_options=["Ethereum", "Solana", "Bitcoin", "Other"],
    poll_duration_minutes=1440                    # 24 hours
)
print(f"Poll posted: https://twitter.com/i/status/{response.data['id']}")
```

---

## Terms of Service

Before using this plugin, you must agree to:
- [Virtuals Terms of Use](https://virtuals.io/terms)
- GAME X API Terms

The plugin is intended for legitimate use cases. Avoid:
- Spam or automated bulk posting
- Harassment or abuse
- Circumventing Twitter's terms of service

---

## Resources

- [Virtuals GAME Console](https://console.game.virtuals.io/)
- [game-python GitHub](https://github.com/game-by-virtuals/game-python)
- [virtuals-tweepy on PyPI](https://pypi.org/project/virtuals-tweepy/)
- [Tweepy Documentation](https://docs.tweepy.org/) (API compatible)
- [Twitter API v2 Documentation](https://developer.twitter.com/en/docs/twitter-api)
