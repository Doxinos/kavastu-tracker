"""
Kavastu Portfolio Tracker - REST API

FastAPI backend serving portfolio data, screener results, and trade recommendations.
Designed to be consumed by the Next.js dashboard frontend.

Run with:
    uvicorn api.main:app --reload --port 8000
"""
import sys
from pathlib import Path
from datetime import datetime
from typing import Optional, List

from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

import pandas as pd

from src.database import PortfolioDB

app = FastAPI(
    title="Kavastu Portfolio Tracker API",
    description="REST API for Swedish stock momentum trading dashboard",
    version="1.0.0"
)

# Allow CORS for frontend (localhost + local network + Vercel production)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# --- Response Models ---

class PortfolioSnapshot(BaseModel):
    date: str
    total_value: float
    cash: float
    invested: float
    ytd_return: float
    week_return: float
    month_return: Optional[float] = 0
    year_return: Optional[float] = 0
    holdings_count: int
    benchmark_ytd: Optional[float] = 0
    alpha_ytd: Optional[float] = 0

class ScreenerStock(BaseModel):
    ticker: str
    rank: int
    score: float
    trending_score: float
    trending_classification: str
    price: float
    ma50: Optional[float] = None
    ma200: Optional[float] = None
    ma200_trend: Optional[str] = None
    rs_rating: Optional[float] = None
    momentum_3m: Optional[float] = None
    momentum_6m: Optional[float] = None
    quality_score: Optional[float] = None

class TradeSignal(BaseModel):
    ticker: str
    action: str  # BUY or SELL
    score: float
    trending_score: float
    trending_classification: str
    price: float
    reason: str

class DashboardSummary(BaseModel):
    snapshot: Optional[PortfolioSnapshot] = None
    top_stocks: List[ScreenerStock]
    hot_stocks: List[ScreenerStock]
    cold_stocks: List[ScreenerStock]
    buy_signals: List[TradeSignal]
    total_screened: int
    last_updated: str

class PortfolioHistoryPoint(BaseModel):
    date: str
    value: float
    week_return: Optional[float] = 0

class TrendingAnalysis(BaseModel):
    hot: List[ScreenerStock]
    neutral: List[ScreenerStock]
    cold: List[ScreenerStock]
    distribution: dict


# --- Helper Functions ---

def get_db() -> PortfolioDB:
    """Get database instance."""
    return PortfolioDB()


def row_to_screener_stock(row) -> ScreenerStock:
    """Convert a database row to ScreenerStock model."""
    return ScreenerStock(
        ticker=row['ticker'],
        rank=row.get('rank', 0),
        score=row['score'],
        trending_score=row.get('trending_score', 0),
        trending_classification=row.get('trending_classification', 'NEUTRAL'),
        price=row.get('price', 0),
        ma50=row.get('ma50'),
        ma200=row.get('ma200'),
        ma200_trend=row.get('ma200_trend'),
        rs_rating=row.get('rs_rating'),
        momentum_3m=row.get('momentum_3m'),
        momentum_6m=row.get('momentum_6m'),
        quality_score=row.get('quality_score')
    )


# --- API Endpoints ---

@app.get("/")
def root():
    """Health check endpoint."""
    return {
        "status": "ok",
        "service": "Kavastu Portfolio Tracker API",
        "version": "1.0.0",
        "timestamp": datetime.now().isoformat()
    }


@app.get("/api/dashboard", response_model=DashboardSummary)
def get_dashboard():
    """
    Get full dashboard summary - everything the frontend needs in one call.
    Includes: latest snapshot, top stocks, hot/cold trending, buy signals.
    """
    with get_db() as db:
        # Get latest snapshot
        snapshot_row = db.get_latest_snapshot()
        snapshot = None
        if snapshot_row:
            snapshot = PortfolioSnapshot(**snapshot_row)

        # Get latest screener results
        cursor = db.conn.cursor()
        cursor.execute("""
            SELECT * FROM screener_results
            WHERE snapshot_id = (SELECT MAX(id) FROM weekly_snapshots)
            ORDER BY rank ASC
        """)
        rows = [dict(r) for r in cursor.fetchall()]

        all_stocks = [row_to_screener_stock(r) for r in rows]
        hot_stocks = [s for s in all_stocks if s.trending_classification == 'HOT']
        cold_stocks = [s for s in all_stocks if s.trending_classification == 'COLD']

        # Generate buy signals
        buy_signals = []
        for stock in all_stocks:
            if stock.score >= 100 and stock.trending_score >= 70:
                buy_signals.append(TradeSignal(
                    ticker=stock.ticker,
                    action="BUY",
                    score=stock.score,
                    trending_score=stock.trending_score,
                    trending_classification=stock.trending_classification,
                    price=stock.price,
                    reason=f"Score {stock.score:.0f}/130 • Trending {stock.trending_classification} ({stock.trending_score:.0f}/100)"
                ))

        last_updated = snapshot_row['date'] if snapshot_row else "Never"

        return DashboardSummary(
            snapshot=snapshot,
            top_stocks=all_stocks[:10],
            hot_stocks=hot_stocks[:10],
            cold_stocks=cold_stocks[:10],
            buy_signals=buy_signals,
            total_screened=len(all_stocks),
            last_updated=last_updated
        )


@app.get("/api/snapshot", response_model=Optional[PortfolioSnapshot])
def get_latest_snapshot():
    """Get the most recent portfolio snapshot."""
    with get_db() as db:
        row = db.get_latest_snapshot()
        if row:
            return PortfolioSnapshot(**row)
        return None


@app.get("/api/screener", response_model=List[ScreenerStock])
def get_screener_results(
    limit: int = Query(50, ge=1, le=200),
    min_score: float = Query(0, ge=0),
    trending: Optional[str] = Query(None, description="Filter: HOT, COLD, NEUTRAL")
):
    """
    Get latest screener results with optional filters.

    Args:
        limit: Max number of results (default 50)
        min_score: Minimum Kavastu score filter
        trending: Filter by trending classification (HOT/COLD/NEUTRAL)
    """
    with get_db() as db:
        cursor = db.conn.cursor()

        query = """
            SELECT * FROM screener_results
            WHERE snapshot_id = (SELECT MAX(id) FROM weekly_snapshots)
            AND score >= ?
        """
        params = [min_score]

        if trending:
            query += " AND trending_classification = ?"
            params.append(trending.upper())

        query += " ORDER BY rank ASC LIMIT ?"
        params.append(limit)

        cursor.execute(query, params)
        rows = [dict(r) for r in cursor.fetchall()]

        return [row_to_screener_stock(r) for r in rows]


@app.get("/api/stock/{ticker}")
def get_stock_detail(ticker: str):
    """
    Get detailed info for a specific stock, including historical screener appearances.
    """
    ticker = ticker.upper()

    with get_db() as db:
        # Get latest screener entry
        cursor = db.conn.cursor()
        cursor.execute("""
            SELECT * FROM screener_results
            WHERE ticker = ?
            ORDER BY date DESC LIMIT 1
        """, (ticker,))
        latest = cursor.fetchone()

        if not latest:
            return {"error": f"Stock {ticker} not found in screener results"}

        # Get historical scores (last 12 weeks)
        cursor.execute("""
            SELECT date, score, trending_score, trending_classification, rank, price
            FROM screener_results
            WHERE ticker = ?
            ORDER BY date DESC LIMIT 12
        """, (ticker,))
        history = [dict(r) for r in cursor.fetchall()]

        # Get trade history for this stock
        cursor.execute("""
            SELECT date, action, shares, price, amount, reason
            FROM trade_history
            WHERE ticker = ?
            ORDER BY date DESC LIMIT 20
        """, (ticker,))
        trades = [dict(r) for r in cursor.fetchall()]

        latest_dict = dict(latest)
        return {
            "ticker": ticker,
            "rank": latest_dict.get('rank', 0),
            "score": latest_dict.get('score', 0),
            "trending_score": latest_dict.get('trending_score', 0),
            "trending_classification": latest_dict.get('trending_classification', 'NEUTRAL'),
            "price": latest_dict.get('price', 0),
            "ma200_trend": latest_dict.get('ma200_trend'),
            "score_history": [{"date": h['date'], "score": h['score']} for h in history],
            "trades": [{"date": t['date'], "action": t['action'], "price": t['price'], "quantity": t.get('shares', 0)} for t in trades]
        }


@app.get("/api/history", response_model=List[PortfolioHistoryPoint])
def get_portfolio_history(days: int = Query(365, ge=7, le=1825)):
    """
    Get portfolio value history for charting.

    Args:
        days: Number of days to look back (default 365, max 5 years)
    """
    with get_db() as db:
        df = db.get_portfolio_history(days=days)

        if df.empty:
            return []

        return [
            PortfolioHistoryPoint(
                date=row['date'],
                value=row['total_value'],
                week_return=row.get('week_return', 0) or 0
            )
            for _, row in df.iterrows()
        ]


@app.get("/api/trending", response_model=TrendingAnalysis)
def get_trending_analysis():
    """Get trending stock analysis - HOT/COLD/NEUTRAL breakdown."""
    with get_db() as db:
        cursor = db.conn.cursor()
        cursor.execute("""
            SELECT * FROM screener_results
            WHERE snapshot_id = (SELECT MAX(id) FROM weekly_snapshots)
            ORDER BY trending_score DESC
        """)
        rows = [dict(r) for r in cursor.fetchall()]

        all_stocks = [row_to_screener_stock(r) for r in rows]
        hot = [s for s in all_stocks if s.trending_classification == 'HOT']
        cold = [s for s in all_stocks if s.trending_classification == 'COLD']
        neutral = [s for s in all_stocks if s.trending_classification == 'NEUTRAL']

        return TrendingAnalysis(
            hot=hot[:10],
            neutral=neutral[:10],
            cold=cold[:10],
            distribution={
                'hot': len(hot),
                'neutral': len(neutral),
                'cold': len(cold)
            }
        )


@app.get("/api/trades")
def get_trade_history(
    ticker: Optional[str] = None,
    days: int = Query(365, ge=7, le=1825),
    profile_id: Optional[int] = None
):
    """
    Get trade history, optionally filtered by ticker and/or profile.

    Args:
        ticker: Filter by stock ticker
        days: Number of days to look back
        profile_id: Filter by user profile
    """
    with get_db() as db:
        df = db.get_trade_history(ticker=ticker, days=days, profile_id=profile_id)

        if df.empty:
            return []

        return df.to_dict(orient='records')


@app.get("/api/recommendations")
def get_recommendations():
    """
    Get current trade recommendations (BUY/SELL signals).

    BUY criteria: Score >= 100 AND Trending >= 70 (HOT)
    """
    with get_db() as db:
        cursor = db.conn.cursor()
        cursor.execute("""
            SELECT * FROM screener_results
            WHERE snapshot_id = (SELECT MAX(id) FROM weekly_snapshots)
            ORDER BY score DESC
        """)
        rows = [dict(r) for r in cursor.fetchall()]

        buy_signals = []
        for row in rows:
            if row['score'] >= 100 and row.get('trending_score', 0) >= 70:
                buy_signals.append({
                    'ticker': row['ticker'],
                    'action': 'BUY',
                    'score': row['score'],
                    'trending_score': row.get('trending_score', 0),
                    'trending_classification': row.get('trending_classification', 'NEUTRAL'),
                    'price': row.get('price', 0),
                    'reason': f"Score {row['score']:.0f}/130 • Trending {row.get('trending_classification', 'N/A')} ({row.get('trending_score', 0):.0f}/100)"
                })

        return {
            'buy_signals': buy_signals,
            'sell_signals': [],  # Will implement when we have active portfolio tracking
            'generated_at': datetime.now().isoformat()
        }


# --- Stock Search Endpoint ---

class StockSearchResult(BaseModel):
    ticker: str
    name: str
    sector: str
    market_cap: str

@app.get("/api/search", response_model=List[StockSearchResult])
def search_stocks(q: str = Query(..., min_length=1, description="Search query (ticker or company name)")):
    """Search stocks by ticker or company name from the universe CSV."""
    csv_path = Path(__file__).parent.parent / "config" / "swedish_stocks.csv"
    if not csv_path.exists():
        return []

    df = pd.read_csv(csv_path)
    query = q.upper()

    # Search in both ticker and name columns
    mask = (
        df['Ticker'].str.upper().str.contains(query, na=False) |
        df['Name'].str.upper().str.contains(query, na=False)
    )
    matches = df[mask].head(15)

    return [
        StockSearchResult(
            ticker=row['Ticker'],
            name=row['Name'],
            sector=row.get('Sector', ''),
            market_cap=row.get('MarketCap', '')
        )
        for _, row in matches.iterrows()
    ]


# --- Watchlist Endpoints ---

class WatchlistItem(BaseModel):
    ticker: str
    added_date: str
    notes: Optional[str] = ""
    score: Optional[float] = None
    trending_score: Optional[float] = None
    trending_classification: Optional[str] = None
    price: Optional[float] = None
    rank: Optional[int] = None
    ma200_trend: Optional[str] = None
    last_screened: Optional[str] = None

class WatchlistAdd(BaseModel):
    ticker: str
    notes: Optional[str] = ""


@app.get("/api/watchlist", response_model=List[WatchlistItem])
def get_watchlist():
    """Get all watchlist stocks with latest screener data."""
    with get_db() as db:
        rows = db.get_watchlist()
        return [WatchlistItem(**r) for r in rows]


@app.post("/api/watchlist")
def add_to_watchlist(item: WatchlistAdd):
    """Add a stock to the watchlist."""
    ticker = item.ticker.upper()

    with get_db() as db:
        added = db.add_to_watchlist(ticker, item.notes or "")
        if added:
            return {"status": "added", "ticker": ticker}
        return {"status": "already_exists", "ticker": ticker}


@app.delete("/api/watchlist/{ticker}")
def remove_from_watchlist(ticker: str):
    """Remove a stock from the watchlist."""
    ticker = ticker.upper()

    with get_db() as db:
        removed = db.remove_from_watchlist(ticker)
        if removed:
            return {"status": "removed", "ticker": ticker}
        return {"status": "not_found", "ticker": ticker}


@app.put("/api/watchlist/{ticker}/notes")
def update_watchlist_notes(ticker: str, body: dict):
    """Update notes for a watchlist stock."""
    ticker = ticker.upper()

    with get_db() as db:
        updated = db.update_watchlist_notes(ticker, body.get("notes", ""))
        if updated:
            return {"status": "updated", "ticker": ticker}
        return {"status": "not_found", "ticker": ticker}


# --- Market Analysis Endpoints ---

class MarketAnalysisResponse(BaseModel):
    id: int
    date: str
    source: str
    source_type: str
    title: Optional[str] = ""
    url: Optional[str] = ""
    regime: Optional[str] = ""
    summary: Optional[str] = ""
    tickers_mentioned: Optional[list] = []
    buy_signals: Optional[list] = []
    sell_signals: Optional[list] = []
    targets: Optional[dict] = {}

@app.get("/api/market-analysis", response_model=List[MarketAnalysisResponse])
def get_market_analyses(limit: int = Query(20, ge=1, le=100), source: Optional[str] = None):
    """Get recent market analyses from external sources (MarketMate etc)."""
    with get_db() as db:
        analyses = db.get_market_analyses(limit=limit, source=source)
        return [MarketAnalysisResponse(**{
            'id': a['id'],
            'date': a['date'],
            'source': a['source'],
            'source_type': a['source_type'],
            'title': a.get('title', ''),
            'url': a.get('url', ''),
            'regime': a.get('regime', ''),
            'summary': a.get('summary', ''),
            'tickers_mentioned': a.get('tickers_mentioned', []),
            'buy_signals': a.get('buy_signals', []),
            'sell_signals': a.get('sell_signals', []),
            'targets': a.get('targets', {}),
        }) for a in analyses]


@app.get("/api/market-regime")
def get_market_regime():
    """Get the latest market regime assessment."""
    with get_db() as db:
        regime = db.get_latest_market_regime()
        if regime:
            return {
                'regime': regime.get('regime', 'UNKNOWN'),
                'date': regime.get('date'),
                'source': regime.get('source'),
                'summary': regime.get('summary'),
                'buy_signals': regime.get('buy_signals', []),
                'sell_signals': regime.get('sell_signals', []),
                'targets': regime.get('targets', {}),
            }
        return {'regime': 'UNKNOWN', 'date': None, 'summary': 'No analysis data yet'}


@app.post("/api/market-analysis/scrape")
def trigger_scrape():
    """Manually trigger a MarketMate scrape."""
    try:
        from src.marketmate_scraper import run_full_scrape
        results = run_full_scrape(save_to_db=True)
        return {
            'status': 'ok',
            'youtube_videos': len(results['youtube_videos']),
            'website_analyses': len(results['website_analyses']),
            'total_saved': results['total_saved'],
        }
    except Exception as e:
        return {'status': 'error', 'message': str(e)}


# --- Portfolio Management Endpoints ---

class PortfolioConfigInput(BaseModel):
    initial_capital: float
    profile_id: int = 1

class TradeInput(BaseModel):
    ticker: str
    action: str = "BUY"  # BUY or SELL
    shares: int
    price: float
    date: Optional[str] = None  # YYYY-MM-DD, defaults to today
    reason: Optional[str] = None
    profile_id: int = 1

class ProfileInput(BaseModel):
    name: str
    avatar: str = '🦊'


# --- Profile Endpoints ---

@app.get("/api/profiles")
def list_profiles():
    """List all user profiles."""
    with get_db() as db:
        profiles = db.get_profiles()
        # Seed defaults if no profiles exist
        if not profiles:
            db.create_profile("Peter", "🐺")
            db.create_profile("Thilde", "🦒")
            db.create_profile("Lukas", "🦁")
            profiles = db.get_profiles()
        return profiles

@app.post("/api/profiles")
def create_profile(profile: ProfileInput):
    """Create a new user profile."""
    with get_db() as db:
        profile_id = db.create_profile(profile.name, profile.avatar)
        return {'status': 'ok', 'id': profile_id, 'name': profile.name, 'avatar': profile.avatar}

@app.put("/api/profiles/{profile_id}")
def update_profile(profile_id: int, profile: ProfileInput):
    """Update a profile's name or avatar."""
    with get_db() as db:
        db.update_profile(profile_id, profile.name, profile.avatar)
        return {'status': 'ok', 'id': profile_id}

@app.delete("/api/profiles/{profile_id}")
def delete_profile(profile_id: int):
    """Delete a profile and all its data."""
    with get_db() as db:
        deleted = db.delete_profile(profile_id)
        return {'status': 'deleted' if deleted else 'not_found'}


# --- Portfolio Management Endpoints ---

@app.get("/api/portfolio")
def get_portfolio(profile_id: int = 1):
    """
    Get active portfolio: positions with live-ish prices, cash, and totals.
    Computes positions from trade history and fetches latest screener prices.
    """
    with get_db() as db:
        config_capital = db.get_portfolio_config('initial_capital', profile_id=profile_id)
        if not config_capital:
            return {
                'configured': False,
                'message': 'Set initial capital first via POST /api/portfolio/config',
            }

        initial_capital = float(config_capital)
        positions = db.get_active_positions(profile_id=profile_id)
        cash = db.get_portfolio_cash(profile_id=profile_id)

        # Enrich positions with latest screener prices if available
        cursor = db.conn.cursor()
        enriched = []
        total_market_value = 0

        for pos in positions:
            ticker = pos['ticker']

            # Get latest price from screener
            cursor.execute("""
                SELECT price, score, trending_score, trending_classification
                FROM screener_results
                WHERE ticker = ?
                ORDER BY date DESC LIMIT 1
            """, (ticker,))
            screener = cursor.fetchone()

            current_price = dict(screener)['price'] if screener else pos['avg_cost']
            market_value = pos['shares'] * current_price
            gain_loss = market_value - pos['total_invested']
            gain_loss_pct = (gain_loss / pos['total_invested'] * 100) if pos['total_invested'] > 0 else 0

            total_market_value += market_value

            entry = {
                'ticker': ticker,
                'shares': pos['shares'],
                'avg_cost': pos['avg_cost'],
                'current_price': round(current_price, 2),
                'market_value': round(market_value, 2),
                'total_invested': pos['total_invested'],
                'gain_loss': round(gain_loss, 2),
                'gain_loss_pct': round(gain_loss_pct, 2),
                'first_buy_date': pos['first_buy_date'],
            }

            if screener:
                s = dict(screener)
                entry['kavastu_score'] = s.get('score')
                entry['trending_score'] = s.get('trending_score')
                entry['trending_classification'] = s.get('trending_classification')

            enriched.append(entry)

        # Calculate weights based on total portfolio value
        total_value = total_market_value + cash
        for entry in enriched:
            entry['weight_pct'] = round((entry['market_value'] / total_value * 100) if total_value > 0 else 0, 2)

        # Sort by market value descending
        enriched.sort(key=lambda x: x['market_value'], reverse=True)

        total_gain = total_market_value - (initial_capital - cash)
        total_gain_pct = (total_gain / initial_capital * 100) if initial_capital > 0 else 0

        return {
            'configured': True,
            'initial_capital': initial_capital,
            'cash': cash,
            'cash_pct': round((cash / total_value * 100) if total_value > 0 else 100, 1),
            'invested': round(total_market_value, 2),
            'total_value': round(total_value, 2),
            'total_gain': round(total_gain, 2),
            'total_gain_pct': round(total_gain_pct, 2),
            'holdings_count': len(enriched),
            'positions': enriched,
        }


@app.post("/api/portfolio/config")
def set_portfolio_config(config: PortfolioConfigInput):
    """Set portfolio initial capital."""
    with get_db() as db:
        db.set_portfolio_config('initial_capital', str(config.initial_capital), profile_id=config.profile_id)
        return {'status': 'ok', 'initial_capital': config.initial_capital, 'profile_id': config.profile_id}


@app.post("/api/portfolio/trade")
def add_trade(trade: TradeInput):
    """Record a BUY or SELL trade."""
    ticker = trade.ticker.upper()
    trade_date = trade.date or datetime.now().strftime('%Y-%m-%d')
    amount = trade.shares * trade.price

    with get_db() as db:
        # Validate: can't sell more than we own
        if trade.action.upper() == 'SELL':
            positions = db.get_active_positions(profile_id=trade.profile_id)
            held = next((p for p in positions if p['ticker'] == ticker), None)
            if not held or held['shares'] < trade.shares:
                current = held['shares'] if held else 0
                return {'status': 'error', 'message': f'Cannot sell {trade.shares} shares of {ticker}, only hold {current}'}

        # Validate: enough cash for buy
        if trade.action.upper() == 'BUY':
            cash = db.get_portfolio_cash(profile_id=trade.profile_id)
            if amount > cash:
                return {'status': 'error', 'message': f'Not enough cash. Need {amount:,.0f} SEK but only {cash:,.0f} available'}

        db.save_trade(
            date=trade_date,
            ticker=ticker,
            action=trade.action.upper(),
            shares=trade.shares,
            price=trade.price,
            amount=amount,
            reason=trade.reason,
            profile_id=trade.profile_id,
        )

        return {
            'status': 'ok',
            'trade': {
                'ticker': ticker,
                'action': trade.action.upper(),
                'shares': trade.shares,
                'price': trade.price,
                'amount': amount,
                'date': trade_date,
            }
        }


@app.delete("/api/portfolio/trade/{trade_id}")
def delete_trade(trade_id: int):
    """Delete a trade record (for corrections)."""
    with get_db() as db:
        deleted = db.delete_trade(trade_id)
        if deleted:
            return {'status': 'deleted', 'trade_id': trade_id}
        return {'status': 'not_found', 'trade_id': trade_id}


@app.get("/api/market-synthesis")
def get_market_synthesis():
    """Cross-reference MarketMate analysis with our technical model."""
    try:
        from src.market_synthesis import generate_market_synthesis
        return generate_market_synthesis()
    except Exception as e:
        return {'available': False, 'reason': str(e)}


# --- Admin: Database sync endpoint ---

from fastapi import UploadFile, File
import shutil

@app.post("/api/admin/upload-db")
async def upload_database(file: UploadFile = File(...), secret: str = ""):
    """Upload a SQLite database file to replace the current one."""
    if secret != "kavastu2026sync":
        return {"status": "error", "message": "Invalid secret"}
    try:
        db_path = Path(__file__).parent.parent / "data" / "portfolio.db"
        db_path.parent.mkdir(parents=True, exist_ok=True)
        with open(db_path, "wb") as f:
            shutil.copyfileobj(file.file, f)
        size = db_path.stat().st_size
        return {"status": "ok", "size_bytes": size}
    except Exception as e:
        return {"status": "error", "message": str(e)}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("api.main:app", host="0.0.0.0", port=8000, reload=True)
