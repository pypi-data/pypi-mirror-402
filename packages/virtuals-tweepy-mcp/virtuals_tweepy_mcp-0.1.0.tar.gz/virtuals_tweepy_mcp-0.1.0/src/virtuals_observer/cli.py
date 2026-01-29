#!/usr/bin/env python3
"""
Virtuals Twitter SDK CLI - Test key functionality of the SDK.

Usage:
    python cli.py auth              # Authenticate and get access token
    python cli.py me                # Get your profile
    python cli.py search <query>    # Search tweets
    python cli.py timeline <user>   # Get user's timeline
    python cli.py user <username>   # Get user info
    python cli.py post <text>       # Post a tweet
"""

import argparse
import json
import os
import signal
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

# State file for tracking monitored tweets
STATE_FILE = Path.home() / ".vobs_state.json"

def get_client():
    """Initialize and return Twitter client."""
    try:
        from virtuals_tweepy import Client
    except ImportError:
        print("Error: virtuals-tweepy not installed.")
        print("Run: pip install virtuals-tweepy")
        sys.exit(1)

    token = os.environ.get("GAME_TWITTER_ACCESS_TOKEN")
    if not token:
        print("Error: GAME_TWITTER_ACCESS_TOKEN not found in environment.")
        print("Run: python cli.py auth")
        sys.exit(1)

    return Client(game_twitter_access_token=token)

def cmd_auth(args):
    """Authenticate and get access token."""
    api_key = os.environ.get("GAME_API_KEY")
    if not api_key:
        print("Error: GAME_API_KEY not found in .env")
        print("Get your API key from: https://console.game.virtuals.io/")
        sys.exit(1)

    print(f"Using GAME_API_KEY: {api_key[:8]}...{api_key[-4:]}")
    print("\nRunning authentication flow...")
    print("=" * 50)

    try:
        from twitter_plugin_gamesdk.game_twitter_auth import AuthManager
        auth = AuthManager()
        auth.start_authentication(api_key)
        print("\n" + "=" * 50)
        print("If successful, add the token to your .env file as:")
        print("GAME_TWITTER_ACCESS_TOKEN=apx-...")
    except ImportError:
        print("Error: twitter_plugin_gamesdk not installed.")
        print("Run: uv add twitter-plugin-gamesdk")
        sys.exit(1)
    except Exception as e:
        print(f"Error during authentication: {e}")
        sys.exit(1)

def cmd_me(args):
    """Get your own profile."""
    client = get_client()

    print("Fetching your profile...")
    try:
        me = client.get_me(
            user_fields=["created_at", "description", "public_metrics", "verified"]
        )
        user = me.data
        metrics = user.public_metrics

        print("\n" + "=" * 50)
        print(f"Username:    @{user.username}")
        print(f"Name:        {user.name}")
        print(f"ID:          {user.id}")
        print(f"Followers:   {metrics['followers_count']:,}")
        print(f"Following:   {metrics['following_count']:,}")
        print(f"Tweets:      {metrics['tweet_count']:,}")
        if hasattr(user, 'description') and user.description:
            print(f"Bio:         {user.description[:100]}...")
        print("=" * 50)
        print("\n✓ Authentication working!")

    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

def cmd_search(args):
    """Search for tweets."""
    client = get_client()
    query = args.query
    count = args.count

    print(f"Searching for: {query}")
    print(f"Max results: {count}")
    print("-" * 50)

    try:
        response = client.search_recent_tweets(
            query=query,
            max_results=min(count, 100),
            tweet_fields=["created_at", "public_metrics", "author_id"],
            expansions=["author_id"],
            user_fields=["username", "verified"]
        )

        if not response.data:
            print("No tweets found.")
            return

        # Build user lookup
        users = {}
        if response.includes and "users" in response.includes:
            users = {u.id: u for u in response.includes["users"]}

        print(f"\nFound {len(response.data)} tweets:\n")

        for i, tweet in enumerate(response.data, 1):
            author = users.get(tweet.author_id)
            username = f"@{author.username}" if author else f"[{tweet.author_id}]"
            metrics = tweet.public_metrics
            created = tweet.created_at.strftime("%Y-%m-%d %H:%M") if tweet.created_at else "?"

            print(f"{i}. {username} ({created})")
            print(f"   {tweet.text[:200]}")
            print(f"   ♥ {metrics['like_count']}  ⟲ {metrics['retweet_count']}  💬 {metrics['reply_count']}")
            print(f"   https://twitter.com/i/status/{tweet.id}")
            print()

        print("-" * 50)
        print(f"✓ Found {len(response.data)} tweets for '{query}'")

    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

def cmd_timeline(args):
    """Get a user's timeline."""
    client = get_client()
    username = args.username.lstrip('@')
    count = args.count

    print(f"Fetching timeline for @{username}...")

    try:
        # First get user ID
        user_response = client.get_user(
            username=username,
            user_fields=["public_metrics", "description"]
        )

        if not user_response.data:
            print(f"User @{username} not found.")
            sys.exit(1)

        user = user_response.data
        metrics = user.public_metrics

        print(f"\n@{user.username} - {user.name}")
        print(f"Followers: {metrics['followers_count']:,} | Following: {metrics['following_count']:,}")
        print("-" * 50)

        # Get tweets
        tweets_response = client.get_users_tweets(
            id=user.id,
            max_results=min(count, 100),
            tweet_fields=["created_at", "public_metrics"],
            exclude=["retweets"] if args.no_retweets else None
        )

        if not tweets_response.data:
            print("No tweets found.")
            return

        print(f"\nRecent {len(tweets_response.data)} tweets:\n")

        for i, tweet in enumerate(tweets_response.data, 1):
            metrics = tweet.public_metrics
            created = tweet.created_at.strftime("%Y-%m-%d %H:%M") if tweet.created_at else "?"

            print(f"{i}. ({created})")
            print(f"   {tweet.text[:200]}")
            print(f"   ♥ {metrics['like_count']}  ⟲ {metrics['retweet_count']}  💬 {metrics['reply_count']}")
            print()

        print("-" * 50)
        print(f"✓ Fetched {len(tweets_response.data)} tweets from @{username}")

    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

def cmd_user(args):
    """Get user information."""
    client = get_client()
    username = args.username.lstrip('@')

    print(f"Looking up @{username}...")

    try:
        response = client.get_user(
            username=username,
            user_fields=["created_at", "description", "public_metrics", "verified", "location", "url"]
        )

        if not response.data:
            print(f"User @{username} not found.")
            sys.exit(1)

        user = response.data
        metrics = user.public_metrics

        print("\n" + "=" * 50)
        print(f"Username:    @{user.username}")
        print(f"Name:        {user.name}")
        print(f"ID:          {user.id}")
        print(f"Followers:   {metrics['followers_count']:,}")
        print(f"Following:   {metrics['following_count']:,}")
        print(f"Tweets:      {metrics['tweet_count']:,}")
        print(f"Listed:      {metrics['listed_count']:,}")

        if hasattr(user, 'location') and user.location:
            print(f"Location:    {user.location}")
        if hasattr(user, 'url') and user.url:
            print(f"URL:         {user.url}")
        if hasattr(user, 'created_at') and user.created_at:
            print(f"Joined:      {user.created_at.strftime('%Y-%m-%d')}")
        if hasattr(user, 'description') and user.description:
            print(f"Bio:         {user.description}")

        print("=" * 50)

    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

def extract_tweet_id(url_or_id):
    """Extract tweet ID from URL or return as-is if already an ID."""
    import re
    # If it's just digits, return as-is
    if url_or_id.isdigit():
        return url_or_id
    # Try to extract from URL patterns
    patterns = [
        r'twitter\.com/\w+/status/(\d+)',
        r'x\.com/\w+/status/(\d+)',
        r'/status/(\d+)',
    ]
    for pattern in patterns:
        match = re.search(pattern, url_or_id)
        if match:
            return match.group(1)
    # If nothing matched, return as-is and let the API handle it
    return url_or_id

def fetch_article_content(tweet_url: str) -> dict | None:
    """Fetch X Article content using Playwright.

    Returns dict with title, content, images, or None if not an article or playwright unavailable.
    """
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print("Error: playwright not installed. Install with: uv add playwright")
        print("Then run: playwright install chromium")
        return None

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()

            # Navigate to tweet with longer timeout
            page.goto(tweet_url, wait_until="domcontentloaded", timeout=60000)

            # Wait for article content to load (X is heavy)
            page.wait_for_timeout(5000)

            # Check if this is an article tweet
            article_content = page.evaluate("""
                () => {
                    const article = document.querySelector('article');
                    if (!article) return null;

                    // Check for article indicators (headings in the tweet body)
                    const headings = article.querySelectorAll('h2');
                    if (headings.length < 2) return null;  // Not an article

                    // Extract title - usually the first prominent text
                    const titleCandidates = article.querySelectorAll('[dir="auto"]');
                    let title = '';
                    for (const el of titleCandidates) {
                        const text = el.innerText.trim();
                        if (text.length > 10 && text.length < 100 && !text.startsWith('@')) {
                            title = text;
                            break;
                        }
                    }

                    // Get full article text
                    const fullText = article.innerText;

                    // Extract image URLs
                    const images = [];
                    const imgElements = article.querySelectorAll('img[src*="pbs.twimg.com/media"]');
                    imgElements.forEach(img => {
                        if (img.src && !images.includes(img.src)) {
                            images.push(img.src);
                        }
                    });

                    // Extract sections by headings
                    const sections = [];
                    headings.forEach(h => {
                        sections.push(h.innerText.trim());
                    });

                    return {
                        title: title,
                        content: fullText,
                        sections: sections,
                        images: images
                    };
                }
            """)

            browser.close()
            return article_content

    except Exception as e:
        print(f"Error fetching article: {e}")
        return None


def cmd_fetch(args):
    """Fetch a specific tweet by URL or ID."""
    client = get_client()
    tweet_id = extract_tweet_id(args.tweet)
    output_json = args.json

    if not output_json:
        print(f"Fetching tweet {tweet_id}...")

    try:
        response = client.get_tweet(
            id=tweet_id,
            tweet_fields=["created_at", "public_metrics", "entities", "conversation_id"],
            expansions=["author_id", "attachments.media_keys"],
            user_fields=["username", "name", "verified", "public_metrics"],
            media_fields=["url", "preview_image_url", "type", "variants", "duration_ms"]
        )

        if not response.data:
            print(f"Tweet {tweet_id} not found.")
            sys.exit(1)

        tweet = response.data
        metrics = tweet.public_metrics

        # Get author info
        author = None
        if response.includes and "users" in response.includes:
            author = response.includes["users"][0]

        # Get entity URLs (expanded URLs, article links, etc.)
        entity_urls = []
        if hasattr(tweet, 'entities') and tweet.entities and 'urls' in tweet.entities:
            for url_entity in tweet.entities['urls']:
                entity_url = {
                    "short_url": url_entity.get('url'),
                    "expanded_url": url_entity.get('expanded_url') or url_entity.get('unwound_url'),
                    "display_url": url_entity.get('display_url'),
                }
                # Detect X Articles
                expanded = entity_url.get('expanded_url', '')
                if expanded and '/article/' in expanded:
                    entity_url["type"] = "article"
                elif expanded and '/status/' in expanded:
                    entity_url["type"] = "tweet"
                else:
                    entity_url["type"] = "link"
                entity_urls.append(entity_url)

        # Get media info
        media_items = []
        if response.includes and "media" in response.includes:
            for m in response.includes["media"]:
                media_type = m.type if hasattr(m, 'type') else 'unknown'
                item = {"type": media_type}

                if media_type == "video" or media_type == "animated_gif":
                    # Get video variants (different qualities)
                    if hasattr(m, 'variants') and m.variants:
                        # Filter for mp4 and sort by bitrate (highest first)
                        mp4_variants = [v for v in m.variants if v.get('content_type') == 'video/mp4']
                        if mp4_variants:
                            mp4_variants.sort(key=lambda x: x.get('bit_rate', 0), reverse=True)
                            item["url"] = mp4_variants[0]['url']  # Highest quality
                            item["variants"] = [{"url": v['url'], "bitrate": v.get('bit_rate')} for v in mp4_variants]
                    if hasattr(m, 'preview_image_url') and m.preview_image_url:
                        item["thumbnail"] = m.preview_image_url
                    if hasattr(m, 'duration_ms') and m.duration_ms:
                        item["duration_ms"] = m.duration_ms
                else:
                    # Image
                    if hasattr(m, 'url') and m.url:
                        item["url"] = m.url
                    elif hasattr(m, 'preview_image_url') and m.preview_image_url:
                        item["url"] = m.preview_image_url

                media_items.append(item)

        # Check if this is an article and auto-fetch content (unless --no-article)
        has_article = any(u.get("type") == "article" for u in entity_urls)
        article_content = None

        if has_article and not args.no_article:
            username_for_url = author.username if author else "unknown"
            tweet_url_for_article = f"https://x.com/{username_for_url}/status/{tweet.id}"
            if not output_json:
                print("Fetching article content...")
            article_content = fetch_article_content(tweet_url_for_article)

        username = author.username if author else "unknown"
        tweet_url = f"https://twitter.com/{username}/status/{tweet.id}"

        if output_json:
            tweet_data = {
                "id": tweet.id,
                "text": tweet.text,
                "username": username,
                "name": author.name if author else None,
                "created_at": tweet.created_at.isoformat() if tweet.created_at else None,
                "url": tweet_url,
                "likes": metrics['like_count'],
                "retweets": metrics['retweet_count'],
                "replies": metrics['reply_count'],
                "quotes": metrics.get('quote_count', 0),
                "bookmarks": metrics.get('bookmark_count', 0),
                "impressions": metrics.get('impression_count', 0),
                "media": media_items,
                "urls": entity_urls,
                "conversation_id": tweet.conversation_id if hasattr(tweet, 'conversation_id') else None,
            }
            if article_content:
                tweet_data["article"] = article_content
            print(json.dumps(tweet_data, indent=2))
        else:
            created = tweet.created_at.strftime("%Y-%m-%d %H:%M") if tweet.created_at else "?"

            print("\n" + "=" * 50)
            if author:
                print(f"Author:      @{author.username} ({author.name})")
            print(f"Posted:      {created}")
            print(f"Tweet ID:    {tweet.id}")
            print("=" * 50)
            print(f"\n{tweet.text}\n")
            print("-" * 50)
            print(f"♥ {metrics['like_count']:,}  ⟲ {metrics['retweet_count']:,}  💬 {metrics['reply_count']:,}  🔖 {metrics.get('bookmark_count', 0):,}")
            if entity_urls:
                print(f"\nLinks ({len(entity_urls)}):")
                for url_info in entity_urls:
                    url_type = url_info.get('type', 'link')
                    expanded = url_info.get('expanded_url', url_info.get('short_url', 'N/A'))
                    if url_type == 'article':
                        print(f"  📄 [X Article] {expanded}")
                    elif url_type == 'tweet':
                        print(f"  🐦 [Tweet] {expanded}")
                    else:
                        print(f"  🔗 {expanded}")
            if media_items:
                print(f"\nMedia ({len(media_items)}):")
                for item in media_items:
                    media_type = item.get('type', 'unknown')
                    if media_type == 'video' or media_type == 'animated_gif':
                        duration = item.get('duration_ms', 0) // 1000
                        print(f"  [{media_type}] {item.get('url', 'N/A')} ({duration}s)")
                    else:
                        print(f"  [{media_type}] {item.get('url', 'N/A')}")
            print(f"\n{tweet_url}")
            print("=" * 50)

            # Display article content if fetched
            if article_content:
                print("\n" + "=" * 50)
                print("📄 ARTICLE CONTENT")
                print("=" * 50)
                if article_content.get('title'):
                    print(f"\nTitle: {article_content['title']}")
                if article_content.get('sections'):
                    print(f"\nSections: {len(article_content['sections'])}")
                    for section in article_content['sections']:
                        print(f"  • {section}")
                if article_content.get('content'):
                    print("\n" + "-" * 50)
                    print("Full Content:")
                    print("-" * 50)
                    # Clean up the content (remove UI elements at the end)
                    content = article_content['content']
                    # Try to remove the footer/UI parts
                    if '조회수' in content:  # Korean "views" - indicates end of content
                        content = content.split('조회수')[0].rsplit('\n', 3)[0]
                    print(content)
                if article_content.get('images'):
                    print("\n" + "-" * 50)
                    print(f"Images ({len(article_content['images'])}):")
                    for img in article_content['images']:
                        print(f"  {img}")
                print("=" * 50)

    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

def cmd_post(args):
    """Post a tweet."""
    client = get_client()
    text = args.text

    if not args.yes:
        print(f"About to post:\n\n  {text}\n")
        confirm = input("Confirm? [y/N]: ").strip().lower()
        if confirm != 'y':
            print("Cancelled.")
            return

    try:
        response = client.create_tweet(text=text)
        tweet_id = response.data['id']
        print(f"\n✓ Tweet posted!")
        print(f"  https://twitter.com/i/status/{tweet_id}")

    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

def cmd_mentions(args):
    """Get your mentions."""
    client = get_client()
    count = args.count

    print("Fetching your mentions...")

    try:
        # Get my user ID first
        me = client.get_me()
        my_id = me.data.id

        response = client.get_users_mentions(
            id=my_id,
            max_results=min(count, 100),
            tweet_fields=["created_at", "public_metrics", "author_id"],
            expansions=["author_id"],
            user_fields=["username"]
        )

        if not response.data:
            print("No mentions found.")
            return

        # Build user lookup
        users = {}
        if response.includes and "users" in response.includes:
            users = {u.id: u for u in response.includes["users"]}

        print(f"\nRecent {len(response.data)} mentions:\n")

        for i, tweet in enumerate(response.data, 1):
            author = users.get(tweet.author_id)
            username = f"@{author.username}" if author else f"[{tweet.author_id}]"
            created = tweet.created_at.strftime("%Y-%m-%d %H:%M") if tweet.created_at else "?"

            print(f"{i}. {username} ({created})")
            print(f"   {tweet.text[:200]}")
            print(f"   https://twitter.com/i/status/{tweet.id}")
            print()

        print("-" * 50)
        print(f"✓ Found {len(response.data)} mentions")

    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

def cmd_home(args):
    """Get your home timeline."""
    client = get_client()
    count = args.count

    print("Fetching your home timeline...")

    try:
        response = client.get_home_timeline(
            max_results=min(count, 100),
            tweet_fields=["created_at", "public_metrics", "author_id"],
            expansions=["author_id"],
            user_fields=["username"]
        )

        if not response.data:
            print("No tweets found.")
            return

        # Build user lookup
        users = {}
        if response.includes and "users" in response.includes:
            users = {u.id: u for u in response.includes["users"]}

        print(f"\nRecent {len(response.data)} tweets:\n")

        for i, tweet in enumerate(response.data, 1):
            author = users.get(tweet.author_id)
            username = f"@{author.username}" if author else f"[{tweet.author_id}]"
            metrics = tweet.public_metrics
            created = tweet.created_at.strftime("%Y-%m-%d %H:%M") if tweet.created_at else "?"

            print(f"{i}. {username} ({created})")
            print(f"   {tweet.text[:200]}")
            print(f"   ♥ {metrics['like_count']}  ⟲ {metrics['retweet_count']}")
            print()

        print("-" * 50)
        print(f"✓ Fetched {len(response.data)} tweets from home timeline")

    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

def load_state():
    """Load monitoring state from file."""
    if STATE_FILE.exists():
        try:
            with open(STATE_FILE) as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return {}
    return {}

def save_state(state):
    """Save monitoring state to file."""
    with open(STATE_FILE, 'w') as f:
        json.dump(state, f, indent=2)

def get_last_tweet_id(username):
    """Get last seen tweet ID for a user."""
    state = load_state()
    return state.get(f"last_tweet_{username.lower()}")

def set_last_tweet_id(username, tweet_id):
    """Set last seen tweet ID for a user."""
    state = load_state()
    state[f"last_tweet_{username.lower()}"] = tweet_id
    save_state(state)

def cmd_monitor(args):
    """Monitor a user's tweets."""
    client = get_client()
    username = args.username.lstrip('@')
    interval = args.interval
    exec_cmd = args.exec
    include_rts = not args.no_retweets
    output_json = args.json

    # Get user info first
    print(f"Setting up monitor for @{username}...")
    try:
        user_response = client.get_user(
            username=username,
            user_fields=["public_metrics"]
        )
        if not user_response.data:
            print(f"User @{username} not found.")
            sys.exit(1)

        user = user_response.data
        user_id = user.id
        print(f"Found user: @{user.username} (ID: {user_id})")

    except Exception as e:
        print(f"Error fetching user: {e}")
        sys.exit(1)

    # Get last seen tweet ID
    last_tweet_id = get_last_tweet_id(username)
    if last_tweet_id:
        print(f"Resuming from tweet ID: {last_tweet_id}")
    else:
        print("First run - will capture baseline and watch for new tweets")

    # Handle Ctrl+C gracefully
    running = True
    def signal_handler(sig, frame):
        nonlocal running
        print("\n\nStopping monitor...")
        running = False

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    print(f"\nMonitoring @{username} every {interval}s (Ctrl+C to stop)")
    print("=" * 50)

    poll_count = 0
    new_tweets_total = 0

    while running:
        poll_count += 1
        try:
            # Fetch recent tweets
            params = {
                "id": user_id,
                "max_results": 10,
                "tweet_fields": ["created_at", "public_metrics", "entities"],
            }
            if not include_rts:
                params["exclude"] = ["retweets"]
            if last_tweet_id:
                params["since_id"] = last_tweet_id

            response = client.get_users_tweets(**params)

            if response.data:
                # Sort by ID (newest first is default, we want oldest first for processing)
                tweets = sorted(response.data, key=lambda t: int(t.id))

                for tweet in tweets:
                    new_tweets_total += 1
                    created = tweet.created_at.strftime("%Y-%m-%d %H:%M") if tweet.created_at else "?"
                    metrics = tweet.public_metrics
                    tweet_url = f"https://twitter.com/{username}/status/{tweet.id}"

                    if output_json:
                        # JSON output mode
                        tweet_data = {
                            "id": tweet.id,
                            "username": username,
                            "text": tweet.text,
                            "created_at": tweet.created_at.isoformat() if tweet.created_at else None,
                            "url": tweet_url,
                            "likes": metrics['like_count'],
                            "retweets": metrics['retweet_count'],
                            "replies": metrics['reply_count'],
                        }
                        print(json.dumps(tweet_data))
                    else:
                        # Human-readable output
                        print(f"\n[NEW] @{username} ({created})")
                        print(f"  {tweet.text}")
                        print(f"  ♥ {metrics['like_count']}  ⟲ {metrics['retweet_count']}  💬 {metrics['reply_count']}")
                        print(f"  {tweet_url}")

                    # Execute callback if provided
                    if exec_cmd:
                        cmd = exec_cmd.replace("{}", tweet_url)
                        cmd = cmd.replace("{text}", tweet.text.replace('"', '\\"'))
                        cmd = cmd.replace("{id}", tweet.id)
                        cmd = cmd.replace("{user}", username)
                        try:
                            subprocess.run(cmd, shell=True, check=False)
                        except Exception as e:
                            print(f"  [exec error: {e}]")

                    # Update last seen ID
                    last_tweet_id = tweet.id
                    set_last_tweet_id(username, last_tweet_id)

            # Status update (unless in JSON mode)
            if not output_json:
                now = datetime.now().strftime("%H:%M:%S")
                status = f"[{now}] Poll #{poll_count} - {new_tweets_total} new tweets total"
                print(f"\r{status}", end="", flush=True)

        except Exception as e:
            if not output_json:
                print(f"\n[Error] {e}")

        # Wait for next poll
        for _ in range(interval):
            if not running:
                break
            time.sleep(1)

    print(f"\nMonitor stopped. Total new tweets captured: {new_tweets_total}")

def main():
    load_dotenv()

    parser = argparse.ArgumentParser(
        description="Virtuals Twitter SDK CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  vobs auth                       # Get access token
  vobs me                         # Check your profile
  vobs search "#Bitcoin"          # Search tweets
  vobs timeline VitalikButerin    # Get user's timeline
  vobs user elonmusk              # Get user info
  vobs fetch <tweet-url>          # Fetch specific tweet
  vobs fetch 1234567890           # Fetch by tweet ID
  vobs monitor elonmusk           # Monitor user's tweets
  vobs monitor elonmusk -i 120    # Poll every 2 minutes
  vobs post "Hello world!"        # Post a tweet
        """
    )

    subparsers = parser.add_subparsers(dest="command", help="Command to run")

    # auth
    auth_parser = subparsers.add_parser("auth", help="Authenticate and get access token")
    auth_parser.set_defaults(func=cmd_auth)

    # me
    me_parser = subparsers.add_parser("me", help="Get your profile")
    me_parser.set_defaults(func=cmd_me)

    # search
    search_parser = subparsers.add_parser("search", help="Search tweets")
    search_parser.add_argument("query", help="Search query (supports Twitter search syntax)")
    search_parser.add_argument("-n", "--count", type=int, default=10, help="Number of results (default: 10)")
    search_parser.set_defaults(func=cmd_search)

    # timeline
    timeline_parser = subparsers.add_parser("timeline", help="Get user's timeline")
    timeline_parser.add_argument("username", help="Twitter username")
    timeline_parser.add_argument("-n", "--count", type=int, default=10, help="Number of tweets (default: 10)")
    timeline_parser.add_argument("--no-retweets", action="store_true", help="Exclude retweets")
    timeline_parser.set_defaults(func=cmd_timeline)

    # user
    user_parser = subparsers.add_parser("user", help="Get user information")
    user_parser.add_argument("username", help="Twitter username")
    user_parser.set_defaults(func=cmd_user)

    # fetch
    fetch_parser = subparsers.add_parser("fetch", help="Fetch a specific tweet by URL or ID")
    fetch_parser.add_argument("tweet", help="Tweet URL or ID")
    fetch_parser.add_argument("--json", action="store_true", help="Output as JSON")
    fetch_parser.add_argument("--no-article", action="store_true", help="Skip fetching article content even if detected")
    fetch_parser.set_defaults(func=cmd_fetch)

    # mentions
    mentions_parser = subparsers.add_parser("mentions", help="Get your mentions")
    mentions_parser.add_argument("-n", "--count", type=int, default=10, help="Number of mentions (default: 10)")
    mentions_parser.set_defaults(func=cmd_mentions)

    # home
    home_parser = subparsers.add_parser("home", help="Get your home timeline")
    home_parser.add_argument("-n", "--count", type=int, default=10, help="Number of tweets (default: 10)")
    home_parser.set_defaults(func=cmd_home)

    # post
    post_parser = subparsers.add_parser("post", help="Post a tweet")
    post_parser.add_argument("text", help="Tweet text")
    post_parser.add_argument("-y", "--yes", action="store_true", help="Skip confirmation")
    post_parser.set_defaults(func=cmd_post)

    # monitor
    monitor_parser = subparsers.add_parser("monitor", help="Monitor a user's tweets")
    monitor_parser.add_argument("username", help="Twitter username to monitor")
    monitor_parser.add_argument("-i", "--interval", type=int, default=60, help="Poll interval in seconds (default: 60)")
    monitor_parser.add_argument("--exec", help="Command to execute for each new tweet. Placeholders: {} (url), {text}, {id}, {user}")
    monitor_parser.add_argument("--no-retweets", action="store_true", help="Exclude retweets")
    monitor_parser.add_argument("--json", action="store_true", help="Output tweets as JSON (one per line)")
    monitor_parser.set_defaults(func=cmd_monitor)

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    args.func(args)

if __name__ == "__main__":
    main()
