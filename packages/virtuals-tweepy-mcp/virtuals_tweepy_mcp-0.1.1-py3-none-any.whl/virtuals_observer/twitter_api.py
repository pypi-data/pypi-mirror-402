"""Shared Twitter API wrapper for CLI and MCP server.

Provides simplified, consistent response formats across all Twitter operations.
"""

from __future__ import annotations

import os
import re
from dataclasses import dataclass
from datetime import datetime
from typing import Any


class TwitterAPIError(Exception):
    """Base exception for Twitter API errors."""

    def __init__(self, code: str, message: str, http_status: int | None = None):
        self.code = code
        self.message = message
        self.http_status = http_status
        super().__init__(message)

    def to_dict(self) -> dict:
        return {"error": True, "code": self.code, "message": self.message}


def extract_tweet_id(url_or_id: str) -> str:
    """Extract tweet ID from URL or return as-is if already an ID."""
    if url_or_id.isdigit():
        return url_or_id
    patterns = [
        r"twitter\.com/\w+/status/(\d+)",
        r"x\.com/\w+/status/(\d+)",
        r"/status/(\d+)",
    ]
    for pattern in patterns:
        match = re.search(pattern, url_or_id)
        if match:
            return match.group(1)
    return url_or_id


def _ensure_playwright_browsers() -> bool:
    """Install Playwright browsers if not present. Returns True if ready."""
    import subprocess
    import sys

    try:
        result = subprocess.run(
            [sys.executable, "-m", "playwright", "install", "chromium"],
            capture_output=True,
            text=True,
            timeout=120,
        )
        return result.returncode == 0
    except Exception:
        return False


def _simplify_tweet(tweet: Any, users: dict | None = None, media: list | None = None) -> dict:
    """Convert raw tweet response to simplified format."""
    metrics = tweet.public_metrics if hasattr(tweet, "public_metrics") and tweet.public_metrics else {}

    # Get author info
    author = None
    if users and hasattr(tweet, "author_id"):
        author = users.get(tweet.author_id)

    username = author.username if author else "unknown"
    name = author.name if author else None

    # Build tweet URL
    tweet_url = f"https://twitter.com/{username}/status/{tweet.id}"

    # Process entity URLs
    entity_urls = []
    has_article = False
    if hasattr(tweet, "entities") and tweet.entities and "urls" in tweet.entities:
        for url_entity in tweet.entities["urls"]:
            expanded = url_entity.get("expanded_url") or url_entity.get("unwound_url", "")
            entity_url = {
                "expanded_url": expanded,
                "type": "link",
            }
            if "/article/" in expanded:
                entity_url["type"] = "article"
                has_article = True
            elif "/status/" in expanded:
                entity_url["type"] = "tweet"
            entity_urls.append(entity_url)

    # Process media
    media_items = []
    if media:
        for m in media:
            media_type = m.type if hasattr(m, "type") else "unknown"
            item = {"type": media_type}

            if media_type in ("video", "animated_gif"):
                if hasattr(m, "variants") and m.variants:
                    mp4_variants = [v for v in m.variants if v.get("content_type") == "video/mp4"]
                    if mp4_variants:
                        mp4_variants.sort(key=lambda x: x.get("bit_rate", 0), reverse=True)
                        item["url"] = mp4_variants[0]["url"]
                if hasattr(m, "preview_image_url") and m.preview_image_url:
                    item["thumbnail"] = m.preview_image_url
                if hasattr(m, "duration_ms") and m.duration_ms:
                    item["duration_ms"] = m.duration_ms
            else:
                if hasattr(m, "url") and m.url:
                    item["url"] = m.url
                elif hasattr(m, "preview_image_url") and m.preview_image_url:
                    item["url"] = m.preview_image_url

            media_items.append(item)

    # Detect if this is part of a thread
    is_thread = False
    conversation_id = getattr(tweet, "conversation_id", None)
    in_reply_to = getattr(tweet, "in_reply_to_user_id", None)

    # Check if it's a self-reply (thread continuation)
    if in_reply_to and author and str(in_reply_to) == str(author.id if hasattr(author, "id") else ""):
        is_thread = True

    # Check for thread indicators in text
    text = tweet.text or ""
    if re.match(r"^[1-9]\d?[/\.]", text) or "🧵" in text:
        is_thread = True

    return {
        "id": tweet.id,
        "text": text,
        "username": username,
        "name": name,
        "created_at": tweet.created_at.isoformat() if hasattr(tweet, "created_at") and tweet.created_at else None,
        "url": tweet_url,
        "likes": metrics.get("like_count", 0),
        "retweets": metrics.get("retweet_count", 0),
        "replies": metrics.get("reply_count", 0),
        "quotes": metrics.get("quote_count", 0),
        "bookmarks": metrics.get("bookmark_count", 0),
        "impressions": metrics.get("impression_count", 0),
        "media": media_items,
        "urls": entity_urls,
        "is_reply": bool(in_reply_to),
        "is_retweet": text.startswith("RT @"),
        "is_thread": is_thread,
        "has_article": has_article,
        "conversation_id": conversation_id,
    }


def _simplify_user(user: Any) -> dict:
    """Convert raw user response to simplified format."""
    metrics = user.public_metrics if hasattr(user, "public_metrics") and user.public_metrics else {}

    return {
        "id": user.id,
        "username": user.username,
        "name": user.name,
        "bio": getattr(user, "description", None),
        "location": getattr(user, "location", None),
        "url": getattr(user, "url", None),
        "followers": metrics.get("followers_count", 0),
        "following": metrics.get("following_count", 0),
        "tweets": metrics.get("tweet_count", 0),
        "listed": metrics.get("listed_count", 0),
        "verified": getattr(user, "verified", False),
        "created_at": user.created_at.strftime("%Y-%m-%d") if hasattr(user, "created_at") and user.created_at else None,
        "profile_url": f"https://twitter.com/{user.username}",
    }


class TwitterAPI:
    """Wrapper for virtuals_tweepy.Client with simplified responses."""

    def __init__(self, access_token: str | None = None):
        """Initialize Twitter API client.

        Args:
            access_token: GAME Twitter access token. If not provided,
                         reads from GAME_TWITTER_ACCESS_TOKEN env var.
        """
        self._client = None
        self._access_token = access_token or os.environ.get("GAME_TWITTER_ACCESS_TOKEN")

    @property
    def client(self):
        """Lazy initialization of the Twitter client."""
        if self._client is None:
            if not self._access_token:
                raise TwitterAPIError(
                    "unauthorized",
                    "GAME_TWITTER_ACCESS_TOKEN not found. Run 'vobs auth' to authenticate.",
                    401,
                )
            try:
                from virtuals_tweepy import Client
            except ImportError:
                raise TwitterAPIError(
                    "server_error",
                    "virtuals-tweepy not installed. Run: pip install virtuals-tweepy",
                    500,
                )
            self._client = Client(game_twitter_access_token=self._access_token)
        return self._client

    def _handle_error(self, e: Exception) -> None:
        """Convert exceptions to TwitterAPIError."""
        error_str = str(e).lower()
        if "401" in error_str or "unauthorized" in error_str:
            raise TwitterAPIError("unauthorized", "Invalid or expired access token", 401)
        elif "403" in error_str or "forbidden" in error_str:
            raise TwitterAPIError("forbidden", "Action not allowed", 403)
        elif "404" in error_str or "not found" in error_str:
            raise TwitterAPIError("not_found", "Resource not found", 404)
        elif "429" in error_str or "rate limit" in error_str:
            raise TwitterAPIError("rate_limited", "Rate limit exceeded. Try again in a few minutes.", 429)
        else:
            raise TwitterAPIError("server_error", str(e), 500)

    # ========== Tweet Operations ==========

    def get_tweet(self, tweet: str) -> dict:
        """Fetch a single tweet by ID or URL."""
        tweet_id = extract_tweet_id(tweet)
        try:
            response = self.client.get_tweet(
                id=tweet_id,
                tweet_fields=["created_at", "public_metrics", "entities", "conversation_id", "in_reply_to_user_id"],
                expansions=["author_id", "attachments.media_keys"],
                user_fields=["username", "name", "verified", "public_metrics"],
                media_fields=["url", "preview_image_url", "type", "variants", "duration_ms"],
            )
            if not response.data:
                raise TwitterAPIError("not_found", f"Tweet {tweet_id} not found", 404)

            users = {}
            media = []
            if response.includes:
                if "users" in response.includes:
                    users = {u.id: u for u in response.includes["users"]}
                if "media" in response.includes:
                    media = response.includes["media"]

            return _simplify_tweet(response.data, users, media)
        except TwitterAPIError:
            raise
        except Exception as e:
            self._handle_error(e)

    def get_tweets(self, tweet_ids: list[str]) -> dict:
        """Fetch multiple tweets by IDs (batch lookup)."""
        try:
            response = self.client.get_tweets(
                ids=tweet_ids[:100],
                tweet_fields=["created_at", "public_metrics", "entities", "conversation_id", "in_reply_to_user_id"],
                expansions=["author_id", "attachments.media_keys"],
                user_fields=["username", "name", "verified", "public_metrics"],
                media_fields=["url", "preview_image_url", "type", "variants", "duration_ms"],
            )
            if not response.data:
                return {"tweets": [], "count": 0}

            users = {}
            media = []
            if response.includes:
                if "users" in response.includes:
                    users = {u.id: u for u in response.includes["users"]}
                if "media" in response.includes:
                    media = response.includes["media"]

            tweets = [_simplify_tweet(t, users, media) for t in response.data]
            return {"tweets": tweets, "count": len(tweets)}
        except TwitterAPIError:
            raise
        except Exception as e:
            self._handle_error(e)

    def create_tweet(
        self,
        text: str,
        reply_to: str | None = None,
        quote_tweet_id: str | None = None,
        media_ids: list[str] | None = None,
        poll_options: list[str] | None = None,
        poll_duration_minutes: int | None = None,
    ) -> dict:
        """Post a new tweet."""
        try:
            kwargs = {"text": text}
            if reply_to:
                kwargs["in_reply_to_tweet_id"] = reply_to
            if quote_tweet_id:
                kwargs["quote_tweet_id"] = quote_tweet_id
            if media_ids:
                kwargs["media_ids"] = media_ids
            if poll_options:
                kwargs["poll_options"] = poll_options
                kwargs["poll_duration_minutes"] = poll_duration_minutes or 1440

            response = self.client.create_tweet(**kwargs)
            tweet_id = response.data["id"]
            return {
                "success": True,
                "action": "create_tweet",
                "tweet_id": tweet_id,
                "url": f"https://twitter.com/i/status/{tweet_id}",
            }
        except TwitterAPIError:
            raise
        except Exception as e:
            self._handle_error(e)

    def delete_tweet(self, tweet_id: str) -> dict:
        """Delete a tweet by ID."""
        try:
            self.client.delete_tweet(id=tweet_id)
            return {"success": True, "action": "delete_tweet", "tweet_id": tweet_id}
        except TwitterAPIError:
            raise
        except Exception as e:
            self._handle_error(e)

    def get_thread(self, tweet: str, include_replies: bool = False) -> dict:
        """Fetch entire thread from any tweet in the conversation."""
        tweet_id = extract_tweet_id(tweet)
        try:
            # First get the tweet to find conversation_id and author
            initial = self.client.get_tweet(
                id=tweet_id,
                tweet_fields=["conversation_id", "author_id"],
                expansions=["author_id"],
                user_fields=["username", "name"],
            )
            if not initial.data:
                raise TwitterAPIError("not_found", f"Tweet {tweet_id} not found", 404)

            conversation_id = initial.data.conversation_id
            author_id = initial.data.author_id

            author = None
            if initial.includes and "users" in initial.includes:
                author = initial.includes["users"][0]

            # Search for all tweets in conversation from this author
            query = f"conversation_id:{conversation_id} from:{author.username}"
            if include_replies:
                query = f"conversation_id:{conversation_id}"

            response = self.client.search_recent_tweets(
                query=query,
                max_results=100,
                tweet_fields=["created_at", "public_metrics", "entities", "in_reply_to_user_id"],
                expansions=["author_id"],
                user_fields=["username", "name"],
            )

            tweets = []
            if response.data:
                users = {}
                if response.includes and "users" in response.includes:
                    users = {u.id: u for u in response.includes["users"]}

                # Sort by ID (chronological)
                sorted_tweets = sorted(response.data, key=lambda t: int(t.id))
                for i, t in enumerate(sorted_tweets, 1):
                    simplified = _simplify_tweet(t, users)
                    simplified["position"] = i
                    tweets.append(simplified)

            return {
                "thread_id": conversation_id,
                "author": {"username": author.username, "name": author.name} if author else None,
                "tweets": tweets,
                "count": len(tweets),
            }
        except TwitterAPIError:
            raise
        except Exception as e:
            self._handle_error(e)

    def get_article(self, tweet: str) -> dict | None:
        """Extract full content from an X Article using Playwright."""
        tweet_id = extract_tweet_id(tweet)

        try:
            from playwright.sync_api import sync_playwright
        except ImportError:
            raise TwitterAPIError(
                "playwright_error",
                "playwright not installed. Install with: pip install playwright && playwright install chromium",
            )

        # First get the tweet to find author username
        tweet_data = self.get_tweet(tweet)
        username = tweet_data.get("username", "unknown")
        tweet_url = f"https://x.com/{username}/status/{tweet_id}"

        def _launch_browser(p, retry: bool = True):
            try:
                return p.chromium.launch(headless=True)
            except Exception as e:
                if retry and "Executable doesn't exist" in str(e):
                    if _ensure_playwright_browsers():
                        return _launch_browser(p, retry=False)
                raise

        try:
            with sync_playwright() as p:
                browser = _launch_browser(p)
                page = browser.new_page()
                page.goto(tweet_url, wait_until="domcontentloaded", timeout=60000)
                page.wait_for_timeout(5000)

                article_content = page.evaluate(
                    """
                    () => {
                        const article = document.querySelector('article');
                        if (!article) return null;

                        const headings = article.querySelectorAll('h2');
                        if (headings.length < 2) return null;

                        const titleCandidates = article.querySelectorAll('[dir="auto"]');
                        let title = '';
                        for (const el of titleCandidates) {
                            const text = el.innerText.trim();
                            if (text.length > 10 && text.length < 100 && !text.startsWith('@')) {
                                title = text;
                                break;
                            }
                        }

                        const fullText = article.innerText;
                        const images = [];
                        const imgElements = article.querySelectorAll('img[src*="pbs.twimg.com/media"]');
                        imgElements.forEach(img => {
                            if (img.src && !images.includes(img.src)) {
                                images.push(img.src);
                            }
                        });

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
                """
                )

                browser.close()

                if not article_content:
                    raise TwitterAPIError("article_not_found", "Tweet exists but is not an article")

                return {
                    "title": article_content.get("title"),
                    "content": article_content.get("content"),
                    "sections": article_content.get("sections", []),
                    "images": article_content.get("images", []),
                    "tweet_id": tweet_id,
                    "author": username,
                }

        except TwitterAPIError:
            raise
        except Exception as e:
            raise TwitterAPIError("playwright_error", f"Browser automation failed: {e}")

    # ========== Search ==========

    def search_tweets(
        self,
        query: str,
        max_results: int = 10,
        pagination_token: str | None = None,
    ) -> dict:
        """Search recent tweets (last 7 days)."""
        try:
            kwargs = {
                "query": query,
                "max_results": min(max(max_results, 10), 100),
                "tweet_fields": ["created_at", "public_metrics", "entities", "conversation_id", "in_reply_to_user_id"],
                "expansions": ["author_id"],
                "user_fields": ["username", "name", "verified"],
            }
            if pagination_token:
                kwargs["next_token"] = pagination_token

            response = self.client.search_recent_tweets(**kwargs)

            if not response.data:
                return {"tweets": [], "count": 0, "next_token": None}

            users = {}
            if response.includes and "users" in response.includes:
                users = {u.id: u for u in response.includes["users"]}

            tweets = [_simplify_tweet(t, users) for t in response.data]
            next_token = response.meta.get("next_token") if hasattr(response, "meta") and response.meta else None

            return {"tweets": tweets, "count": len(tweets), "next_token": next_token}
        except TwitterAPIError:
            raise
        except Exception as e:
            self._handle_error(e)

    def search_all_tweets(
        self,
        query: str,
        max_results: int = 10,
        start_time: str | None = None,
        end_time: str | None = None,
        pagination_token: str | None = None,
    ) -> dict:
        """Search full tweet archive (requires elevated access)."""
        try:
            kwargs = {
                "query": query,
                "max_results": min(max(max_results, 10), 500),
                "tweet_fields": ["created_at", "public_metrics", "entities", "conversation_id", "in_reply_to_user_id"],
                "expansions": ["author_id"],
                "user_fields": ["username", "name", "verified"],
            }
            if start_time:
                kwargs["start_time"] = start_time
            if end_time:
                kwargs["end_time"] = end_time
            if pagination_token:
                kwargs["next_token"] = pagination_token

            response = self.client.search_all_tweets(**kwargs)

            if not response.data:
                return {"tweets": [], "count": 0, "next_token": None}

            users = {}
            if response.includes and "users" in response.includes:
                users = {u.id: u for u in response.includes["users"]}

            tweets = [_simplify_tweet(t, users) for t in response.data]
            next_token = response.meta.get("next_token") if hasattr(response, "meta") and response.meta else None

            return {"tweets": tweets, "count": len(tweets), "next_token": next_token}
        except TwitterAPIError:
            raise
        except Exception as e:
            self._handle_error(e)

    def count_tweets(
        self,
        query: str,
        granularity: str = "day",
        start_time: str | None = None,
        end_time: str | None = None,
    ) -> dict:
        """Count tweets matching a query over time."""
        try:
            kwargs = {
                "query": query,
                "granularity": granularity,
            }
            if start_time:
                kwargs["start_time"] = start_time
            if end_time:
                kwargs["end_time"] = end_time

            response = self.client.get_recent_tweets_count(**kwargs)

            counts = []
            total = 0
            if response.data:
                for c in response.data:
                    counts.append({"start": c.start.isoformat(), "end": c.end.isoformat(), "count": c.tweet_count})
                    total += c.tweet_count

            return {"counts": counts, "total": total, "granularity": granularity}
        except TwitterAPIError:
            raise
        except Exception as e:
            self._handle_error(e)

    # ========== Timelines ==========

    def get_home_timeline(
        self,
        max_results: int = 10,
        pagination_token: str | None = None,
    ) -> dict:
        """Get your home timeline."""
        try:
            kwargs = {
                "max_results": min(max(max_results, 1), 100),
                "tweet_fields": ["created_at", "public_metrics", "entities", "conversation_id", "in_reply_to_user_id"],
                "expansions": ["author_id"],
                "user_fields": ["username", "name"],
            }
            if pagination_token:
                kwargs["pagination_token"] = pagination_token

            response = self.client.get_home_timeline(**kwargs)

            if not response.data:
                return {"tweets": [], "count": 0, "next_token": None}

            users = {}
            if response.includes and "users" in response.includes:
                users = {u.id: u for u in response.includes["users"]}

            tweets = [_simplify_tweet(t, users) for t in response.data]
            next_token = response.meta.get("next_token") if hasattr(response, "meta") and response.meta else None

            return {"tweets": tweets, "count": len(tweets), "next_token": next_token}
        except TwitterAPIError:
            raise
        except Exception as e:
            self._handle_error(e)

    def get_user_tweets(
        self,
        username: str | None = None,
        user_id: str | None = None,
        max_results: int = 10,
        since_id: str | None = None,
        exclude_retweets: bool = False,
        exclude_replies: bool = False,
        pagination_token: str | None = None,
    ) -> dict:
        """Get tweets from a specific user."""
        if not username and not user_id:
            raise TwitterAPIError("invalid_params", "Either username or user_id is required", 400)

        try:
            # Get user ID if username provided
            if username and not user_id:
                user_response = self.client.get_user(username=username.lstrip("@"))
                if not user_response.data:
                    raise TwitterAPIError("not_found", f"User @{username} not found", 404)
                user_id = user_response.data.id

            exclude = []
            if exclude_retweets:
                exclude.append("retweets")
            if exclude_replies:
                exclude.append("replies")

            kwargs = {
                "id": user_id,
                "max_results": min(max(max_results, 5), 100),
                "tweet_fields": ["created_at", "public_metrics", "entities", "conversation_id", "in_reply_to_user_id"],
                "expansions": ["author_id"],
                "user_fields": ["username", "name"],
            }
            if exclude:
                kwargs["exclude"] = exclude
            if since_id:
                kwargs["since_id"] = since_id
            if pagination_token:
                kwargs["pagination_token"] = pagination_token

            response = self.client.get_users_tweets(**kwargs)

            if not response.data:
                return {"tweets": [], "count": 0, "next_token": None}

            users = {}
            if response.includes and "users" in response.includes:
                users = {u.id: u for u in response.includes["users"]}

            tweets = [_simplify_tweet(t, users) for t in response.data]
            next_token = response.meta.get("next_token") if hasattr(response, "meta") and response.meta else None

            return {"tweets": tweets, "count": len(tweets), "next_token": next_token}
        except TwitterAPIError:
            raise
        except Exception as e:
            self._handle_error(e)

    def get_mentions(
        self,
        max_results: int = 10,
        since_id: str | None = None,
        pagination_token: str | None = None,
    ) -> dict:
        """Get tweets mentioning you."""
        try:
            me = self.client.get_me()
            my_id = me.data.id

            kwargs = {
                "id": my_id,
                "max_results": min(max(max_results, 5), 100),
                "tweet_fields": ["created_at", "public_metrics", "entities", "conversation_id", "in_reply_to_user_id"],
                "expansions": ["author_id"],
                "user_fields": ["username", "name"],
            }
            if since_id:
                kwargs["since_id"] = since_id
            if pagination_token:
                kwargs["pagination_token"] = pagination_token

            response = self.client.get_users_mentions(**kwargs)

            if not response.data:
                return {"tweets": [], "count": 0, "next_token": None}

            users = {}
            if response.includes and "users" in response.includes:
                users = {u.id: u for u in response.includes["users"]}

            tweets = [_simplify_tweet(t, users) for t in response.data]
            next_token = response.meta.get("next_token") if hasattr(response, "meta") and response.meta else None

            return {"tweets": tweets, "count": len(tweets), "next_token": next_token}
        except TwitterAPIError:
            raise
        except Exception as e:
            self._handle_error(e)

    # ========== User Lookup ==========

    def get_me(self) -> dict:
        """Get your own profile."""
        try:
            response = self.client.get_me(
                user_fields=["created_at", "description", "public_metrics", "verified", "location", "url"]
            )
            if not response.data:
                raise TwitterAPIError("unauthorized", "Could not fetch profile", 401)
            return _simplify_user(response.data)
        except TwitterAPIError:
            raise
        except Exception as e:
            self._handle_error(e)

    def get_user(self, username: str | None = None, user_id: str | None = None) -> dict:
        """Get a user's profile."""
        if not username and not user_id:
            raise TwitterAPIError("invalid_params", "Either username or user_id is required", 400)

        try:
            kwargs = {"user_fields": ["created_at", "description", "public_metrics", "verified", "location", "url"]}
            if username:
                kwargs["username"] = username.lstrip("@")
                response = self.client.get_user(**kwargs)
            else:
                kwargs["id"] = user_id
                response = self.client.get_user(**kwargs)

            if not response.data:
                raise TwitterAPIError("not_found", f"User not found", 404)
            return _simplify_user(response.data)
        except TwitterAPIError:
            raise
        except Exception as e:
            self._handle_error(e)

    def get_users(self, usernames: list[str] | None = None, user_ids: list[str] | None = None) -> dict:
        """Get multiple users (batch lookup)."""
        if not usernames and not user_ids:
            raise TwitterAPIError("invalid_params", "Either usernames or user_ids is required", 400)

        try:
            kwargs = {"user_fields": ["created_at", "description", "public_metrics", "verified", "location", "url"]}
            if usernames:
                kwargs["usernames"] = [u.lstrip("@") for u in usernames[:100]]
                response = self.client.get_users(**kwargs)
            else:
                kwargs["ids"] = user_ids[:100]
                response = self.client.get_users(**kwargs)

            if not response.data:
                return {"users": [], "count": 0}

            users = [_simplify_user(u) for u in response.data]
            return {"users": users, "count": len(users)}
        except TwitterAPIError:
            raise
        except Exception as e:
            self._handle_error(e)

    def get_followers(
        self,
        username: str | None = None,
        user_id: str | None = None,
        max_results: int = 100,
        pagination_token: str | None = None,
    ) -> dict:
        """Get a user's followers."""
        if not username and not user_id:
            raise TwitterAPIError("invalid_params", "Either username or user_id is required", 400)

        try:
            if username and not user_id:
                user_response = self.client.get_user(username=username.lstrip("@"))
                if not user_response.data:
                    raise TwitterAPIError("not_found", f"User @{username} not found", 404)
                user_id = user_response.data.id

            kwargs = {
                "id": user_id,
                "max_results": min(max(max_results, 1), 1000),
                "user_fields": ["created_at", "description", "public_metrics", "verified"],
            }
            if pagination_token:
                kwargs["pagination_token"] = pagination_token

            response = self.client.get_users_followers(**kwargs)

            if not response.data:
                return {"users": [], "count": 0, "next_token": None}

            users = [_simplify_user(u) for u in response.data]
            next_token = response.meta.get("next_token") if hasattr(response, "meta") and response.meta else None

            return {"users": users, "count": len(users), "next_token": next_token}
        except TwitterAPIError:
            raise
        except Exception as e:
            self._handle_error(e)

    def get_following(
        self,
        username: str | None = None,
        user_id: str | None = None,
        max_results: int = 100,
        pagination_token: str | None = None,
    ) -> dict:
        """Get accounts a user follows."""
        if not username and not user_id:
            raise TwitterAPIError("invalid_params", "Either username or user_id is required", 400)

        try:
            if username and not user_id:
                user_response = self.client.get_user(username=username.lstrip("@"))
                if not user_response.data:
                    raise TwitterAPIError("not_found", f"User @{username} not found", 404)
                user_id = user_response.data.id

            kwargs = {
                "id": user_id,
                "max_results": min(max(max_results, 1), 1000),
                "user_fields": ["created_at", "description", "public_metrics", "verified"],
            }
            if pagination_token:
                kwargs["pagination_token"] = pagination_token

            response = self.client.get_users_following(**kwargs)

            if not response.data:
                return {"users": [], "count": 0, "next_token": None}

            users = [_simplify_user(u) for u in response.data]
            next_token = response.meta.get("next_token") if hasattr(response, "meta") and response.meta else None

            return {"users": users, "count": len(users), "next_token": next_token}
        except TwitterAPIError:
            raise
        except Exception as e:
            self._handle_error(e)

    # ========== Social Actions ==========

    def _get_user_id(self, username: str | None = None, user_id: str | None = None) -> str:
        """Helper to get user_id from username if needed."""
        if user_id:
            return user_id
        if username:
            user_response = self.client.get_user(username=username.lstrip("@"))
            if not user_response.data:
                raise TwitterAPIError("not_found", f"User @{username} not found", 404)
            return user_response.data.id
        raise TwitterAPIError("invalid_params", "Either username or user_id is required", 400)

    def follow(self, username: str | None = None, user_id: str | None = None) -> dict:
        """Follow a user."""
        try:
            target_id = self._get_user_id(username, user_id)
            me = self.client.get_me()
            self.client.follow_user(target_user_id=target_id)
            return {"success": True, "action": "follow", "user_id": target_id}
        except TwitterAPIError:
            raise
        except Exception as e:
            self._handle_error(e)

    def unfollow(self, username: str | None = None, user_id: str | None = None) -> dict:
        """Unfollow a user."""
        try:
            target_id = self._get_user_id(username, user_id)
            me = self.client.get_me()
            self.client.unfollow_user(target_user_id=target_id)
            return {"success": True, "action": "unfollow", "user_id": target_id}
        except TwitterAPIError:
            raise
        except Exception as e:
            self._handle_error(e)

    def mute(self, username: str | None = None, user_id: str | None = None) -> dict:
        """Mute a user."""
        try:
            target_id = self._get_user_id(username, user_id)
            self.client.mute(target_user_id=target_id)
            return {"success": True, "action": "mute", "user_id": target_id}
        except TwitterAPIError:
            raise
        except Exception as e:
            self._handle_error(e)

    def unmute(self, username: str | None = None, user_id: str | None = None) -> dict:
        """Unmute a user."""
        try:
            target_id = self._get_user_id(username, user_id)
            self.client.unmute(target_user_id=target_id)
            return {"success": True, "action": "unmute", "user_id": target_id}
        except TwitterAPIError:
            raise
        except Exception as e:
            self._handle_error(e)

    def block(self, username: str | None = None, user_id: str | None = None) -> dict:
        """Block a user."""
        try:
            target_id = self._get_user_id(username, user_id)
            self.client.block(target_user_id=target_id)
            return {"success": True, "action": "block", "user_id": target_id}
        except TwitterAPIError:
            raise
        except Exception as e:
            self._handle_error(e)

    def unblock(self, username: str | None = None, user_id: str | None = None) -> dict:
        """Unblock a user."""
        try:
            target_id = self._get_user_id(username, user_id)
            self.client.unblock(target_user_id=target_id)
            return {"success": True, "action": "unblock", "user_id": target_id}
        except TwitterAPIError:
            raise
        except Exception as e:
            self._handle_error(e)

    def get_muted(self, max_results: int = 100, pagination_token: str | None = None) -> dict:
        """Get list of muted users."""
        try:
            kwargs = {
                "max_results": min(max(max_results, 1), 1000),
                "user_fields": ["created_at", "description", "public_metrics", "verified"],
            }
            if pagination_token:
                kwargs["pagination_token"] = pagination_token

            response = self.client.get_muted(**kwargs)

            if not response.data:
                return {"users": [], "count": 0, "next_token": None}

            users = [_simplify_user(u) for u in response.data]
            next_token = response.meta.get("next_token") if hasattr(response, "meta") and response.meta else None

            return {"users": users, "count": len(users), "next_token": next_token}
        except TwitterAPIError:
            raise
        except Exception as e:
            self._handle_error(e)

    def get_blocked(self, max_results: int = 100, pagination_token: str | None = None) -> dict:
        """Get list of blocked users."""
        try:
            kwargs = {
                "max_results": min(max(max_results, 1), 1000),
                "user_fields": ["created_at", "description", "public_metrics", "verified"],
            }
            if pagination_token:
                kwargs["pagination_token"] = pagination_token

            response = self.client.get_blocked(**kwargs)

            if not response.data:
                return {"users": [], "count": 0, "next_token": None}

            users = [_simplify_user(u) for u in response.data]
            next_token = response.meta.get("next_token") if hasattr(response, "meta") and response.meta else None

            return {"users": users, "count": len(users), "next_token": next_token}
        except TwitterAPIError:
            raise
        except Exception as e:
            self._handle_error(e)

    # ========== Engagement ==========

    def like(self, tweet_id: str) -> dict:
        """Like a tweet."""
        try:
            self.client.like(tweet_id=tweet_id)
            return {"success": True, "action": "like", "tweet_id": tweet_id}
        except TwitterAPIError:
            raise
        except Exception as e:
            self._handle_error(e)

    def unlike(self, tweet_id: str) -> dict:
        """Unlike a tweet."""
        try:
            self.client.unlike(tweet_id=tweet_id)
            return {"success": True, "action": "unlike", "tweet_id": tweet_id}
        except TwitterAPIError:
            raise
        except Exception as e:
            self._handle_error(e)

    def retweet(self, tweet_id: str) -> dict:
        """Retweet a tweet."""
        try:
            self.client.retweet(tweet_id=tweet_id)
            return {"success": True, "action": "retweet", "tweet_id": tweet_id}
        except TwitterAPIError:
            raise
        except Exception as e:
            self._handle_error(e)

    def unretweet(self, tweet_id: str) -> dict:
        """Unretweet a tweet."""
        try:
            self.client.unretweet(tweet_id=tweet_id)
            return {"success": True, "action": "unretweet", "tweet_id": tweet_id}
        except TwitterAPIError:
            raise
        except Exception as e:
            self._handle_error(e)

    def bookmark(self, tweet_id: str) -> dict:
        """Bookmark a tweet."""
        try:
            self.client.bookmark(tweet_id=tweet_id)
            return {"success": True, "action": "bookmark", "tweet_id": tweet_id}
        except TwitterAPIError:
            raise
        except Exception as e:
            self._handle_error(e)

    def remove_bookmark(self, tweet_id: str) -> dict:
        """Remove a bookmark."""
        try:
            self.client.remove_bookmark(tweet_id=tweet_id)
            return {"success": True, "action": "remove_bookmark", "tweet_id": tweet_id}
        except TwitterAPIError:
            raise
        except Exception as e:
            self._handle_error(e)

    def get_bookmarks(self, max_results: int = 10, pagination_token: str | None = None) -> dict:
        """Get your bookmarked tweets."""
        try:
            kwargs = {
                "max_results": min(max(max_results, 1), 100),
                "tweet_fields": ["created_at", "public_metrics", "entities", "conversation_id", "in_reply_to_user_id"],
                "expansions": ["author_id"],
                "user_fields": ["username", "name"],
            }
            if pagination_token:
                kwargs["pagination_token"] = pagination_token

            response = self.client.get_bookmarks(**kwargs)

            if not response.data:
                return {"tweets": [], "count": 0, "next_token": None}

            users = {}
            if response.includes and "users" in response.includes:
                users = {u.id: u for u in response.includes["users"]}

            tweets = [_simplify_tweet(t, users) for t in response.data]
            next_token = response.meta.get("next_token") if hasattr(response, "meta") and response.meta else None

            return {"tweets": tweets, "count": len(tweets), "next_token": next_token}
        except TwitterAPIError:
            raise
        except Exception as e:
            self._handle_error(e)

    def get_liking_users(
        self,
        tweet_id: str,
        max_results: int = 100,
        pagination_token: str | None = None,
    ) -> dict:
        """Get users who liked a tweet."""
        try:
            kwargs = {
                "id": tweet_id,
                "max_results": min(max(max_results, 1), 100),
                "user_fields": ["created_at", "description", "public_metrics", "verified"],
            }
            if pagination_token:
                kwargs["pagination_token"] = pagination_token

            response = self.client.get_liking_users(**kwargs)

            if not response.data:
                return {"users": [], "count": 0, "next_token": None}

            users = [_simplify_user(u) for u in response.data]
            next_token = response.meta.get("next_token") if hasattr(response, "meta") and response.meta else None

            return {"users": users, "count": len(users), "next_token": next_token}
        except TwitterAPIError:
            raise
        except Exception as e:
            self._handle_error(e)

    def get_retweeters(
        self,
        tweet_id: str,
        max_results: int = 100,
        pagination_token: str | None = None,
    ) -> dict:
        """Get users who retweeted a tweet."""
        try:
            kwargs = {
                "id": tweet_id,
                "max_results": min(max(max_results, 1), 100),
                "user_fields": ["created_at", "description", "public_metrics", "verified"],
            }
            if pagination_token:
                kwargs["pagination_token"] = pagination_token

            response = self.client.get_retweeters(**kwargs)

            if not response.data:
                return {"users": [], "count": 0, "next_token": None}

            users = [_simplify_user(u) for u in response.data]
            next_token = response.meta.get("next_token") if hasattr(response, "meta") and response.meta else None

            return {"users": users, "count": len(users), "next_token": next_token}
        except TwitterAPIError:
            raise
        except Exception as e:
            self._handle_error(e)

    # ========== Replies ==========

    def hide_reply(self, tweet_id: str) -> dict:
        """Hide a reply to your tweet."""
        try:
            self.client.hide_reply(id=tweet_id)
            return {"success": True, "action": "hide_reply", "tweet_id": tweet_id}
        except TwitterAPIError:
            raise
        except Exception as e:
            self._handle_error(e)

    def unhide_reply(self, tweet_id: str) -> dict:
        """Unhide a reply."""
        try:
            self.client.unhide_reply(id=tweet_id)
            return {"success": True, "action": "unhide_reply", "tweet_id": tweet_id}
        except TwitterAPIError:
            raise
        except Exception as e:
            self._handle_error(e)
