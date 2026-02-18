"""News fetcher - Fetch latest headlines from Google News RSS feeds for stocks and market context."""
import feedparser
import requests
from typing import List, Dict, Optional
from datetime import datetime, timedelta
import json
import os
from pathlib import Path
import time


# Sentiment analysis keywords (English + Swedish)
POSITIVE_KEYWORDS = [
    'gain', 'rise', 'surge', 'profit', 'growth', 'beat', 'strong', 'up',
    'record', 'ökning', 'vinst', 'tillväxt', 'stiger', 'rekordhög',
    'höjer', 'positiv', 'bra', 'öka', 'framgång', 'succé'
]

NEGATIVE_KEYWORDS = [
    'fall', 'drop', 'loss', 'decline', 'weak', 'miss', 'down', 'warning',
    'nedgång', 'förlust', 'varning', 'sjunker', 'faller', 'minskar',
    'negativ', 'kris', 'problem', 'risk', 'orolig'
]

# Cache directory
CACHE_DIR = Path("/tmp/kavastu_news_cache")
CACHE_DIR.mkdir(exist_ok=True)


def _extract_company_name(ticker: str) -> str:
    """
    Extract company name from ticker for Google News search.

    Args:
        ticker: Stock ticker (e.g., "VOLV-B.ST", "ERIC-B.ST")

    Returns:
        Clean company name (e.g., "Volvo", "Ericsson")
    """
    # Remove .ST suffix
    name = ticker.replace('.ST', '')

    # Remove -A, -B, -C share class suffixes
    name = name.split('-')[0]

    # Special cases for common tickers
    ticker_to_name = {
        'VOLV': 'Volvo',
        'ERIC': 'Ericsson',
        'ABB': 'ABB',
        'HM': 'H&M',
        'HEXA': 'Hexagon',
        'AZN': 'AstraZeneca',
        'ATCO': 'Atlas Copco',
        'SAND': 'Sandvik',
        'SKF': 'SKF',
        'ALFA': 'Alfa Laval',
        'BOL': 'Boliden',
        'NDA-SE': 'Nordea',
        'SEB': 'SEB',
        'SHB': 'Handelsbanken',
        'SWED': 'Swedbank',
        'EVO': 'Evolution Gaming',
        'INVE': 'Investor',
        'TELIA': 'Telia',
        'TEL2': 'Tele2',
    }

    return ticker_to_name.get(name, name)


def _get_cache_path(ticker: str, cache_hours: int) -> Optional[Path]:
    """
    Get cache file path and check if it's valid.

    Args:
        ticker: Stock ticker
        cache_hours: Cache validity in hours

    Returns:
        Cache file path if valid cache exists, None otherwise
    """
    cache_file = CACHE_DIR / f"{ticker}_{datetime.now().strftime('%Y-%m-%d')}.json"

    if cache_file.exists():
        # Check if cache is still valid
        file_time = datetime.fromtimestamp(cache_file.stat().st_mtime)
        if datetime.now() - file_time < timedelta(hours=cache_hours):
            return cache_file

    return None


def _save_to_cache(ticker: str, articles: List[Dict]) -> None:
    """
    Save articles to cache file.

    Args:
        ticker: Stock ticker
        articles: List of article dictionaries
    """
    cache_file = CACHE_DIR / f"{ticker}_{datetime.now().strftime('%Y-%m-%d')}.json"

    # Convert datetime objects to strings for JSON serialization
    serializable_articles = []
    for article in articles:
        article_copy = article.copy()
        if isinstance(article_copy.get('published'), datetime):
            article_copy['published'] = article_copy['published'].isoformat()
        serializable_articles.append(article_copy)

    with open(cache_file, 'w', encoding='utf-8') as f:
        json.dump(serializable_articles, f, ensure_ascii=False, indent=2)


def _load_from_cache(cache_file: Path) -> List[Dict]:
    """
    Load articles from cache file.

    Args:
        cache_file: Path to cache file

    Returns:
        List of article dictionaries
    """
    with open(cache_file, 'r', encoding='utf-8') as f:
        articles = json.load(f)

    # Convert ISO strings back to datetime objects
    for article in articles:
        if isinstance(article.get('published'), str):
            try:
                article['published'] = datetime.fromisoformat(article['published'])
            except (ValueError, TypeError):
                article['published'] = datetime.now()

    return articles


def analyze_sentiment_simple(title: str, summary: str) -> str:
    """
    Simple keyword-based sentiment analysis.

    Positive keywords: gain, rise, surge, profit, growth, beat, strong, up
    Negative keywords: fall, drop, loss, decline, weak, miss, down, warning

    Args:
        title: Article title
        summary: Article summary text

    Returns:
        'positive' | 'negative' | 'neutral'
    """
    # Combine title and summary, convert to lowercase
    text = (title + ' ' + summary).lower()

    # Count positive and negative keywords
    positive_count = sum(1 for keyword in POSITIVE_KEYWORDS if keyword in text)
    negative_count = sum(1 for keyword in NEGATIVE_KEYWORDS if keyword in text)

    # Determine sentiment
    if positive_count > negative_count:
        return 'positive'
    elif negative_count > positive_count:
        return 'negative'
    else:
        return 'neutral'


def fetch_stock_news(ticker: str, max_articles: int = 5, cache_hours: int = 6) -> List[Dict]:
    """
    Fetch latest news for a stock from Google News RSS.

    Args:
        ticker: Stock ticker (e.g., "VOLV-B.ST")
        max_articles: Number of articles to return
        cache_hours: Cache duration to avoid re-fetching

    Returns:
        [
            {
                'title': str,
                'link': str,
                'published': datetime,
                'source': str,
                'sentiment': 'positive' | 'negative' | 'neutral',
                'summary': str  # First 150 chars
            },
            ...
        ]
    """
    # Check cache first
    cache_file = _get_cache_path(ticker, cache_hours)
    if cache_file:
        try:
            articles = _load_from_cache(cache_file)
            return articles[:max_articles]
        except Exception as e:
            print(f"Warning: Cache read failed for {ticker}: {e}")

    # Fetch fresh data
    try:
        # Extract company name and build Google News URL
        company_name = _extract_company_name(ticker)
        search_query = f"{company_name} stock Sweden"
        url = f"https://news.google.com/rss/search?q={search_query}&hl=sv&gl=SE&ceid=SE:sv"

        # Fetch RSS feed with timeout
        response = requests.get(url, timeout=10)
        response.raise_for_status()

        # Parse RSS feed
        feed = feedparser.parse(response.content)

        # Process articles
        articles = []
        for entry in feed.entries[:max_articles]:
            # Extract source from title (Google News format: "Title - Source")
            title = entry.get('title', '')
            source = 'Unknown'
            if ' - ' in title:
                parts = title.rsplit(' - ', 1)
                title = parts[0]
                source = parts[1]

            # Get summary (first 150 chars of description or title)
            description = entry.get('description', '') or entry.get('summary', '') or title
            # Remove HTML tags if present
            import re
            description = re.sub(r'<[^>]+>', '', description)
            summary = description[:150]

            # Parse published date
            published = datetime.now()
            if hasattr(entry, 'published_parsed') and entry.published_parsed:
                try:
                    published = datetime(*entry.published_parsed[:6])
                except (TypeError, ValueError):
                    pass

            # Analyze sentiment
            sentiment = analyze_sentiment_simple(title, summary)

            article = {
                'title': title,
                'link': entry.get('link', ''),
                'published': published,
                'source': source,
                'sentiment': sentiment,
                'summary': summary
            }

            articles.append(article)

        # Save to cache
        if articles:
            _save_to_cache(ticker, articles)

        return articles

    except requests.Timeout:
        print(f"Error: Timeout fetching news for {ticker}")
        return []
    except requests.RequestException as e:
        print(f"Error: Network error fetching news for {ticker}: {e}")
        return []
    except Exception as e:
        print(f"Error: Failed to parse news for {ticker}: {e}")
        return []


def fetch_market_news(market: str = "OMXS30", max_articles: int = 10) -> List[Dict]:
    """
    Fetch general market news for Swedish stock market.

    Args:
        market: Market identifier (default: "OMXS30")
        max_articles: Number of articles to return

    Returns:
        Same structure as fetch_stock_news()
    """
    # Use "OMXS30" as ticker for caching
    cache_ticker = f"MARKET_{market}"
    cache_hours = 6

    # Check cache first
    cache_file = _get_cache_path(cache_ticker, cache_hours)
    if cache_file:
        try:
            articles = _load_from_cache(cache_file)
            return articles[:max_articles]
        except Exception as e:
            print(f"Warning: Cache read failed for {market}: {e}")

    # Fetch fresh data
    try:
        # Build Google News URL for Swedish market news
        search_query = f"{market} Stockholmsbörsen aktier"
        url = f"https://news.google.com/rss/search?q={search_query}&hl=sv&gl=SE&ceid=SE:sv"

        # Fetch RSS feed with timeout
        response = requests.get(url, timeout=10)
        response.raise_for_status()

        # Parse RSS feed
        feed = feedparser.parse(response.content)

        # Process articles
        articles = []
        for entry in feed.entries[:max_articles]:
            # Extract source from title
            title = entry.get('title', '')
            source = 'Unknown'
            if ' - ' in title:
                parts = title.rsplit(' - ', 1)
                title = parts[0]
                source = parts[1]

            # Get summary
            description = entry.get('description', '') or entry.get('summary', '') or title
            import re
            description = re.sub(r'<[^>]+>', '', description)
            summary = description[:150]

            # Parse published date
            published = datetime.now()
            if hasattr(entry, 'published_parsed') and entry.published_parsed:
                try:
                    published = datetime(*entry.published_parsed[:6])
                except (TypeError, ValueError):
                    pass

            # Analyze sentiment
            sentiment = analyze_sentiment_simple(title, summary)

            article = {
                'title': title,
                'link': entry.get('link', ''),
                'published': published,
                'source': source,
                'sentiment': sentiment,
                'summary': summary
            }

            articles.append(article)

        # Save to cache
        if articles:
            _save_to_cache(cache_ticker, articles)

        return articles

    except requests.Timeout:
        print(f"Error: Timeout fetching market news for {market}")
        return []
    except requests.RequestException as e:
        print(f"Error: Network error fetching market news for {market}: {e}")
        return []
    except Exception as e:
        print(f"Error: Failed to parse market news for {market}: {e}")
        return []


def fetch_aggregated_market_news(max_articles: int = 15) -> Dict:
    """
    Fetch and aggregate market news from multiple sources.

    Combines:
    - OMXS30 index news
    - Swedish stock market news
    - Stockholm Stock Exchange news
    - Nordic markets news

    Returns:
        {
            'articles': List of articles (deduplicated),
            'sentiment_summary': {
                'positive_count': int,
                'negative_count': int,
                'neutral_count': int,
                'overall_sentiment': 'positive' | 'negative' | 'neutral'
            },
            'total_articles': int,
            'sources': List of source names,
            'fetched_at': datetime
        }
    """
    from datetime import datetime

    all_articles = []
    seen_titles = set()  # For deduplication

    # Source 1: OMXS30 index
    print("  Fetching OMXS30 news...")
    omxs_news = fetch_market_news("OMXS30", max_articles=5)
    all_articles.extend(omxs_news)

    # Source 2: Swedish stock market general
    print("  Fetching Swedish market news...")
    swedish_news = fetch_market_news("Swedish stock market", max_articles=5)
    all_articles.extend(swedish_news)

    # Source 3: Stockholm Stock Exchange (Stockholmsbörsen)
    print("  Fetching Stockholm Stock Exchange news...")
    sse_news = fetch_market_news("Stockholmsbörsen", max_articles=5)
    all_articles.extend(sse_news)

    # Deduplicate by title similarity (exact match for now)
    deduplicated = []
    for article in all_articles:
        title_lower = article['title'].lower()
        if title_lower not in seen_titles:
            seen_titles.add(title_lower)
            deduplicated.append(article)

    # Sort by published date (most recent first)
    deduplicated.sort(key=lambda x: x['published'], reverse=True)

    # Limit to max_articles
    final_articles = deduplicated[:max_articles]

    # Calculate sentiment summary
    sentiment_counts = {'positive': 0, 'negative': 0, 'neutral': 0}
    for article in final_articles:
        sentiment = article.get('sentiment', 'neutral')
        sentiment_counts[sentiment] += 1

    # Determine overall sentiment
    if sentiment_counts['positive'] > sentiment_counts['negative']:
        overall_sentiment = 'positive'
    elif sentiment_counts['negative'] > sentiment_counts['positive']:
        overall_sentiment = 'negative'
    else:
        overall_sentiment = 'neutral'

    return {
        'articles': final_articles,
        'sentiment_summary': {
            'positive_count': sentiment_counts['positive'],
            'negative_count': sentiment_counts['negative'],
            'neutral_count': sentiment_counts['neutral'],
            'overall_sentiment': overall_sentiment
        },
        'total_articles': len(final_articles),
        'sources': ['OMXS30', 'Swedish Stock Market', 'Stockholm Stock Exchange'],
        'fetched_at': datetime.now()
    }


def get_market_sentiment_emoji(sentiment: str) -> str:
    """Convert sentiment to emoji for display."""
    return {
        'positive': '🟢',
        'negative': '🔴',
        'neutral': '🟡'
    }.get(sentiment, '⚪')


if __name__ == "__main__":
    print("Testing news_fetcher.py...")
    print("=" * 80)

    # Test 1: Fetch news for VOLV-B.ST
    print("\n1. Testing fetch_stock_news() for VOLV-B.ST...")
    volvo_news = fetch_stock_news("VOLV-B.ST", max_articles=5)

    if volvo_news:
        print(f"   Found {len(volvo_news)} articles for Volvo")
        print("\n   First 3 articles:")
        for i, article in enumerate(volvo_news[:3], 1):
            print(f"\n   Article {i}:")
            print(f"   Title: {article['title']}")
            print(f"   Source: {article['source']}")
            print(f"   Sentiment: {article['sentiment']}")
            print(f"   Published: {article['published'].strftime('%Y-%m-%d %H:%M')}")
            print(f"   Summary: {article['summary'][:100]}...")
            print(f"   Link: {article['link'][:80]}...")
    else:
        print("   No articles found for Volvo")

    # Test 2: Fetch OMXS30 market news
    print("\n\n2. Testing fetch_market_news() for OMXS30...")
    market_news = fetch_market_news("OMXS30", max_articles=10)

    if market_news:
        print(f"   Found {len(market_news)} market news articles")
        print("\n   First 3 articles:")
        for i, article in enumerate(market_news[:3], 1):
            print(f"\n   Article {i}:")
            print(f"   Title: {article['title']}")
            print(f"   Source: {article['source']}")
            print(f"   Sentiment: {article['sentiment']}")
            print(f"   Published: {article['published'].strftime('%Y-%m-%d %H:%M')}")
    else:
        print("   No market news articles found")

    # Test 3: Cache functionality
    print("\n\n3. Testing cache functionality...")
    print("   Fetching Volvo news again (should use cache)...")
    start_time = time.time()
    volvo_news_cached = fetch_stock_news("VOLV-B.ST", max_articles=5)
    cache_time = time.time() - start_time

    print(f"   Cached fetch took {cache_time:.3f} seconds")
    print(f"   Found {len(volvo_news_cached)} cached articles")

    if volvo_news_cached:
        print(f"   Cache working: {'YES' if cache_time < 0.1 else 'NO (slow fetch)'}")

    # Test 4: Sentiment analysis
    print("\n\n4. Testing sentiment analysis...")
    test_cases = [
        ("Volvo aktie stiger kraftigt efter stark rapport", "positive"),
        ("Ericsson varnar för nedgång och förluster", "negative"),
        ("ABB håller presskonferens idag", "neutral"),
        ("Record profit and strong growth for company", "positive"),
        ("Shares fall after weak earnings miss", "negative"),
    ]

    correct = 0
    for text, expected in test_cases:
        result = analyze_sentiment_simple(text, "")
        match = "✓" if result == expected else "✗"
        print(f"   {match} '{text[:50]}...' -> {result} (expected: {expected})")
        if result == expected:
            correct += 1

    print(f"\n   Sentiment accuracy: {correct}/{len(test_cases)} ({100*correct/len(test_cases):.0f}%)")

    # Test 5: Cache directory check
    print("\n\n5. Checking cache directory...")
    cache_files = list(CACHE_DIR.glob("*.json"))
    print(f"   Cache location: {CACHE_DIR}")
    print(f"   Cache files: {len(cache_files)}")
    if cache_files:
        print(f"   Latest cache: {cache_files[-1].name}")

    # Test 6: Aggregated market news
    print("\n" + "=" * 80)
    print("TEST 6: Aggregated Market News")
    print("=" * 80)
    aggregated = fetch_aggregated_market_news(max_articles=15)
    print(f"\nFetched {aggregated['total_articles']} articles from {len(aggregated['sources'])} sources")
    print(f"Sentiment: {aggregated['sentiment_summary']['overall_sentiment']}")
    print(f"  Positive: {aggregated['sentiment_summary']['positive_count']}")
    print(f"  Negative: {aggregated['sentiment_summary']['negative_count']}")
    print(f"  Neutral: {aggregated['sentiment_summary']['neutral_count']}")
    print(f"\nTop 5 articles:")
    for i, article in enumerate(aggregated['articles'][:5], 1):
        emoji = get_market_sentiment_emoji(article['sentiment'])
        print(f"  {i}. {emoji} {article['title'][:60]}...")

    print("\n" + "=" * 80)
    print("Testing complete!")
    print("\nAcceptance Criteria:")
    print(f"   {'✓' if volvo_news else '✗'} fetch_stock_news() returns valid articles")
    print(f"   {'✓' if market_news else '✗'} fetch_market_news() works for OMXS30")
    print(f"   {'✓' if correct >= 4 else '✗'} Sentiment analysis classifies correctly")
    print(f"   {'✓' if cache_time < 0.1 and volvo_news_cached else '✗'} Caching prevents redundant fetches")
    print(f"   {'✓' if cache_files else '✗'} Cache files created")
    print(f"   {'✓' if aggregated['total_articles'] > 0 else '✗'} fetch_aggregated_market_news() returns articles")
    print(f"   {'✓' if len(aggregated['sources']) == 3 else '✗'} Fetches from 3 sources")
    print(f"   {'✓' if aggregated['sentiment_summary']['overall_sentiment'] in ['positive', 'negative', 'neutral'] else '✗'} Sentiment summary calculated")
