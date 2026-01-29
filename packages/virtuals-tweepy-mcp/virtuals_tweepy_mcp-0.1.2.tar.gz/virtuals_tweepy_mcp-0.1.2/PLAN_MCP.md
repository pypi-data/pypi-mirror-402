# MCP Server Implementation Plan

This document outlines the design for an MCP server that exposes the full GAME SDK Twitter API.

## Overview

| Aspect   | Decision                                                    |
| -------- | ----------------------------------------------------------- |
| Scope    | Full GAME SDK API (37 tools)                                |
| Auth     | Environment variable (`GAME_TWITTER_ACCESS_TOKEN`)          |
| Naming   | Flat namespace (`get_tweet`, `search_tweets`, etc.)         |
| Features | Tools only (no resources/prompts for v1)                    |
| Response | Simplified JSON with consistent shapes                      |
| Monitor  | Excluded (clients poll with `get_user_tweets` + `since_id`) |

---

## Project Structure

```
src/virtuals_observer/
├── cli.py            # Existing CLI (refactor to use twitter_api.py)
├── mcp_server.py     # New - MCP server with 37 tools
└── twitter_api.py    # New - Shared API wrapper with simplified responses
```

### Dependencies

Add to `pyproject.toml`:

```toml
dependencies = [
    # ... existing deps ...
    "mcp>=1.0.0",
    "httpx>=0.27.0",
]

[project.scripts]
vobs = "virtuals_observer.cli:main"
vobs-mcp = "virtuals_observer.mcp_server:main"
```

### Running the Server

```bash
# Direct execution
uv run vobs-mcp

# Via MCP client configuration (e.g., Claude Desktop)
{
  "mcpServers": {
    "twitter": {
      "command": "uv",
      "args": ["run", "--directory", "/path/to/virtuals-observer", "vobs-mcp"],
      "env": {"GAME_TWITTER_ACCESS_TOKEN": "apx-..."}
    }
  }
}
```

---

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    MCP Client (Claude, etc.)            │
└─────────────────────────┬───────────────────────────────┘
                          │ stdio (JSON-RPC)
┌─────────────────────────▼───────────────────────────────┐
│                   mcp_server.py                         │
│  - FastMCP Server with @mcp.tool decorators             │
│  - Pydantic parameter validation                        │
│  - Error handling wrapper                               │
└─────────────────────────┬───────────────────────────────┘
                          │
┌─────────────────────────▼───────────────────────────────┐
│                   twitter_api.py                        │
│  - TwitterAPI class wrapping virtuals_tweepy.Client     │
│  - Response simplification functions                    │
│  - Shared by CLI and MCP server                         │
└─────────────────────────┬───────────────────────────────┘
                          │
┌─────────────────────────▼───────────────────────────────┐
│              virtuals_tweepy.Client                     │
│              (GAME SDK / Twitter API v2)                │
└─────────────────────────────────────────────────────────┘
```

---

## Complete Tool List (37 tools)

### Tweet Operations (7 tools)

| Tool           | Description                                            |
| -------------- | ------------------------------------------------------ |
| `create_tweet` | Post a new tweet with optional media, polls, replies   |
| `delete_tweet` | Delete a tweet by ID                                   |
| `get_tweet`    | Fetch a single tweet with full details                 |
| `get_tweets`   | Fetch multiple tweets by IDs (batch, up to 100)        |
| `get_thread`   | Fetch entire thread from any tweet in the conversation |
| `get_article`  | Extract full content from X Article (long-form post)   |
| `upload_media` | Upload image/video and get media_id for attachment     |

### Search (3 tools)

| Tool                | Description                                          |
| ------------------- | ---------------------------------------------------- |
| `search_tweets`     | Search recent tweets (last 7 days)                   |
| `search_all_tweets` | Search full tweet history (elevated access required) |
| `count_tweets`      | Count tweets matching query over time                |

### Timelines (3 tools)

| Tool                | Description                     |
| ------------------- | ------------------------------- |
| `get_home_timeline` | Get your home feed              |
| `get_user_tweets`   | Get tweets from a specific user |
| `get_mentions`      | Get tweets mentioning you       |

### User Lookup (5 tools)

| Tool            | Description                            |
| --------------- | -------------------------------------- |
| `get_me`        | Get your own profile                   |
| `get_user`      | Get a user's profile by username or ID |
| `get_users`     | Get multiple users (batch)             |
| `get_followers` | Get a user's followers                 |
| `get_following` | Get accounts a user follows            |

### Social Actions (8 tools)

| Tool          | Description        |
| ------------- | ------------------ |
| `follow`      | Follow a user      |
| `unfollow`    | Unfollow a user    |
| `mute`        | Mute a user        |
| `unmute`      | Unmute a user      |
| `block`       | Block a user       |
| `unblock`     | Unblock a user     |
| `get_muted`   | List muted users   |
| `get_blocked` | List blocked users |

### Engagement (9 tools)

| Tool               | Description                 |
| ------------------ | --------------------------- |
| `like`             | Like a tweet                |
| `unlike`           | Unlike a tweet              |
| `retweet`          | Retweet a tweet             |
| `unretweet`        | Undo a retweet              |
| `bookmark`         | Bookmark a tweet            |
| `remove_bookmark`  | Remove bookmark             |
| `get_bookmarks`    | List your bookmarks         |
| `get_liking_users` | Get users who liked a tweet |
| `get_retweeters`   | Get users who retweeted     |

### Replies (2 tools)

| Tool           | Description                |
| -------------- | -------------------------- |
| `hide_reply`   | Hide a reply to your tweet |
| `unhide_reply` | Unhide a reply             |

---

## Response Formats

### Tweet Object

```json
{
  "id": "1234567890",
  "text": "Hello world!",
  "username": "elonmusk",
  "name": "Elon Musk",
  "created_at": "2024-01-15T10:30:00Z",
  "url": "https://twitter.com/elonmusk/status/1234567890",
  "likes": 5420,
  "retweets": 892,
  "replies": 341,
  "quotes": 56,
  "bookmarks": 120,
  "impressions": 1250000,
  "media": [
    {"type": "image", "url": "https://pbs.twimg.com/..."},
    {"type": "video", "url": "https://video.twimg.com/...", "duration_ms": 15000}
  ],
  "urls": [
    {"expanded_url": "https://example.com", "type": "link"}
  ],
  "is_reply": false,
  "is_retweet": false,
  "is_thread": false,
  "has_article": false,
  "conversation_id": "1234567890"
}
```

**Special flags:**
- `is_thread: true` - Tweet is part of a thread (self-reply or text contains 1/, 🧵, etc.)
- `has_article: true` - Tweet contains an X Article; call `get_article` for full content

### User Object

```json
{
  "id": "44196397",
  "username": "elonmusk",
  "name": "Elon Musk",
  "bio": "Mars & Cars",
  "location": "Austin, Texas",
  "url": "https://tesla.com",
  "followers": 180000000,
  "following": 500,
  "tweets": 30000,
  "listed": 120000,
  "verified": true,
  "created_at": "2009-06-02",
  "profile_url": "https://twitter.com/elonmusk"
}
```

### List Response (search, timelines, etc.)

```json
{
  "tweets": [...],
  "count": 10,
  "next_token": "abc123..."
}
```

`next_token` is for pagination. Pass it as `pagination_token` in next request. `null` when no more results.

### Action Response (like, follow, etc.)

```json
{
  "success": true,
  "action": "like",
  "tweet_id": "1234567890"
}
```

### Error Response

```json
{
  "error": true,
  "code": "rate_limited",
  "message": "Rate limit exceeded. Try again in 5 minutes."
}
```

---

## Tool Specifications

### get_tweet

**Description:**
```
Fetch a single tweet by ID or URL. Returns tweet content, metrics, media, and metadata.

Use this for: Quick tweet lookups, getting metrics, checking if a tweet exists.

Note: If the tweet contains an X Article (long-form post), only the preview text is returned.
Check `has_article: true` in response, then call `get_article` for full content.

If `is_thread: true`, consider calling `get_thread` to fetch the full thread.
```

**Parameters:**
| Name    | Type   | Required | Description                                                                         |
| ------- | ------ | -------- | ----------------------------------------------------------------------------------- |
| `tweet` | string | yes      | Tweet ID or full URL (e.g., "1234567890" or "https://x.com/user/status/1234567890") |

---

### get_article

**Description:**
```
Extract full content from an X Article (long-form post). Uses browser automation to render the article.

WHEN TO USE:
- After `get_tweet` returns `has_article: true`
- When user asks for "full article", "long post content", or "read the article"
- When tweet text appears truncated with "Show more" or article link

WHEN NOT TO USE:
- For regular tweets (will return null)
- When you only need tweet metrics or basic info (use `get_tweet`)
- For speed-critical operations (this tool is slower, ~5-10 seconds)

Requires: Tweet URL or ID of an article tweet.
```

**Parameters:**
| Name    | Type   | Required | Description                             |
| ------- | ------ | -------- | --------------------------------------- |
| `tweet` | string | yes      | Tweet ID or URL containing an X Article |

**Response:**
```json
{
  "title": "Article Title",
  "content": "Full article text with paragraphs...",
  "sections": ["Section 1", "Section 2"],
  "images": ["https://..."],
  "tweet_id": "1234567890",
  "author": "username"
}
```

Returns `null` if tweet is not an article.

---

### get_thread

**Description:**
```
Fetch an entire Twitter thread (series of connected tweets by the same author).

Given any tweet in a thread, retrieves all tweets from the original author in that conversation, sorted chronologically.

Use this when:
- User asks for "the full thread", "all tweets in thread", or "thread starting with..."
- `get_tweet` returns `is_thread: true`
- Tweet text starts with "1/", "🧵", or indicates it's part of a series
- You need context from earlier/later tweets in a conversation

Returns only the thread author's tweets by default, not replies from others.
```

**Parameters:**
| Name              | Type    | Required | Description                                  |
| ----------------- | ------- | -------- | -------------------------------------------- |
| `tweet`           | string  | yes      | Any tweet ID or URL from the thread          |
| `include_replies` | boolean | no       | Include replies from others (default: false) |

**Response:**
```json
{
  "thread_id": "1234567890",
  "author": {
    "username": "elonmusk",
    "name": "Elon Musk"
  },
  "tweets": [
    {"position": 1, "id": "1234567890", "text": "1/ Starting a thread..."},
    {"position": 2, "id": "1234567891", "text": "2/ More context..."},
    {"position": 3, "id": "1234567892", "text": "3/ Final thoughts..."}
  ],
  "count": 3
}
```

---

### search_tweets

**Description:**
```
Search for tweets from the last 7 days using Twitter's search syntax.

Supports operators:
- Keywords: bitcoin, "exact phrase"
- Users: from:elonmusk, to:user, @mention
- Filters: -is:retweet, has:media, has:links, lang:en
- Engagement: min_faves:100, min_retweets:50
- Combine with AND, OR, -exclude

Examples:
- "bitcoin -is:retweet lang:en" (English tweets about bitcoin, no RTs)
- "from:VitalikButerin ethereum" (Vitalik's tweets about ethereum)
- "#AI has:images min_faves:500" (Popular AI tweets with images)

For tweets older than 7 days, use `search_all_tweets` (requires elevated access).
```

**Parameters:**
| Name               | Type    | Required | Description                                |
| ------------------ | ------- | -------- | ------------------------------------------ |
| `query`            | string  | yes      | Search query with Twitter syntax           |
| `max_results`      | integer | no       | Results per page, 10-100 (default: 10)     |
| `pagination_token` | string  | no       | Token from previous response for next page |

---

### create_tweet

**Description:**
```
Post a new tweet. Can include text, media, polls, or be a reply/quote.

Character limit: 280 (or 25,000 for X Premium subscribers).

For media attachments: First call `upload_media` to get a media_id, then pass it here.
For replies: Set `reply_to` to the tweet ID you're replying to.
For quotes: Set `quote_tweet_id` to the tweet you're quoting.
```

**Parameters:**
| Name                    | Type    | Required | Description                                  |
| ----------------------- | ------- | -------- | -------------------------------------------- |
| `text`                  | string  | yes      | Tweet content (max 280 chars)                |
| `reply_to`              | string  | no       | Tweet ID to reply to                         |
| `quote_tweet_id`        | string  | no       | Tweet ID to quote                            |
| `media_ids`             | array   | no       | List of media IDs from `upload_media`        |
| `poll_options`          | array   | no       | Poll choices (2-4 strings)                   |
| `poll_duration_minutes` | integer | no       | Poll duration: 5-10080 (default: 1440 = 24h) |

---

### upload_media

**Description:**
```
Upload an image or video file to Twitter and get a media_id for attachment to tweets.

Workflow:
1. Call `upload_media` with file path or URL
2. Receive `media_id` in response
3. Pass `media_id` to `create_tweet` in `media_ids` array

Supported formats:
- Images: PNG, JPEG, GIF, WEBP (max 5MB)
- Videos: MP4 (max 512MB, 140 seconds)
```

**Parameters:**
| Name         | Type   | Required | Description                               |
| ------------ | ------ | -------- | ----------------------------------------- |
| `file_path`  | string | no       | Local file path to upload                 |
| `url`        | string | no       | URL of image/video to upload              |
| `media_type` | string | no       | MIME type (auto-detected if not provided) |

One of `file_path` or `url` is required.

---

### get_me

**Description:**
```
Get your own Twitter profile information.

Use this to:
- Verify authentication is working
- Get your user ID for other API calls
- Check your follower/following counts
```

**Parameters:** None

---

### get_user

**Description:**
```
Get a Twitter user's profile by username or user ID.

Use this to:
- Look up user information before fetching their tweets
- Get user ID (required for some API calls)
- Check follower counts, bio, verification status
```

**Parameters:**
| Name       | Type   | Required | Description                                 |
| ---------- | ------ | -------- | ------------------------------------------- |
| `username` | string | no       | Twitter handle without @ (e.g., "elonmusk") |
| `user_id`  | string | no       | Twitter user ID                             |

One of `username` or `user_id` is required.

---

### get_user_tweets

**Description:**
```
Get recent tweets from a specific user.

Use this to:
- Monitor what someone has been posting
- Fetch tweets for analysis
- Poll for new tweets (use `since_id` parameter)

Note: For thread detection, check `is_thread` flag on returned tweets.
```

**Parameters:**
| Name               | Type    | Required | Description                            |
| ------------------ | ------- | -------- | -------------------------------------- |
| `username`         | string  | no       | Twitter handle (e.g., "elonmusk")      |
| `user_id`          | string  | no       | Twitter user ID                        |
| `max_results`      | integer | no       | Results to return, 5-100 (default: 10) |
| `since_id`         | string  | no       | Only return tweets newer than this ID  |
| `exclude_retweets` | boolean | no       | Exclude retweets (default: false)      |
| `exclude_replies`  | boolean | no       | Exclude replies (default: false)       |
| `pagination_token` | string  | no       | Token for next page                    |

One of `username` or `user_id` is required.

---

### get_home_timeline

**Description:**
```
Get your home timeline - tweets from accounts you follow.

Note: Results are algorithmic (not strictly chronological).
```

**Parameters:**
| Name               | Type    | Required | Description                            |
| ------------------ | ------- | -------- | -------------------------------------- |
| `max_results`      | integer | no       | Results to return, 1-100 (default: 10) |
| `pagination_token` | string  | no       | Token for next page                    |

---

### get_mentions

**Description:**
```
Get tweets that mention you (@username).

Use this to:
- Check for replies to your tweets
- Monitor mentions of your account
- Build reply/engagement workflows
```

**Parameters:**
| Name               | Type    | Required | Description                             |
| ------------------ | ------- | -------- | --------------------------------------- |
| `max_results`      | integer | no       | Results to return, 5-100 (default: 10)  |
| `since_id`         | string  | no       | Only return mentions newer than this ID |
| `pagination_token` | string  | no       | Token for next page                     |

---

### like

**Description:**
```
Like a tweet.
```

**Parameters:**
| Name       | Type   | Required | Description         |
| ---------- | ------ | -------- | ------------------- |
| `tweet_id` | string | yes      | ID of tweet to like |

---

### unlike

**Description:**
```
Remove your like from a tweet.
```

**Parameters:**
| Name       | Type   | Required | Description           |
| ---------- | ------ | -------- | --------------------- |
| `tweet_id` | string | yes      | ID of tweet to unlike |

---

### retweet

**Description:**
```
Retweet a tweet.
```

**Parameters:**
| Name       | Type   | Required | Description            |
| ---------- | ------ | -------- | ---------------------- |
| `tweet_id` | string | yes      | ID of tweet to retweet |

---

### unretweet

**Description:**
```
Undo a retweet.
```

**Parameters:**
| Name       | Type   | Required | Description              |
| ---------- | ------ | -------- | ------------------------ |
| `tweet_id` | string | yes      | ID of tweet to unretweet |

---

### bookmark

**Description:**
```
Bookmark a tweet for later.
```

**Parameters:**
| Name       | Type   | Required | Description             |
| ---------- | ------ | -------- | ----------------------- |
| `tweet_id` | string | yes      | ID of tweet to bookmark |

---

### remove_bookmark

**Description:**
```
Remove a tweet from your bookmarks.
```

**Parameters:**
| Name       | Type   | Required | Description                          |
| ---------- | ------ | -------- | ------------------------------------ |
| `tweet_id` | string | yes      | ID of tweet to remove from bookmarks |

---

### get_bookmarks

**Description:**
```
Get your bookmarked tweets.
```

**Parameters:**
| Name               | Type    | Required | Description                            |
| ------------------ | ------- | -------- | -------------------------------------- |
| `max_results`      | integer | no       | Results to return, 1-100 (default: 10) |
| `pagination_token` | string  | no       | Token for next page                    |

---

### follow

**Description:**
```
Follow a Twitter user.
```

**Parameters:**
| Name       | Type   | Required | Description              |
| ---------- | ------ | -------- | ------------------------ |
| `username` | string | no       | Twitter handle to follow |
| `user_id`  | string | no       | User ID to follow        |

One of `username` or `user_id` is required.

---

### unfollow

**Description:**
```
Unfollow a Twitter user.
```

**Parameters:**
| Name       | Type   | Required | Description                |
| ---------- | ------ | -------- | -------------------------- |
| `username` | string | no       | Twitter handle to unfollow |
| `user_id`  | string | no       | User ID to unfollow        |

One of `username` or `user_id` is required.

---

### mute

**Description:**
```
Mute a Twitter user. Their tweets won't appear in your timeline.
```

**Parameters:**
| Name       | Type   | Required | Description            |
| ---------- | ------ | -------- | ---------------------- |
| `username` | string | no       | Twitter handle to mute |
| `user_id`  | string | no       | User ID to mute        |

One of `username` or `user_id` is required.

---

### unmute

**Description:**
```
Unmute a Twitter user.
```

**Parameters:**
| Name       | Type   | Required | Description              |
| ---------- | ------ | -------- | ------------------------ |
| `username` | string | no       | Twitter handle to unmute |
| `user_id`  | string | no       | User ID to unmute        |

One of `username` or `user_id` is required.

---

### block

**Description:**
```
Block a Twitter user. They cannot see your tweets or interact with you.
```

**Parameters:**
| Name       | Type   | Required | Description             |
| ---------- | ------ | -------- | ----------------------- |
| `username` | string | no       | Twitter handle to block |
| `user_id`  | string | no       | User ID to block        |

One of `username` or `user_id` is required.

---

### unblock

**Description:**
```
Unblock a Twitter user.
```

**Parameters:**
| Name       | Type   | Required | Description               |
| ---------- | ------ | -------- | ------------------------- |
| `username` | string | no       | Twitter handle to unblock |
| `user_id`  | string | no       | User ID to unblock        |

One of `username` or `user_id` is required.

---

### get_followers

**Description:**
```
Get a user's followers.
```

**Parameters:**
| Name               | Type    | Required | Description                              |
| ------------------ | ------- | -------- | ---------------------------------------- |
| `username`         | string  | no       | Twitter handle                           |
| `user_id`          | string  | no       | User ID                                  |
| `max_results`      | integer | no       | Results to return, 1-1000 (default: 100) |
| `pagination_token` | string  | no       | Token for next page                      |

One of `username` or `user_id` is required.

---

### get_following

**Description:**
```
Get accounts a user follows.
```

**Parameters:**
| Name               | Type    | Required | Description                              |
| ------------------ | ------- | -------- | ---------------------------------------- |
| `username`         | string  | no       | Twitter handle                           |
| `user_id`          | string  | no       | User ID                                  |
| `max_results`      | integer | no       | Results to return, 1-1000 (default: 100) |
| `pagination_token` | string  | no       | Token for next page                      |

One of `username` or `user_id` is required.

---

### get_muted

**Description:**
```
Get list of users you have muted.
```

**Parameters:**
| Name               | Type    | Required | Description                              |
| ------------------ | ------- | -------- | ---------------------------------------- |
| `max_results`      | integer | no       | Results to return, 1-1000 (default: 100) |
| `pagination_token` | string  | no       | Token for next page                      |

---

### get_blocked

**Description:**
```
Get list of users you have blocked.
```

**Parameters:**
| Name               | Type    | Required | Description                              |
| ------------------ | ------- | -------- | ---------------------------------------- |
| `max_results`      | integer | no       | Results to return, 1-1000 (default: 100) |
| `pagination_token` | string  | no       | Token for next page                      |

---

### get_liking_users

**Description:**
```
Get users who liked a specific tweet.
```

**Parameters:**
| Name               | Type    | Required | Description                             |
| ------------------ | ------- | -------- | --------------------------------------- |
| `tweet_id`         | string  | yes      | ID of the tweet                         |
| `max_results`      | integer | no       | Results to return, 1-100 (default: 100) |
| `pagination_token` | string  | no       | Token for next page                     |

---

### get_retweeters

**Description:**
```
Get users who retweeted a specific tweet.
```

**Parameters:**
| Name               | Type    | Required | Description                             |
| ------------------ | ------- | -------- | --------------------------------------- |
| `tweet_id`         | string  | yes      | ID of the tweet                         |
| `max_results`      | integer | no       | Results to return, 1-100 (default: 100) |
| `pagination_token` | string  | no       | Token for next page                     |

---

### hide_reply

**Description:**
```
Hide a reply to one of your tweets. The reply will be collapsed and shown as "hidden".
```

**Parameters:**
| Name       | Type   | Required | Description             |
| ---------- | ------ | -------- | ----------------------- |
| `tweet_id` | string | yes      | ID of the reply to hide |

---

### unhide_reply

**Description:**
```
Unhide a previously hidden reply.
```

**Parameters:**
| Name       | Type   | Required | Description               |
| ---------- | ------ | -------- | ------------------------- |
| `tweet_id` | string | yes      | ID of the reply to unhide |

---

### delete_tweet

**Description:**
```
Delete one of your tweets.
```

**Parameters:**
| Name       | Type   | Required | Description                |
| ---------- | ------ | -------- | -------------------------- |
| `tweet_id` | string | yes      | ID of your tweet to delete |

---

### get_tweets

**Description:**
```
Fetch multiple tweets by their IDs in a single request (batch lookup).

Use this when you have a list of tweet IDs and want to fetch them efficiently.
Maximum 100 tweets per request.
```

**Parameters:**
| Name        | Type  | Required | Description                 |
| ----------- | ----- | -------- | --------------------------- |
| `tweet_ids` | array | yes      | List of tweet IDs (max 100) |

---

### get_users

**Description:**
```
Fetch multiple users by username or ID in a single request (batch lookup).

Use this when you need to look up several users efficiently.
Maximum 100 users per request.
```

**Parameters:**
| Name        | Type  | Required | Description                       |
| ----------- | ----- | -------- | --------------------------------- |
| `usernames` | array | no       | List of Twitter handles (max 100) |
| `user_ids`  | array | no       | List of user IDs (max 100)        |

One of `usernames` or `user_ids` is required.

---

### search_all_tweets

**Description:**
```
Search the full archive of public tweets (not just last 7 days).

Requires elevated API access. Same query syntax as `search_tweets`.

Additional time-based parameters allow searching specific date ranges.
```

**Parameters:**
| Name               | Type    | Required | Description                            |
| ------------------ | ------- | -------- | -------------------------------------- |
| `query`            | string  | yes      | Search query with Twitter syntax       |
| `max_results`      | integer | no       | Results per page, 10-500 (default: 10) |
| `start_time`       | string  | no       | ISO 8601 timestamp for range start     |
| `end_time`         | string  | no       | ISO 8601 timestamp for range end       |
| `pagination_token` | string  | no       | Token for next page                    |

---

### count_tweets

**Description:**
```
Count tweets matching a search query over time.

Returns counts grouped by time granularity (minute, hour, or day).
Useful for analyzing tweet volume trends.
```

**Parameters:**
| Name          | Type   | Required | Description                                           |
| ------------- | ------ | -------- | ----------------------------------------------------- |
| `query`       | string | yes      | Search query with Twitter syntax                      |
| `granularity` | string | no       | Time bucket: "minute", "hour", "day" (default: "day") |
| `start_time`  | string | no       | ISO 8601 timestamp for range start                    |
| `end_time`    | string | no       | ISO 8601 timestamp for range end                      |

---

## Testing with MCP Inspector

**Installation & Running:**
```bash
npx @modelcontextprotocol/inspector uv run vobs-mcp
```

**Testing checklist:**

| Test                     | What to verify                                    |
| ------------------------ | ------------------------------------------------- |
| Server startup           | Connects without errors, all 37 tools listed      |
| `get_me`                 | Returns your profile (validates auth working)     |
| `get_tweet` with URL     | Parses URL correctly, returns simplified response |
| `get_tweet` with article | `has_article: true` flag present                  |
| `get_tweet` with thread  | `is_thread: true` flag present                    |
| `get_article`            | Playwright launches, extracts content             |
| `get_thread`             | Returns tweets in correct chronological order     |
| `search_tweets`          | Query operators work, pagination token returned   |
| `create_tweet`           | Posts successfully (use test account!)            |
| Invalid params           | Returns structured error, not crash               |
| Missing auth             | Clear error message about missing token           |
| Rate limit               | Graceful error with retry guidance                |

---

## Implementation Steps

1. **Create `twitter_api.py`**
   - Extract `get_client()` from cli.py
   - Create `TwitterAPI` class with all methods
   - Implement response simplification for each endpoint
   - Add `is_thread` and `has_article` detection logic

2. **Create `mcp_server.py`**
   - Set up FastMCP server
   - Register all 37 tools with Pydantic models
   - Implement error handling wrapper
   - Add lazy client initialization

3. **Refactor `cli.py`**
   - Import shared code from `twitter_api.py`
   - Remove duplicated response formatting

4. **Update `pyproject.toml`**
   - Add mcp and httpx dependencies
   - Add vobs-mcp entry point

5. **Test with MCP Inspector**
   - Verify all tools work
   - Test error cases
   - Document any edge cases

---

## Error Codes

| Code                | HTTP | Description                                              |
| ------------------- | ---- | -------------------------------------------------------- |
| `unauthorized`      | 401  | Invalid or missing access token                          |
| `forbidden`         | 403  | Action not allowed (e.g., deleting someone else's tweet) |
| `not_found`         | 404  | Tweet or user not found                                  |
| `rate_limited`      | 429  | Too many requests, retry after delay                     |
| `invalid_params`    | 400  | Invalid or missing parameters                            |
| `server_error`      | 500  | Twitter API or server error                              |
| `article_not_found` | -    | Tweet exists but is not an article                       |
| `playwright_error`  | -    | Browser automation failed                                |
