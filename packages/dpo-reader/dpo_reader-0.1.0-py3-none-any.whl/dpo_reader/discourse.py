"""Discourse thread fetcher and parser."""

from __future__ import annotations

import re
from dataclasses import dataclass
from urllib.parse import urlparse

import httpx
from bs4 import BeautifulSoup


@dataclass
class Post:
    """A single post from a Discourse thread."""

    id: int
    number: int
    author: str
    username: str
    content: str
    created_at: str
    reply_to: int | None = None


@dataclass
class Thread:
    """A complete Discourse thread."""

    id: int
    title: str
    url: str
    posts: list[Post]

    @property
    def authors(self) -> set[str]:
        """Get unique authors in the thread."""
        return {p.username for p in self.posts}

    @property
    def author_post_counts(self) -> dict[str, int]:
        """Get post count per author, sorted by count descending."""
        counts: dict[str, int] = {}
        for post in self.posts:
            counts[post.username] = counts.get(post.username, 0) + 1
        return dict(sorted(counts.items(), key=lambda x: x[1], reverse=True))


def parse_discourse_url(url: str) -> tuple[str, str]:
    """Extract base URL and topic identifier from a Discourse thread URL.

    Args:
        url: Full Discourse thread URL

    Returns:
        Tuple of (base_url, topic_identifier) where identifier can be ID or slug
    """
    parsed = urlparse(url)
    base = f"{parsed.scheme}://{parsed.netloc}"

    # Try to extract topic ID from path like /t/slug/12345 or /t/slug/12345/123
    match = re.search(r"/t/[^/]+/(\d+)", parsed.path)
    if match:
        return base, match.group(1)

    # Fall back to slug-only URL like /t/slug or /t/slug/
    match = re.search(r"/t/([^/]+)", parsed.path)
    if match:
        return base, match.group(1)

    msg = f"Could not parse topic from URL: {url}"
    raise ValueError(msg)


def html_to_text(html: str) -> str:
    """Convert HTML content to plain text."""
    soup = BeautifulSoup(html, "html.parser")

    # Remove quotes (we'll handle them specially)
    for quote in soup.find_all("aside", class_="quote"):
        quote.decompose()

    # Convert links to just their text
    for link in soup.find_all("a"):
        link.replace_with(link.get_text())

    # Convert code blocks
    for code in soup.find_all("code"):
        code.replace_with(f" {code.get_text()} ")

    # Get text and clean up whitespace
    text = soup.get_text(separator=" ")
    text = re.sub(r"\s+", " ", text).strip()

    return text


async def fetch_thread(url: str, max_posts: int | None = None) -> Thread:
    """Fetch a complete Discourse thread.

    Args:
        url: The Discourse thread URL
        max_posts: Maximum number of posts to fetch (None for all)

    Returns:
        Thread object with all posts
    """
    base_url, topic_identifier = parse_discourse_url(url)

    async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
        # Fetch initial thread data (works with both ID and slug)
        resp = await client.get(f"{base_url}/t/{topic_identifier}.json")
        resp.raise_for_status()
        data = resp.json()

        # Get the actual topic ID from response
        topic_id = data["id"]
        title = data["title"]
        post_stream = data["post_stream"]

        # Get all post IDs from stream
        all_post_ids = post_stream["stream"]
        if max_posts:
            all_post_ids = all_post_ids[:max_posts]

        # First batch of posts is included in initial response
        posts_data = {p["id"]: p for p in post_stream["posts"]}

        # Fetch remaining posts in batches of 20
        missing_ids = [pid for pid in all_post_ids if pid not in posts_data]

        for i in range(0, len(missing_ids), 20):
            batch = missing_ids[i : i + 20]
            params = [("post_ids[]", str(pid)) for pid in batch]
            resp = await client.get(f"{base_url}/t/{topic_id}/posts.json", params=params)
            resp.raise_for_status()
            batch_data = resp.json()

            for post in batch_data.get("post_stream", {}).get("posts", []):
                posts_data[post["id"]] = post

        # Convert to Post objects in order
        posts = []
        for pid in all_post_ids:
            if pid not in posts_data:
                continue
            p = posts_data[pid]
            posts.append(
                Post(
                    id=p["id"],
                    number=p["post_number"],
                    author=p.get("name") or p["username"],
                    username=p["username"],
                    content=html_to_text(p["cooked"]),
                    created_at=p["created_at"],
                    reply_to=p.get("reply_to_post_number"),
                )
            )

    return Thread(id=topic_id, title=title, url=url, posts=posts)


def fetch_thread_sync(url: str, max_posts: int | None = None) -> Thread:
    """Synchronous wrapper for fetch_thread."""
    import asyncio

    return asyncio.run(fetch_thread(url, max_posts))
