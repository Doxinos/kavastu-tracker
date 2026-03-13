"""
MarketMate Scraper - Fetch and analyze content from MarketMate.

Sources:
1. YouTube (@ten_bagger) - Weekly market update videos, transcribed via auto-captions
2. Website (marketmate.se) - Daily stock analyses with entry/stoploss/target

Outputs structured analysis data for the market_analysis database table.
"""
import re
import json
from datetime import datetime
from typing import List, Dict, Optional
from pathlib import Path

# YouTube transcript
try:
    from youtube_transcript_api import YouTubeTranscriptApi
    HAS_TRANSCRIPT_API = True
except ImportError:
    HAS_TRANSCRIPT_API = False

# Web scraping
try:
    import requests
    from bs4 import BeautifulSoup
    HAS_WEB = True
except ImportError:
    HAS_WEB = False


YOUTUBE_CHANNEL = "ten_bagger"
YOUTUBE_CHANNEL_ID = "UC-8y8mhki-e-kJEMPPpsiew"  # @ten_bagger / Marketmate
WEBSITE_BASE = "https://www.marketmate.se"
ANALYSIS_URLS = [
    f"{WEBSITE_BASE}/category/dagens-analys/",
    f"{WEBSITE_BASE}/borsanalyser/",
]

# Known Swedish ticker mappings
TICKER_MAP = {
    'SANDVIK': 'SAND.ST', 'SAND': 'SAND.ST',
    'VOLVO': 'VOLV-B.ST', 'ABB': 'ABB.ST',
    'HEXAGON': 'HEXA-B.ST', 'SAAB': 'SAAB-B.ST',
    'ATLAS': 'ATCO-A.ST', 'ATLAS COPCO': 'ATCO-A.ST',
    'ERICSSON': 'ERIC-B.ST', 'SEB': 'SEB-A.ST',
    'HANDELSBANKEN': 'SHB-A.ST', 'SWEDBANK': 'SWED-A.ST',
    'EVOLUTION': 'EVO.ST', 'NIBE': 'NIBE-B.ST',
    'INVESTOR': 'INVE-B.ST', 'EPIROC': 'EPI-A.ST',
    'MICROSOFT': 'MSFT', 'ORACLE': 'ORCL',
    'NASDAQ': 'QQQ', 'NASDAQ 100': 'QQQ',
    'DANSKE BANK': 'DANSKE.CO', 'DANSKE': 'DANSKE.CO',
    'ISS': 'ISS.CO', 'MAERSK': 'MAERSK-B.CO',
}

# Index keywords
INDEX_KEYWORDS = [
    'OMX', 'OMXS30', 'OMXSPI', 'S&P', 'S&P 500', 'NASDAQ', 'NASDAQ 100',
    'DOW JONES', 'RUSSELL', 'RUSSELL 2000', 'NIKKEI', 'KOSPI', 'STOXX',
    'STOXX 50', 'DAX',
]


def fetch_youtube_transcript(video_id: str) -> Optional[str]:
    """Fetch Swedish auto-generated transcript from YouTube video."""
    if not HAS_TRANSCRIPT_API:
        print("youtube-transcript-api not installed")
        return None

    try:
        ytt = YouTubeTranscriptApi()
        transcript = ytt.fetch(video_id, languages=['sv'])
        return ' '.join([snippet.text for snippet in transcript])
    except Exception as e:
        print(f"Failed to fetch transcript for {video_id}: {e}")
        return None


def _scrape_videos_from_page(channel_handle: str, max_results: int = 5) -> List[Dict]:
    """Scrape video IDs and titles directly from the YouTube channel page."""
    try:
        resp = requests.get(
            f"https://www.youtube.com/@{channel_handle}/videos",
            headers={"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"},
            timeout=15,
        )
        if resp.status_code != 200:
            return []

        video_ids = list(dict.fromkeys(re.findall(r'"videoId":"([a-zA-Z0-9_-]{11})"', resp.text)))
        titles = re.findall(r'"title":\{"runs":\[\{"text":"([^"]+)"\}', resp.text)

        videos = []
        for i, vid in enumerate(video_ids[:max_results]):
            title = titles[i] if i < len(titles) else f"Video {vid}"
            videos.append({
                'video_id': vid,
                'title': title,
                'date': '',
                'url': f"https://youtu.be/{vid}",
                'description': '',
            })
        return videos
    except Exception as e:
        print(f"Page scrape failed: {e}")
        return []


def fetch_channel_videos(channel_handle: str = "ten_bagger", max_results: int = 5) -> List[Dict]:
    """
    Get recent video IDs from a YouTube channel.
    Tries RSS feed first, falls back to direct page scrape.
    """
    if not HAS_WEB:
        return []

    # Try RSS feed first
    rss_url = f"https://www.youtube.com/feeds/videos.xml?channel_id={YOUTUBE_CHANNEL_ID}"
    try:
        rss_resp = requests.get(rss_url, timeout=10)

        if rss_resp.status_code == 200 and '<entry>' in rss_resp.text:
            soup = BeautifulSoup(rss_resp.text, 'xml')
            videos = []
            for entry in soup.find_all('entry')[:max_results]:
                video_id_tag = entry.find('yt:videoId')
                title_tag = entry.find('title')
                published_tag = entry.find('published')
                desc_tag = entry.find('media:description')

                if not video_id_tag or not title_tag:
                    continue

                videos.append({
                    'video_id': video_id_tag.text,
                    'title': title_tag.text,
                    'date': published_tag.text[:10] if published_tag else '',
                    'url': f"https://youtu.be/{video_id_tag.text}",
                    'description': desc_tag.text if desc_tag else '',
                })

            if videos:
                return videos
    except Exception:
        pass

    # Fallback: scrape channel page directly
    print("RSS feed unavailable, scraping channel page...")
    return _scrape_videos_from_page(channel_handle, max_results)


def parse_transcript_analysis(transcript: str, video_title: str = "", video_date: str = "") -> Dict:
    """
    Parse a MarketMate video transcript and extract structured analysis.

    Returns dict with: regime, summary, tickers, buy_signals, sell_signals, targets
    """
    text_lower = transcript.lower()

    # Detect market regime
    regime = "NEUTRAL"
    regime_signals = []

    if any(w in text_lower for w in ['stark bull', 'starka uppgång', 'rally', 'tar fart']):
        regime_signals.append('BULL')
    # Only flag BEAR if it's not negated (e.g. "inte bear", "inte falla samman")
    bear_words = ['ragnarrök', 'sammanbrott', 'krasch', 'falla samman']
    for w in bear_words:
        if w in text_lower:
            # Check if negated within 30 chars before
            idx = text_lower.index(w)
            context = text_lower[max(0, idx-30):idx]
            if 'inte' not in context and 'inga' not in context:
                regime_signals.append('BEAR')
    if any(w in text_lower for w in ['rekyl', 'andhämtning', 'konsolidering']):
        regime_signals.append('PULLBACK_EXPECTED')
    if any(w in text_lower for w in ['sportlov', 'optionslösen']):
        regime_signals.append('SEASONAL_RISK')
    if any(w in text_lower for w in ['inga negativa divergenser i vecko', 'inga varningssignaler']):
        regime_signals.append('WEEKLY_BULLISH')
    if 'negativa divergenser' in text_lower and 'daily' in text_lower:
        regime_signals.append('DAILY_BEARISH_DIV')

    # Determine overall regime - weekly signals trump daily
    if 'WEEKLY_BULLISH' in regime_signals:
        if 'PULLBACK_EXPECTED' in regime_signals or 'DAILY_BEARISH_DIV' in regime_signals:
            regime = "BULL_WITH_SHORT_TERM_PULLBACK"
        else:
            regime = "BULL"
    elif 'BULL' in regime_signals and 'BEAR' not in regime_signals:
        regime = "BULL_WITH_SHORT_TERM_PULLBACK" if 'PULLBACK_EXPECTED' in regime_signals else "BULL"
    elif 'BEAR' in regime_signals:
        regime = "BEAR"

    # Extract tickers mentioned
    tickers_found = set()
    for name, ticker in TICKER_MAP.items():
        if name.lower() in text_lower:
            tickers_found.add(ticker)

    # Extract index mentions
    indices_found = []
    for idx in INDEX_KEYWORDS:
        if idx.lower() in text_lower:
            indices_found.append(idx)

    # Extract price targets (look for patterns like "target 7600", "upp mot 680")
    targets = {}
    target_patterns = [
        r'target[:\s]+(\d[\d\s,.]+)',
        r'upp mot[:\s]+(\d[\d\s,.]+)',
        r'ner mot[:\s]+(\d[\d\s,.]+)',
        r'mål[:\s]+(\d[\d\s,.]+)',
    ]
    for pattern in target_patterns:
        matches = re.findall(pattern, text_lower)
        for m in matches:
            clean = m.strip().replace(' ', '').replace(',', '.')
            try:
                val = float(clean)
                targets[f"level_{len(targets)}"] = val
            except ValueError:
                pass

    # Extract specific S&P 500 target
    sp_match = re.search(r's&p.*?(\d{4})', text_lower)
    if sp_match:
        targets['sp500_target'] = int(sp_match.group(1))

    # Look for buy/sell signals
    buy_signals = []
    sell_signals = []

    # "köper X" pattern
    buy_patterns = re.findall(r'köper\s+(\w+)', text_lower)
    for match in buy_patterns:
        for name, ticker in TICKER_MAP.items():
            if name.lower() == match or name.lower().startswith(match):
                buy_signals.append({'ticker': ticker, 'source': 'MarketMate YouTube'})
                break

    # "short X" or "säljer X" pattern
    sell_patterns = re.findall(r'(?:short|säljer|shortar)\s+(\w+)', text_lower)
    for match in sell_patterns:
        for name, ticker in TICKER_MAP.items():
            if name.lower() == match or name.lower().startswith(match):
                sell_signals.append({'ticker': ticker, 'source': 'MarketMate YouTube'})
                break
        if match == 'omx' or match == 'omxs30':
            sell_signals.append({'ticker': 'OMXS30', 'source': 'MarketMate YouTube', 'type': 'short'})

    # Build summary (key sentences)
    summary_parts = []

    # Regime
    if 'BULL' in regime:
        summary_parts.append("Bullish grundtrend (inga neg divergenser i weekly)")
    if 'PULLBACK_EXPECTED' in regime_signals:
        summary_parts.append("Rekyl 3-5% väntad på kort sikt")
    if 'SEASONAL_RISK' in regime_signals:
        summary_parts.append("Säsongsrisk: optionslösen + sportlov")

    # Specific targets
    if 'sp500_target' in targets:
        summary_parts.append(f"S&P 500 target: {targets['sp500_target']}")

    # Tickers
    if buy_signals:
        tickers_str = ', '.join([s['ticker'] for s in buy_signals])
        summary_parts.append(f"Köpsignaler: {tickers_str}")
    if sell_signals:
        tickers_str = ', '.join([s['ticker'] for s in sell_signals])
        summary_parts.append(f"Sälj/short: {tickers_str}")

    return {
        'date': video_date or datetime.now().strftime('%Y-%m-%d'),
        'source': 'MarketMate',
        'source_type': 'youtube',
        'title': video_title,
        'regime': regime,
        'regime_signals': regime_signals,
        'summary': ' | '.join(summary_parts),
        'tickers_mentioned': sorted(list(tickers_found)),
        'indices_mentioned': sorted(list(set(indices_found))),
        'buy_signals': buy_signals,
        'sell_signals': sell_signals,
        'targets': targets,
    }


def fetch_website_analyses(max_articles: int = 10) -> List[Dict]:
    """
    Scrape recent stock analyses from marketmate.se.

    Returns list of analysis dicts with: ticker, action, entry, stoploss, target, etc.
    """
    if not HAS_WEB:
        print("requests/beautifulsoup4 not installed")
        return []

    analyses = []
    seen_urls = set()

    for listing_url in ANALYSIS_URLS:
        try:
            resp = requests.get(
                listing_url,
                headers={"User-Agent": "Mozilla/5.0"},
                timeout=10
            )
            soup = BeautifulSoup(resp.text, 'html.parser')

            # Find article links
            for link in soup.find_all('a', href=True):
                href = link['href']
                if not href.startswith(WEBSITE_BASE):
                    continue
                if href in seen_urls:
                    continue
                # Filter for analysis/trading articles
                title_text = link.get_text(strip=True).lower()
                if any(kw in title_text for kw in [
                    'köper', 'säljer', 'short', 'lång', 'bull', 'bear', 'analys',
                    'rally', 'rekyl', 'botten', 'topp', 'warrant', 'börs',
                    'aktie', 'index', 'dax', 'omx', 's&p',
                ]):
                    seen_urls.add(href)
                    if len(analyses) < max_articles:
                        article = _fetch_article(href)
                        if article:
                            analyses.append(article)

        except Exception as e:
            print(f"Failed to fetch {listing_url}: {e}")

    return analyses


def _fetch_article(url: str) -> Optional[Dict]:
    """Fetch and parse a single MarketMate article."""
    try:
        resp = requests.get(
            url,
            headers={"User-Agent": "Mozilla/5.0"},
            timeout=10
        )
        soup = BeautifulSoup(resp.text, 'html.parser')

        # Get title
        title_tag = soup.find('h1')
        title = title_tag.get_text(strip=True) if title_tag else ""

        # Get article body text
        article_body = soup.find('article') or soup.find('div', class_='entry-content') or soup.find('main')
        if not article_body:
            return None
        body_text = article_body.get_text(separator=' ', strip=True)

        # Get date
        time_tag = soup.find('time')
        date_str = time_tag.get('datetime', '')[:10] if time_tag else datetime.now().strftime('%Y-%m-%d')

        # Parse the analysis
        text_lower = body_text.lower()

        # Detect action
        action = "NEUTRAL"
        if 'köper' in title.lower():
            action = "BUY"
        elif 'säljer' in title.lower() or 'short' in title.lower():
            action = "SELL"

        # Extract ticker from title
        ticker = None
        title_upper = title.upper().replace('KÖPER ', '').replace('SÄLJER ', '').replace('SHORT ', '').replace('!', '').strip()
        for name, t in TICKER_MAP.items():
            if name in title_upper:
                ticker = t
                break

        # Extract stoploss
        stoploss = None
        sl_match = re.search(r'stop[- ]?loss[:\s]+(\d[\d\s,.]+)', text_lower)
        if sl_match:
            try:
                stoploss = float(sl_match.group(1).strip().replace(' ', '').replace(',', '.'))
            except ValueError:
                pass

        # Extract target
        target = None
        tgt_match = re.search(r'(?:target|mål|riktkurs)[:\s]+(\d[\d\s,.]+)', text_lower)
        if tgt_match:
            try:
                target = float(tgt_match.group(1).strip().replace(' ', '').replace(',', '.'))
            except ValueError:
                pass

        # Extract entry price
        entry = None
        entry_match = re.search(r'(?:köpkurs|entry|kurs)[:\s]+(\d[\d\s,.]+)', text_lower)
        if entry_match:
            try:
                entry = float(entry_match.group(1).strip().replace(' ', '').replace(',', '.'))
            except ValueError:
                pass

        buy_signals = []
        sell_signals = []
        if action == "BUY" and ticker:
            buy_signals.append({
                'ticker': ticker,
                'entry': entry,
                'stoploss': stoploss,
                'target': target,
                'source': 'MarketMate Web'
            })
        elif action == "SELL" and ticker:
            sell_signals.append({
                'ticker': ticker,
                'entry': entry,
                'stoploss': stoploss,
                'target': target,
                'source': 'MarketMate Web'
            })

        tickers_mentioned = [ticker] if ticker else []

        # Build summary
        summary_parts = []
        if action == "BUY" and ticker:
            summary_parts.append(f"KÖP {ticker}")
        elif action == "SELL" and ticker:
            summary_parts.append(f"SÄLJ/SHORT {ticker}")
        if stoploss:
            summary_parts.append(f"SL: {stoploss}")
        if target:
            summary_parts.append(f"Target: {target}")

        return {
            'date': date_str,
            'source': 'MarketMate',
            'source_type': 'website',
            'title': title,
            'url': url,
            'regime': '',
            'summary': ' | '.join(summary_parts) if summary_parts else title,
            'tickers_mentioned': tickers_mentioned,
            'buy_signals': buy_signals,
            'sell_signals': sell_signals,
            'targets': {'stoploss': stoploss, 'target': target, 'entry': entry},
            'raw_content': body_text[:2000],
        }

    except Exception as e:
        print(f"Failed to fetch article {url}: {e}")
        return None


def run_full_scrape(save_to_db: bool = True) -> Dict:
    """
    Run complete MarketMate scrape: YouTube + Website.

    Returns summary of what was found and saved.
    """
    print("=" * 60)
    print("MARKETMATE SCRAPER")
    print("=" * 60)

    results = {
        'youtube_videos': [],
        'website_analyses': [],
        'total_saved': 0,
    }

    # 1. YouTube videos
    print("\n--- YouTube (@ten_bagger) ---")
    videos = fetch_channel_videos(YOUTUBE_CHANNEL, max_results=3)
    print(f"Found {len(videos)} recent videos")

    for video in videos:
        print(f"  Processing: {video['title']} ({video['date']})")
        transcript = fetch_youtube_transcript(video['video_id'])

        # Fallback to RSS description if transcript not available
        text_to_parse = transcript
        source_note = "transcript"
        if not text_to_parse and video.get('description'):
            text_to_parse = video['description']
            source_note = "RSS description"
            print(f"    Using RSS description as fallback")

        if text_to_parse:
            analysis = None

            # Try AI-powered full analysis first (regime + summary + signals in one call)
            if transcript:
                from .ai_summary import generate_full_analysis
                print(f"    Generating AI full analysis...")
                ai_result = generate_full_analysis(transcript, video['title'])
                if ai_result:
                    analysis = {
                        'date': video['date'] or datetime.now().strftime('%Y-%m-%d'),
                        'source': 'MarketMate',
                        'source_type': 'youtube',
                        'title': video['title'],
                        'url': video['url'],
                        'raw_content': text_to_parse[:5000],
                        'regime': ai_result['regime'],
                        'summary': ai_result['summary'],
                        'executive_summary': ai_result['executive_summary'],
                        'tickers_mentioned': ai_result['tickers_mentioned'],
                        'buy_signals': ai_result['buy_signals'],
                        'sell_signals': ai_result['sell_signals'],
                        'targets': ai_result['targets'],
                    }
                    source_note = "AI analysis"
                    print(f"    AI analysis complete ({len(ai_result.get('executive_summary', ''))} chars)")

            # Fallback to keyword parsing if AI analysis failed
            if not analysis:
                print(f"    Falling back to keyword analysis...")
                analysis = parse_transcript_analysis(text_to_parse, video['title'], video['date'])
                analysis['url'] = video['url']
                analysis['raw_content'] = text_to_parse[:5000]

            results['youtube_videos'].append(analysis)
            print(f"    Regime: {analysis['regime']} (from {source_note})")
            print(f"    Tickers: {', '.join(analysis['tickers_mentioned'])}")
            print(f"    Summary: {analysis['summary'][:100]}")
        else:
            print(f"    No transcript or description available")

    # 2. Website analyses
    print("\n--- Website (marketmate.se) ---")
    articles = fetch_website_analyses(max_articles=10)
    print(f"Found {len(articles)} analyses")

    for article in articles:
        print(f"  {article['title']} ({article['date']})")
        if article['buy_signals']:
            for sig in article['buy_signals']:
                print(f"    BUY {sig['ticker']} | SL: {sig.get('stoploss')} | Target: {sig.get('target')}")
        if article['sell_signals']:
            for sig in article['sell_signals']:
                print(f"    SELL {sig['ticker']}")
        results['website_analyses'].append(article)

    # 3. Save to database
    if save_to_db:
        from .database import PortfolioDB
        print("\n--- Saving to Database ---")
        with PortfolioDB() as db:
            for analysis in results['youtube_videos'] + results['website_analyses']:
                # Check if we already have this URL
                cursor = db._cursor()
                if analysis.get('url'):
                    cursor.execute(db._q("SELECT id, executive_summary FROM market_analysis WHERE url = ?"), (analysis['url'],))
                    existing = cursor.fetchone()
                    if existing:
                        # Update AI-generated fields if we have new data and existing is empty
                        if analysis.get('executive_summary') and not existing['executive_summary']:
                            import json as _json
                            cursor.execute(
                                db._q("""UPDATE market_analysis
                                   SET executive_summary = ?, regime = ?, summary = ?,
                                       tickers_mentioned = ?, buy_signals = ?, sell_signals = ?,
                                       targets = ?
                                   WHERE id = ?"""),
                                (
                                    analysis['executive_summary'],
                                    analysis.get('regime', ''),
                                    analysis.get('summary', ''),
                                    _json.dumps(analysis.get('tickers_mentioned', []), ensure_ascii=False),
                                    _json.dumps(analysis.get('buy_signals', []), ensure_ascii=False),
                                    _json.dumps(analysis.get('sell_signals', []), ensure_ascii=False),
                                    _json.dumps(analysis.get('targets', {}), ensure_ascii=False),
                                    existing['id'],
                                )
                            )
                            db.conn.commit()
                            results['total_saved'] += 1
                            print(f"  Updated: {analysis['title']} (ID: {existing['id']})")
                        else:
                            print(f"  Skip (exists): {analysis['title']}")
                        continue

                aid = db.save_market_analysis(analysis)
                results['total_saved'] += 1
                print(f"  Saved: {analysis['title']} (ID: {aid})")

    print(f"\nTotal saved: {results['total_saved']}")
    print("=" * 60)

    return results


if __name__ == "__main__":
    results = run_full_scrape(save_to_db=True)
    print(f"\nYouTube videos processed: {len(results['youtube_videos'])}")
    print(f"Website analyses found: {len(results['website_analyses'])}")
    print(f"Total saved to DB: {results['total_saved']}")
