"""MCP server exposing the full GAME SDK Twitter API.

Run with:
    uv run vobs-mcp

Or configure in Claude Desktop:
    {
        "mcpServers": {
            "twitter": {
                "command": "uv",
                "args": ["run", "--directory", "/path/to/virtuals-observer", "vobs-mcp"],
                "env": {"GAME_TWITTER_ACCESS_TOKEN": "apx-..."}
            }
        }
    }
"""

from mcp.server.fastmcp import FastMCP

from virtuals_observer.twitter_api import TwitterAPI, TwitterAPIError

# Initialize MCP server
mcp = FastMCP("Twitter (GAME SDK)", json_response=True)

# Lazy-initialized API client
_api: TwitterAPI | None = None


def get_api() -> TwitterAPI:
    """Get or create the Twitter API client."""
    global _api
    if _api is None:
        _api = TwitterAPI()
    return _api


def handle_error(e: Exception) -> dict:
    """Convert exceptions to error responses."""
    if isinstance(e, TwitterAPIError):
        return e.to_dict()
    return {"error": True, "code": "server_error", "message": str(e)}


# =============================================================================
# Tweet Operations (7 tools)
# =============================================================================


@mcp.tool()
def get_tweet(tweet: str) -> dict:
    """Fetch a single tweet by ID or URL. Returns tweet content, metrics, media, and metadata.

    Use this for: Quick tweet lookups, getting metrics, checking if a tweet exists.

    Note: If the tweet contains an X Article (long-form post), only the preview text is returned.
    Check `has_article: true` in response, then call `get_article` for full content.

    If `is_thread: true`, consider calling `get_thread` to fetch the full thread.

    Args:
        tweet: Tweet ID or full URL (e.g., "1234567890" or "https://x.com/user/status/1234567890")
    """
    try:
        return get_api().get_tweet(tweet)
    except Exception as e:
        return handle_error(e)


@mcp.tool()
def get_tweets(tweet_ids: list[str]) -> dict:
    """Fetch multiple tweets by their IDs in a single request (batch lookup).

    Use this when you have a list of tweet IDs and want to fetch them efficiently.
    Maximum 100 tweets per request.

    Args:
        tweet_ids: List of tweet IDs (max 100)
    """
    try:
        return get_api().get_tweets(tweet_ids)
    except Exception as e:
        return handle_error(e)


@mcp.tool()
def create_tweet(
    text: str,
    reply_to: str | None = None,
    quote_tweet_id: str | None = None,
    media_ids: list[str] | None = None,
    poll_options: list[str] | None = None,
    poll_duration_minutes: int | None = None,
) -> dict:
    """Post a new tweet. Can include text, media, polls, or be a reply/quote.

    Character limit: 280 (or 25,000 for X Premium subscribers).

    For media attachments: First call `upload_media` to get a media_id, then pass it here.
    For replies: Set `reply_to` to the tweet ID you're replying to.
    For quotes: Set `quote_tweet_id` to the tweet you're quoting.

    Args:
        text: Tweet content (max 280 chars)
        reply_to: Tweet ID to reply to
        quote_tweet_id: Tweet ID to quote
        media_ids: List of media IDs from `upload_media`
        poll_options: Poll choices (2-4 strings)
        poll_duration_minutes: Poll duration: 5-10080 (default: 1440 = 24h)
    """
    try:
        return get_api().create_tweet(
            text=text,
            reply_to=reply_to,
            quote_tweet_id=quote_tweet_id,
            media_ids=media_ids,
            poll_options=poll_options,
            poll_duration_minutes=poll_duration_minutes,
        )
    except Exception as e:
        return handle_error(e)


@mcp.tool()
def delete_tweet(tweet_id: str) -> dict:
    """Delete one of your tweets.

    Args:
        tweet_id: ID of your tweet to delete
    """
    try:
        return get_api().delete_tweet(tweet_id)
    except Exception as e:
        return handle_error(e)


@mcp.tool()
def get_thread(tweet: str, include_replies: bool = False) -> dict:
    """Fetch an entire Twitter thread (series of connected tweets by the same author).

    Given any tweet in a thread, retrieves all tweets from the original author in that conversation, sorted chronologically.

    Use this when:
    - User asks for "the full thread", "all tweets in thread", or "thread starting with..."
    - `get_tweet` returns `is_thread: true`
    - Tweet text starts with "1/", "🧵", or indicates it's part of a series
    - You need context from earlier/later tweets in a conversation

    Returns only the thread author's tweets by default, not replies from others.

    Args:
        tweet: Any tweet ID or URL from the thread
        include_replies: Include replies from others (default: false)
    """
    try:
        return get_api().get_thread(tweet, include_replies)
    except Exception as e:
        return handle_error(e)


@mcp.tool()
async def get_article(tweet: str) -> dict:
    """Extract full content from an X Article (long-form post). Uses browser automation to render the article.

    WHEN TO USE:
    - After `get_tweet` returns `has_article: true`
    - When user asks for "full article", "long post content", or "read the article"
    - When tweet text appears truncated with "Show more" or article link

    WHEN NOT TO USE:
    - For regular tweets (will return null)
    - When you only need tweet metrics or basic info (use `get_tweet`)
    - For speed-critical operations (this tool is slower, ~5-10 seconds)

    Args:
        tweet: Tweet ID or URL containing an X Article
    """
    try:
        result = await get_api().get_article(tweet)
        if result is None:
            return {"error": True, "code": "article_not_found", "message": "Tweet exists but is not an article"}
        return result
    except Exception as e:
        return handle_error(e)


@mcp.tool()
def upload_media(file_path: str | None = None, url: str | None = None, media_type: str | None = None) -> dict:
    """Upload an image or video file to Twitter and get a media_id for attachment to tweets.

    Workflow:
    1. Call `upload_media` with file path or URL
    2. Receive `media_id` in response
    3. Pass `media_id` to `create_tweet` in `media_ids` array

    Supported formats:
    - Images: PNG, JPEG, GIF, WEBP (max 5MB)
    - Videos: MP4 (max 512MB, 140 seconds)

    Args:
        file_path: Local file path to upload
        url: URL of image/video to upload
        media_type: MIME type (auto-detected if not provided)

    One of `file_path` or `url` is required.
    """
    # Note: Media upload implementation depends on the specific API capabilities
    # This is a placeholder that returns an informative error
    return {
        "error": True,
        "code": "not_implemented",
        "message": "Media upload not yet implemented. Use the Twitter web interface to upload media.",
    }


# =============================================================================
# Search (3 tools)
# =============================================================================


@mcp.tool()
def search_tweets(
    query: str,
    max_results: int = 10,
    pagination_token: str | None = None,
) -> dict:
    """Search for tweets from the last 7 days using Twitter's search syntax.

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

    Args:
        query: Search query with Twitter syntax
        max_results: Results per page, 10-100 (default: 10)
        pagination_token: Token from previous response for next page
    """
    try:
        return get_api().search_tweets(query, max_results, pagination_token)
    except Exception as e:
        return handle_error(e)


@mcp.tool()
def search_all_tweets(
    query: str,
    max_results: int = 10,
    start_time: str | None = None,
    end_time: str | None = None,
    pagination_token: str | None = None,
) -> dict:
    """Search the full archive of public tweets (not just last 7 days).

    Requires elevated API access. Same query syntax as `search_tweets`.

    Additional time-based parameters allow searching specific date ranges.

    Args:
        query: Search query with Twitter syntax
        max_results: Results per page, 10-500 (default: 10)
        start_time: ISO 8601 timestamp for range start
        end_time: ISO 8601 timestamp for range end
        pagination_token: Token for next page
    """
    try:
        return get_api().search_all_tweets(query, max_results, start_time, end_time, pagination_token)
    except Exception as e:
        return handle_error(e)


@mcp.tool()
def count_tweets(
    query: str,
    granularity: str = "day",
    start_time: str | None = None,
    end_time: str | None = None,
) -> dict:
    """Count tweets matching a search query over time.

    Returns counts grouped by time granularity (minute, hour, or day).
    Useful for analyzing tweet volume trends.

    Args:
        query: Search query with Twitter syntax
        granularity: Time bucket: "minute", "hour", "day" (default: "day")
        start_time: ISO 8601 timestamp for range start
        end_time: ISO 8601 timestamp for range end
    """
    try:
        return get_api().count_tweets(query, granularity, start_time, end_time)
    except Exception as e:
        return handle_error(e)


# =============================================================================
# Timelines (3 tools)
# =============================================================================


@mcp.tool()
def get_home_timeline(
    max_results: int = 10,
    pagination_token: str | None = None,
) -> dict:
    """Get your home timeline - tweets from accounts you follow.

    Note: Results are algorithmic (not strictly chronological).

    Args:
        max_results: Results to return, 1-100 (default: 10)
        pagination_token: Token for next page
    """
    try:
        return get_api().get_home_timeline(max_results, pagination_token)
    except Exception as e:
        return handle_error(e)


@mcp.tool()
def get_user_tweets(
    username: str | None = None,
    user_id: str | None = None,
    max_results: int = 10,
    since_id: str | None = None,
    exclude_retweets: bool = False,
    exclude_replies: bool = False,
    pagination_token: str | None = None,
) -> dict:
    """Get recent tweets from a specific user.

    Use this to:
    - Monitor what someone has been posting
    - Fetch tweets for analysis
    - Poll for new tweets (use `since_id` parameter)

    Note: For thread detection, check `is_thread` flag on returned tweets.

    Args:
        username: Twitter handle (e.g., "elonmusk")
        user_id: Twitter user ID
        max_results: Results to return, 5-100 (default: 10)
        since_id: Only return tweets newer than this ID
        exclude_retweets: Exclude retweets (default: false)
        exclude_replies: Exclude replies (default: false)
        pagination_token: Token for next page

    One of `username` or `user_id` is required.
    """
    try:
        return get_api().get_user_tweets(
            username=username,
            user_id=user_id,
            max_results=max_results,
            since_id=since_id,
            exclude_retweets=exclude_retweets,
            exclude_replies=exclude_replies,
            pagination_token=pagination_token,
        )
    except Exception as e:
        return handle_error(e)


@mcp.tool()
def get_mentions(
    max_results: int = 10,
    since_id: str | None = None,
    pagination_token: str | None = None,
) -> dict:
    """Get tweets that mention you (@username).

    Use this to:
    - Check for replies to your tweets
    - Monitor mentions of your account
    - Build reply/engagement workflows

    Args:
        max_results: Results to return, 5-100 (default: 10)
        since_id: Only return mentions newer than this ID
        pagination_token: Token for next page
    """
    try:
        return get_api().get_mentions(max_results, since_id, pagination_token)
    except Exception as e:
        return handle_error(e)


# =============================================================================
# User Lookup (5 tools)
# =============================================================================


@mcp.tool()
def get_me() -> dict:
    """Get your own Twitter profile information.

    Use this to:
    - Verify authentication is working
    - Get your user ID for other API calls
    - Check your follower/following counts
    """
    try:
        return get_api().get_me()
    except Exception as e:
        return handle_error(e)


@mcp.tool()
def get_user(username: str | None = None, user_id: str | None = None) -> dict:
    """Get a Twitter user's profile by username or user ID.

    Use this to:
    - Look up user information before fetching their tweets
    - Get user ID (required for some API calls)
    - Check follower counts, bio, verification status

    Args:
        username: Twitter handle without @ (e.g., "elonmusk")
        user_id: Twitter user ID

    One of `username` or `user_id` is required.
    """
    try:
        return get_api().get_user(username, user_id)
    except Exception as e:
        return handle_error(e)


@mcp.tool()
def get_users(usernames: list[str] | None = None, user_ids: list[str] | None = None) -> dict:
    """Fetch multiple users by username or ID in a single request (batch lookup).

    Use this when you need to look up several users efficiently.
    Maximum 100 users per request.

    Args:
        usernames: List of Twitter handles (max 100)
        user_ids: List of user IDs (max 100)

    One of `usernames` or `user_ids` is required.
    """
    try:
        return get_api().get_users(usernames, user_ids)
    except Exception as e:
        return handle_error(e)


@mcp.tool()
def get_followers(
    username: str | None = None,
    user_id: str | None = None,
    max_results: int = 100,
    pagination_token: str | None = None,
) -> dict:
    """Get a user's followers.

    Args:
        username: Twitter handle
        user_id: User ID
        max_results: Results to return, 1-1000 (default: 100)
        pagination_token: Token for next page

    One of `username` or `user_id` is required.
    """
    try:
        return get_api().get_followers(username, user_id, max_results, pagination_token)
    except Exception as e:
        return handle_error(e)


@mcp.tool()
def get_following(
    username: str | None = None,
    user_id: str | None = None,
    max_results: int = 100,
    pagination_token: str | None = None,
) -> dict:
    """Get accounts a user follows.

    Args:
        username: Twitter handle
        user_id: User ID
        max_results: Results to return, 1-1000 (default: 100)
        pagination_token: Token for next page

    One of `username` or `user_id` is required.
    """
    try:
        return get_api().get_following(username, user_id, max_results, pagination_token)
    except Exception as e:
        return handle_error(e)


# =============================================================================
# Social Actions (8 tools)
# =============================================================================


@mcp.tool()
def follow(username: str | None = None, user_id: str | None = None) -> dict:
    """Follow a Twitter user.

    Args:
        username: Twitter handle to follow
        user_id: User ID to follow

    One of `username` or `user_id` is required.
    """
    try:
        return get_api().follow(username, user_id)
    except Exception as e:
        return handle_error(e)


@mcp.tool()
def unfollow(username: str | None = None, user_id: str | None = None) -> dict:
    """Unfollow a Twitter user.

    Args:
        username: Twitter handle to unfollow
        user_id: User ID to unfollow

    One of `username` or `user_id` is required.
    """
    try:
        return get_api().unfollow(username, user_id)
    except Exception as e:
        return handle_error(e)


@mcp.tool()
def mute(username: str | None = None, user_id: str | None = None) -> dict:
    """Mute a Twitter user. Their tweets won't appear in your timeline.

    Args:
        username: Twitter handle to mute
        user_id: User ID to mute

    One of `username` or `user_id` is required.
    """
    try:
        return get_api().mute(username, user_id)
    except Exception as e:
        return handle_error(e)


@mcp.tool()
def unmute(username: str | None = None, user_id: str | None = None) -> dict:
    """Unmute a Twitter user.

    Args:
        username: Twitter handle to unmute
        user_id: User ID to unmute

    One of `username` or `user_id` is required.
    """
    try:
        return get_api().unmute(username, user_id)
    except Exception as e:
        return handle_error(e)


@mcp.tool()
def block(username: str | None = None, user_id: str | None = None) -> dict:
    """Block a Twitter user. They cannot see your tweets or interact with you.

    Args:
        username: Twitter handle to block
        user_id: User ID to block

    One of `username` or `user_id` is required.
    """
    try:
        return get_api().block(username, user_id)
    except Exception as e:
        return handle_error(e)


@mcp.tool()
def unblock(username: str | None = None, user_id: str | None = None) -> dict:
    """Unblock a Twitter user.

    Args:
        username: Twitter handle to unblock
        user_id: User ID to unblock

    One of `username` or `user_id` is required.
    """
    try:
        return get_api().unblock(username, user_id)
    except Exception as e:
        return handle_error(e)


@mcp.tool()
def get_muted(max_results: int = 100, pagination_token: str | None = None) -> dict:
    """Get list of users you have muted.

    Args:
        max_results: Results to return, 1-1000 (default: 100)
        pagination_token: Token for next page
    """
    try:
        return get_api().get_muted(max_results, pagination_token)
    except Exception as e:
        return handle_error(e)


@mcp.tool()
def get_blocked(max_results: int = 100, pagination_token: str | None = None) -> dict:
    """Get list of users you have blocked.

    Args:
        max_results: Results to return, 1-1000 (default: 100)
        pagination_token: Token for next page
    """
    try:
        return get_api().get_blocked(max_results, pagination_token)
    except Exception as e:
        return handle_error(e)


# =============================================================================
# Engagement (9 tools)
# =============================================================================


@mcp.tool()
def like(tweet_id: str) -> dict:
    """Like a tweet.

    Args:
        tweet_id: ID of tweet to like
    """
    try:
        return get_api().like(tweet_id)
    except Exception as e:
        return handle_error(e)


@mcp.tool()
def unlike(tweet_id: str) -> dict:
    """Remove your like from a tweet.

    Args:
        tweet_id: ID of tweet to unlike
    """
    try:
        return get_api().unlike(tweet_id)
    except Exception as e:
        return handle_error(e)


@mcp.tool()
def retweet(tweet_id: str) -> dict:
    """Retweet a tweet.

    Args:
        tweet_id: ID of tweet to retweet
    """
    try:
        return get_api().retweet(tweet_id)
    except Exception as e:
        return handle_error(e)


@mcp.tool()
def unretweet(tweet_id: str) -> dict:
    """Undo a retweet.

    Args:
        tweet_id: ID of tweet to unretweet
    """
    try:
        return get_api().unretweet(tweet_id)
    except Exception as e:
        return handle_error(e)


@mcp.tool()
def bookmark(tweet_id: str) -> dict:
    """Bookmark a tweet for later.

    Args:
        tweet_id: ID of tweet to bookmark
    """
    try:
        return get_api().bookmark(tweet_id)
    except Exception as e:
        return handle_error(e)


@mcp.tool()
def remove_bookmark(tweet_id: str) -> dict:
    """Remove a tweet from your bookmarks.

    Args:
        tweet_id: ID of tweet to remove from bookmarks
    """
    try:
        return get_api().remove_bookmark(tweet_id)
    except Exception as e:
        return handle_error(e)


@mcp.tool()
def get_bookmarks(max_results: int = 10, pagination_token: str | None = None) -> dict:
    """Get your bookmarked tweets.

    Args:
        max_results: Results to return, 1-100 (default: 10)
        pagination_token: Token for next page
    """
    try:
        return get_api().get_bookmarks(max_results, pagination_token)
    except Exception as e:
        return handle_error(e)


@mcp.tool()
def get_liking_users(
    tweet_id: str,
    max_results: int = 100,
    pagination_token: str | None = None,
) -> dict:
    """Get users who liked a specific tweet.

    Args:
        tweet_id: ID of the tweet
        max_results: Results to return, 1-100 (default: 100)
        pagination_token: Token for next page
    """
    try:
        return get_api().get_liking_users(tweet_id, max_results, pagination_token)
    except Exception as e:
        return handle_error(e)


@mcp.tool()
def get_retweeters(
    tweet_id: str,
    max_results: int = 100,
    pagination_token: str | None = None,
) -> dict:
    """Get users who retweeted a specific tweet.

    Args:
        tweet_id: ID of the tweet
        max_results: Results to return, 1-100 (default: 100)
        pagination_token: Token for next page
    """
    try:
        return get_api().get_retweeters(tweet_id, max_results, pagination_token)
    except Exception as e:
        return handle_error(e)


# =============================================================================
# Replies (2 tools)
# =============================================================================


@mcp.tool()
def hide_reply(tweet_id: str) -> dict:
    """Hide a reply to one of your tweets. The reply will be collapsed and shown as "hidden".

    Args:
        tweet_id: ID of the reply to hide
    """
    try:
        return get_api().hide_reply(tweet_id)
    except Exception as e:
        return handle_error(e)


@mcp.tool()
def unhide_reply(tweet_id: str) -> dict:
    """Unhide a previously hidden reply.

    Args:
        tweet_id: ID of the reply to unhide
    """
    try:
        return get_api().unhide_reply(tweet_id)
    except Exception as e:
        return handle_error(e)


# =============================================================================
# Entry Point
# =============================================================================


def main():
    """Run the MCP server."""
    mcp.run()


if __name__ == "__main__":
    main()
