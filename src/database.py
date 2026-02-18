"""Database management for historical tracking of portfolio and screener results."""
import sqlite3
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from datetime import datetime
import pandas as pd


class PortfolioDB:
    """SQLite database manager for Kavastu portfolio tracking."""

    def __init__(self, db_path: str = None):
        """Initialize database connection."""
        if db_path is None:
            # Default to data directory in project root
            project_root = Path(__file__).parent.parent
            db_path = project_root / "data" / "portfolio.db"

        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

        self.conn = sqlite3.connect(str(self.db_path))
        self.conn.row_factory = sqlite3.Row  # Enable dict-like access
        self._init_tables()

    def _init_tables(self):
        """Create tables if they don't exist."""
        cursor = self.conn.cursor()

        # Table 1: Weekly portfolio snapshots
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS weekly_snapshots (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT NOT NULL UNIQUE,
                total_value REAL NOT NULL,
                cash REAL NOT NULL,
                invested REAL NOT NULL,
                ytd_return REAL,
                week_return REAL,
                month_return REAL,
                year_return REAL,
                holdings_count INTEGER,
                benchmark_ytd REAL,
                alpha_ytd REAL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Table 2: Screener results (top stocks each week)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS screener_results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                snapshot_id INTEGER NOT NULL,
                date TEXT NOT NULL,
                ticker TEXT NOT NULL,
                rank INTEGER,
                score REAL NOT NULL,
                trending_score REAL,
                trending_classification TEXT,
                price REAL,
                ma50 REAL,
                ma200 REAL,
                ma200_trend TEXT,
                rs_rating REAL,
                momentum_3m REAL,
                momentum_6m REAL,
                quality_score REAL,
                news_headline TEXT,
                FOREIGN KEY (snapshot_id) REFERENCES weekly_snapshots(id)
            )
        """)

        # Table 3: Trade history
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS trade_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT NOT NULL,
                ticker TEXT NOT NULL,
                action TEXT NOT NULL,
                shares INTEGER NOT NULL,
                price REAL NOT NULL,
                amount REAL NOT NULL,
                reason TEXT,
                kavastu_score REAL,
                trending_score REAL,
                portfolio_value_before REAL,
                portfolio_value_after REAL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Table 4: Holdings (current positions)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS holdings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                snapshot_id INTEGER NOT NULL,
                date TEXT NOT NULL,
                ticker TEXT NOT NULL,
                shares INTEGER NOT NULL,
                avg_cost REAL NOT NULL,
                current_price REAL NOT NULL,
                market_value REAL NOT NULL,
                gain_loss REAL,
                gain_loss_pct REAL,
                weight_pct REAL,
                days_held INTEGER,
                FOREIGN KEY (snapshot_id) REFERENCES weekly_snapshots(id)
            )
        """)

        # Table 5: Watchlist (user-added stocks to track)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS watchlist (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ticker TEXT NOT NULL UNIQUE,
                added_date TEXT NOT NULL,
                notes TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Table 6: Market analysis (from external sources like MarketMate)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS market_analysis (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT NOT NULL,
                source TEXT NOT NULL,
                source_type TEXT NOT NULL,
                title TEXT,
                url TEXT,
                regime TEXT,
                summary TEXT,
                tickers_mentioned TEXT,
                buy_signals TEXT,
                sell_signals TEXT,
                targets TEXT,
                raw_content TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Table 7: Portfolio config (initial capital, settings) - per profile
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS portfolio_config (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Table 8: User profiles (multi-user support)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS profiles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                avatar TEXT NOT NULL DEFAULT '🦊',
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Add profile_id to trade_history if not present
        try:
            cursor.execute("SELECT profile_id FROM trade_history LIMIT 1")
        except sqlite3.OperationalError:
            cursor.execute("ALTER TABLE trade_history ADD COLUMN profile_id INTEGER DEFAULT 1")

        # Add profile_id to portfolio_config if not present
        try:
            cursor.execute("SELECT profile_id FROM portfolio_config LIMIT 1")
        except sqlite3.OperationalError:
            cursor.execute("ALTER TABLE portfolio_config ADD COLUMN profile_id INTEGER DEFAULT 1")

        # Indexes for performance
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_screener_date ON screener_results(date)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_screener_ticker ON screener_results(ticker)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_trades_date ON trade_history(date)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_trades_ticker ON trade_history(ticker)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_holdings_date ON holdings(date)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_market_analysis_date ON market_analysis(date)")

        self.conn.commit()

    def save_weekly_snapshot(self, date: str, portfolio_metrics: Dict) -> int:
        """
        Save weekly portfolio snapshot.

        Args:
            date: Date string (YYYY-MM-DD)
            portfolio_metrics: Dict with keys:
                - total_value, cash, invested, ytd_return, week_return,
                  month_return, year_return, holdings_count, benchmark_ytd, alpha_ytd

        Returns:
            snapshot_id for linking related records
        """
        cursor = self.conn.cursor()

        cursor.execute("""
            INSERT OR REPLACE INTO weekly_snapshots
            (date, total_value, cash, invested, ytd_return, week_return,
             month_return, year_return, holdings_count, benchmark_ytd, alpha_ytd)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            date,
            portfolio_metrics.get('total_value', 0),
            portfolio_metrics.get('cash', 0),
            portfolio_metrics.get('invested', 0),
            portfolio_metrics.get('ytd_return', 0),
            portfolio_metrics.get('week_return', 0),
            portfolio_metrics.get('month_return', 0),
            portfolio_metrics.get('year_return', 0),
            portfolio_metrics.get('holdings_count', 0),
            portfolio_metrics.get('benchmark_ytd', 0),
            portfolio_metrics.get('alpha_ytd', 0)
        ))

        self.conn.commit()
        return cursor.lastrowid

    def save_screener_results(self, snapshot_id: int, date: str, stocks: pd.DataFrame):
        """
        Save screener results for this week.

        Args:
            snapshot_id: ID from weekly_snapshots table
            date: Date string (YYYY-MM-DD)
            stocks: DataFrame with columns: ticker, score, trending_score, etc.
        """
        cursor = self.conn.cursor()

        for idx, row in stocks.iterrows():
            cursor.execute("""
                INSERT INTO screener_results
                (snapshot_id, date, ticker, rank, score, trending_score,
                 trending_classification, price, ma50, ma200, ma200_trend,
                 rs_rating, momentum_3m, momentum_6m, quality_score, news_headline)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                snapshot_id,
                date,
                row.get('ticker'),
                idx + 1,  # Rank (1-based)
                row.get('score', 0),
                row.get('trending_score', 0),
                row.get('trending_classification', 'NEUTRAL'),
                row.get('price', 0),
                row.get('ma50', 0),
                row.get('ma200', 0),
                row.get('ma200_trend', 'UNKNOWN'),
                row.get('rs_rating', 0),
                row.get('momentum_3m', 0),
                row.get('momentum_6m', 0),
                row.get('quality_score', 0),
                row.get('news_headline', '')
            ))

        self.conn.commit()

    def save_trade(self, date: str, ticker: str, action: str, shares: int,
                   price: float, amount: float, reason: str = None,
                   kavastu_score: float = None, trending_score: float = None,
                   portfolio_value_before: float = None,
                   portfolio_value_after: float = None,
                   profile_id: int = 1):
        """
        Save individual trade to history.

        Args:
            date: Trade date (YYYY-MM-DD)
            ticker: Stock ticker
            action: 'BUY' or 'SELL'
            shares: Number of shares
            price: Price per share
            amount: Total transaction amount
            reason: Why this trade was made
            kavastu_score: Stock's Kavastu score at trade time
            trending_score: Stock's trending score at trade time
            portfolio_value_before: Portfolio value before trade
            portfolio_value_after: Portfolio value after trade
            profile_id: User profile ID
        """
        cursor = self.conn.cursor()

        cursor.execute("""
            INSERT INTO trade_history
            (date, ticker, action, shares, price, amount, reason,
             kavastu_score, trending_score, portfolio_value_before, portfolio_value_after, profile_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            date, ticker, action, shares, price, amount, reason,
            kavastu_score, trending_score, portfolio_value_before, portfolio_value_after, profile_id
        ))

        self.conn.commit()

    def save_holdings(self, snapshot_id: int, date: str, holdings: List[Dict]):
        """
        Save current holdings for this snapshot.

        Args:
            snapshot_id: ID from weekly_snapshots table
            date: Date string (YYYY-MM-DD)
            holdings: List of dicts with keys: ticker, shares, avg_cost, current_price, etc.
        """
        cursor = self.conn.cursor()

        for holding in holdings:
            cursor.execute("""
                INSERT INTO holdings
                (snapshot_id, date, ticker, shares, avg_cost, current_price,
                 market_value, gain_loss, gain_loss_pct, weight_pct, days_held)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                snapshot_id,
                date,
                holding.get('ticker'),
                holding.get('shares', 0),
                holding.get('avg_cost', 0),
                holding.get('current_price', 0),
                holding.get('market_value', 0),
                holding.get('gain_loss', 0),
                holding.get('gain_loss_pct', 0),
                holding.get('weight_pct', 0),
                holding.get('days_held', 0)
            ))

        self.conn.commit()

    def get_latest_snapshot(self) -> Optional[Dict]:
        """Get the most recent portfolio snapshot."""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT * FROM weekly_snapshots
            ORDER BY date DESC LIMIT 1
        """)
        row = cursor.fetchone()
        return dict(row) if row else None

    def get_portfolio_history(self, days: int = 365) -> pd.DataFrame:
        """
        Get portfolio value history.

        Args:
            days: Number of days to look back

        Returns:
            DataFrame with columns: date, total_value, ytd_return, etc.
        """
        query = """
            SELECT date, total_value, cash, invested, ytd_return,
                   week_return, month_return, year_return, benchmark_ytd, alpha_ytd
            FROM weekly_snapshots
            WHERE date >= date('now', '-{} days')
            ORDER BY date ASC
        """.format(days)

        return pd.read_sql_query(query, self.conn)

    def get_trade_history(self, ticker: str = None, days: int = 365, profile_id: int = None) -> pd.DataFrame:
        """
        Get trade history, optionally filtered by ticker and/or profile.

        Args:
            ticker: Optional ticker to filter by
            days: Number of days to look back
            profile_id: Optional profile to filter by

        Returns:
            DataFrame with trade history
        """
        conditions = [f"date >= date('now', '-{days} days')"]
        params = []

        if ticker:
            conditions.append("ticker = ?")
            params.append(ticker)
        if profile_id is not None:
            conditions.append("profile_id = ?")
            params.append(profile_id)

        where = " AND ".join(conditions)
        query = f"SELECT * FROM trade_history WHERE {where} ORDER BY date DESC"
        return pd.read_sql_query(query, self.conn, params=params)

    def get_screener_history(self, ticker: str = None, weeks: int = 12) -> pd.DataFrame:
        """
        Get screener results history.

        Args:
            ticker: Optional ticker to filter by
            weeks: Number of weeks to look back

        Returns:
            DataFrame with screener results
        """
        if ticker:
            query = """
                SELECT * FROM screener_results
                WHERE ticker = ? AND date >= date('now', '-{} days')
                ORDER BY date DESC
            """.format(weeks * 7)
            return pd.read_sql_query(query, self.conn, params=(ticker,))
        else:
            query = """
                SELECT * FROM screener_results
                WHERE date >= date('now', '-{} days')
                ORDER BY date DESC, rank ASC
            """.format(weeks * 7)
            return pd.read_sql_query(query, self.conn)

    def get_trending_performance_analysis(self) -> Dict:
        """
        Analyze performance of stocks by trending classification.

        Returns:
            Dict with average returns by trending category (HOT vs COLD vs NEUTRAL)
        """
        # This will be useful later for validation
        # Compare stocks classified as HOT vs COLD at time of screening
        # Did HOT stocks actually outperform?

        cursor = self.conn.cursor()

        # Get stocks that appeared in screener and were later traded
        query = """
            SELECT
                s.ticker,
                s.trending_classification,
                s.trending_score,
                s.score as kavastu_score,
                t.action,
                t.price as entry_price,
                t.date as entry_date
            FROM screener_results s
            JOIN trade_history t ON s.ticker = t.ticker
                AND t.date >= s.date
                AND t.date <= date(s.date, '+7 days')
            WHERE t.action = 'BUY'
            ORDER BY s.date DESC
        """

        df = pd.read_sql_query(query, self.conn)

        if len(df) == 0:
            return {'message': 'No data yet - need trades to analyze'}

        return {
            'total_trades': len(df),
            'hot_trades': len(df[df['trending_classification'] == 'HOT']),
            'cold_trades': len(df[df['trending_classification'] == 'COLD']),
            'neutral_trades': len(df[df['trending_classification'] == 'NEUTRAL']),
            'avg_trending_score': df['trending_score'].mean(),
            'avg_kavastu_score': df['kavastu_score'].mean()
        }

    def add_to_watchlist(self, ticker: str, notes: str = "") -> bool:
        """Add a stock to the watchlist. Returns True if added, False if already exists."""
        cursor = self.conn.cursor()
        try:
            cursor.execute("""
                INSERT INTO watchlist (ticker, added_date, notes)
                VALUES (?, date('now'), ?)
            """, (ticker.upper(), notes))
            self.conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False

    def remove_from_watchlist(self, ticker: str) -> bool:
        """Remove a stock from the watchlist. Returns True if removed."""
        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM watchlist WHERE ticker = ?", (ticker.upper(),))
        self.conn.commit()
        return cursor.rowcount > 0

    def update_watchlist_notes(self, ticker: str, notes: str) -> bool:
        """Update notes for a watchlist stock."""
        cursor = self.conn.cursor()
        cursor.execute("UPDATE watchlist SET notes = ? WHERE ticker = ?", (notes, ticker.upper()))
        self.conn.commit()
        return cursor.rowcount > 0

    def get_watchlist(self) -> List[Dict]:
        """Get all watchlist stocks with their latest screener data if available."""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT
                w.ticker,
                w.added_date,
                w.notes,
                s.score,
                s.trending_score,
                s.trending_classification,
                s.price,
                s.rank,
                s.ma200_trend,
                s.date as last_screened
            FROM watchlist w
            LEFT JOIN screener_results s ON w.ticker = s.ticker
                AND s.date = (
                    SELECT MAX(s2.date) FROM screener_results s2
                    WHERE s2.ticker = w.ticker
                )
            ORDER BY s.score DESC NULLS LAST, w.added_date DESC
        """)
        return [dict(r) for r in cursor.fetchall()]

    def is_in_watchlist(self, ticker: str) -> bool:
        """Check if a stock is in the watchlist."""
        cursor = self.conn.cursor()
        cursor.execute("SELECT 1 FROM watchlist WHERE ticker = ?", (ticker.upper(),))
        return cursor.fetchone() is not None

    def save_market_analysis(self, analysis: Dict) -> int:
        """Save a market analysis entry. Returns the ID."""
        cursor = self.conn.cursor()
        import json
        cursor.execute("""
            INSERT INTO market_analysis
            (date, source, source_type, title, url, regime, summary,
             tickers_mentioned, buy_signals, sell_signals, targets, raw_content)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            analysis.get('date', datetime.now().strftime('%Y-%m-%d')),
            analysis.get('source', ''),
            analysis.get('source_type', ''),
            analysis.get('title', ''),
            analysis.get('url', ''),
            analysis.get('regime', ''),
            analysis.get('summary', ''),
            json.dumps(analysis.get('tickers_mentioned', []), ensure_ascii=False),
            json.dumps(analysis.get('buy_signals', []), ensure_ascii=False),
            json.dumps(analysis.get('sell_signals', []), ensure_ascii=False),
            json.dumps(analysis.get('targets', {}), ensure_ascii=False),
            analysis.get('raw_content', '')
        ))
        self.conn.commit()
        return cursor.lastrowid

    def get_market_analyses(self, limit: int = 20, source: str = None) -> List[Dict]:
        """Get recent market analyses."""
        import json
        cursor = self.conn.cursor()
        if source:
            cursor.execute("""
                SELECT * FROM market_analysis
                WHERE source = ?
                ORDER BY date DESC, created_at DESC LIMIT ?
            """, (source, limit))
        else:
            cursor.execute("""
                SELECT * FROM market_analysis
                ORDER BY date DESC, created_at DESC LIMIT ?
            """, (limit,))
        results = []
        for row in cursor.fetchall():
            d = dict(row)
            for field in ['tickers_mentioned', 'buy_signals', 'sell_signals', 'targets']:
                if d.get(field):
                    try:
                        d[field] = json.loads(d[field])
                    except (json.JSONDecodeError, TypeError):
                        pass
            results.append(d)
        return results

    def get_latest_market_regime(self) -> Optional[Dict]:
        """Get the most recent market regime assessment."""
        import json
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT * FROM market_analysis
            WHERE regime IS NOT NULL AND regime != ''
            ORDER BY date DESC, created_at DESC LIMIT 1
        """)
        row = cursor.fetchone()
        if not row:
            return None
        d = dict(row)
        for field in ['tickers_mentioned', 'buy_signals', 'sell_signals', 'targets']:
            if d.get(field):
                try:
                    d[field] = json.loads(d[field])
                except (json.JSONDecodeError, TypeError):
                    pass
        return d

    # --- Profile Management ---

    def get_profiles(self) -> List[Dict]:
        """Get all user profiles."""
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM profiles ORDER BY id")
        return [dict(r) for r in cursor.fetchall()]

    def create_profile(self, name: str, avatar: str = '🦊') -> int:
        """Create a new profile. Returns profile id."""
        cursor = self.conn.cursor()
        cursor.execute(
            "INSERT INTO profiles (name, avatar) VALUES (?, ?)",
            (name, avatar)
        )
        self.conn.commit()
        return cursor.lastrowid

    def update_profile(self, profile_id: int, name: str = None, avatar: str = None) -> bool:
        """Update a profile's name or avatar."""
        cursor = self.conn.cursor()
        if name is not None:
            cursor.execute("UPDATE profiles SET name = ? WHERE id = ?", (name, profile_id))
        if avatar is not None:
            cursor.execute("UPDATE profiles SET avatar = ? WHERE id = ?", (avatar, profile_id))
        self.conn.commit()
        return cursor.rowcount > 0

    def delete_profile(self, profile_id: int) -> bool:
        """Delete a profile and all its trades/config."""
        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM trade_history WHERE profile_id = ?", (profile_id,))
        cursor.execute("DELETE FROM portfolio_config WHERE profile_id = ?", (profile_id,))
        cursor.execute("DELETE FROM profiles WHERE id = ?", (profile_id,))
        self.conn.commit()
        return cursor.rowcount > 0

    # --- Active Portfolio Management (per profile) ---

    def set_portfolio_config(self, key: str, value: str, profile_id: int = 1):
        """Set a portfolio config value for a profile."""
        cursor = self.conn.cursor()
        compound_key = f"{key}:{profile_id}"
        cursor.execute("""
            INSERT OR REPLACE INTO portfolio_config (key, value, profile_id, updated_at)
            VALUES (?, ?, ?, CURRENT_TIMESTAMP)
        """, (compound_key, value, profile_id))
        self.conn.commit()

    def get_portfolio_config(self, key: str, default: str = None, profile_id: int = 1) -> Optional[str]:
        """Get a portfolio config value for a profile."""
        cursor = self.conn.cursor()
        compound_key = f"{key}:{profile_id}"
        cursor.execute("SELECT value FROM portfolio_config WHERE key = ?", (compound_key,))
        row = cursor.fetchone()
        if row:
            return row['value']
        # Fallback: try old-style key (migration from single-user)
        cursor.execute("SELECT value FROM portfolio_config WHERE key = ? AND profile_id = ?", (key, profile_id))
        row = cursor.fetchone()
        return row['value'] if row else default

    def get_active_positions(self, profile_id: int = 1) -> List[Dict]:
        """
        Compute active stock positions from trade history for a profile.
        Aggregates BUY/SELL trades per ticker to get net shares and average cost.
        """
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT
                ticker,
                SUM(CASE WHEN action = 'BUY' THEN shares ELSE 0 END) as total_bought,
                SUM(CASE WHEN action = 'SELL' THEN shares ELSE 0 END) as total_sold,
                SUM(CASE WHEN action = 'BUY' THEN amount ELSE 0 END) as total_cost,
                SUM(CASE WHEN action = 'SELL' THEN amount ELSE 0 END) as total_proceeds,
                MIN(date) as first_buy_date,
                MAX(date) as last_trade_date
            FROM trade_history
            WHERE profile_id = ?
            GROUP BY ticker
            HAVING total_bought > total_sold
        """, (profile_id,))
        positions = []
        for row in cursor.fetchall():
            d = dict(row)
            net_shares = d['total_bought'] - d['total_sold']
            avg_cost = d['total_cost'] / d['total_bought'] if d['total_bought'] > 0 else 0
            positions.append({
                'ticker': d['ticker'],
                'shares': net_shares,
                'avg_cost': round(avg_cost, 2),
                'total_invested': round(avg_cost * net_shares, 2),
                'first_buy_date': d['first_buy_date'],
                'last_trade_date': d['last_trade_date'],
            })
        return positions

    def get_portfolio_cash(self, profile_id: int = 1) -> float:
        """Calculate available cash for a profile."""
        initial = float(self.get_portfolio_config('initial_capital', '0', profile_id))
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT
                COALESCE(SUM(CASE WHEN action = 'BUY' THEN amount ELSE 0 END), 0) as total_buys,
                COALESCE(SUM(CASE WHEN action = 'SELL' THEN amount ELSE 0 END), 0) as total_sells
            FROM trade_history
            WHERE profile_id = ?
        """, (profile_id,))
        row = cursor.fetchone()
        return round(initial - row['total_buys'] + row['total_sells'], 2)

    def delete_trade(self, trade_id: int) -> bool:
        """Delete a trade by ID. Returns True if deleted."""
        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM trade_history WHERE id = ?", (trade_id,))
        self.conn.commit()
        return cursor.rowcount > 0

    def cleanup_old_data(self, keep_weeks: int = 52):
        """
        Remove old screener results (keep portfolio/trade history forever).

        Args:
            keep_weeks: Number of weeks of screener data to retain (default 1 year)
        """
        cursor = self.conn.cursor()

        # Only clean up screener_results table (detailed stock data)
        # Keep weekly_snapshots, trade_history, holdings forever
        cursor.execute("""
            DELETE FROM screener_results
            WHERE date < date('now', '-{} days')
        """.format(keep_weeks * 7))

        deleted = cursor.rowcount
        self.conn.commit()

        # Vacuum to reclaim space
        cursor.execute("VACUUM")

        return deleted

    def close(self):
        """Close database connection."""
        self.conn.close()

    def __enter__(self):
        """Context manager support."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager cleanup."""
        self.close()


if __name__ == "__main__":
    # Test database creation
    print("Testing database module...")

    with PortfolioDB() as db:
        print(f"✅ Database created at: {db.db_path}")
        print(f"   File size: {db.db_path.stat().st_size / 1024:.1f} KB")

        # Test saving a snapshot
        test_metrics = {
            'total_value': 100000,
            'cash': 10000,
            'invested': 90000,
            'ytd_return': 5.2,
            'week_return': 1.1,
            'holdings_count': 8
        }

        snapshot_id = db.save_weekly_snapshot('2026-02-14', test_metrics)
        print(f"✅ Test snapshot saved (ID: {snapshot_id})")

        # Test retrieval
        latest = db.get_latest_snapshot()
        print(f"✅ Retrieved snapshot: {latest['date']}, Value: {latest['total_value']:,.0f} SEK")

        print("\n✅ Database module working!")
