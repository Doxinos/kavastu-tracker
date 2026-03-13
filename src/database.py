"""Database management for historical tracking of portfolio and screener results.

Supports both SQLite (local dev) and PostgreSQL (production via Supabase).
Set DATABASE_URL environment variable to use PostgreSQL; otherwise falls back to SQLite.
"""
import json
import os
import sqlite3
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from datetime import datetime

try:
    import psycopg2
    import psycopg2.extras
    HAS_PSYCOPG2 = True
except ImportError:
    HAS_PSYCOPG2 = False

import pandas as pd


class PortfolioDB:
    """Database manager for Kavastu portfolio tracking. Supports SQLite and PostgreSQL."""

    def __init__(self, db_path: str = None):
        """Initialize database connection.

        If DATABASE_URL env var is set and psycopg2 is available, use PostgreSQL.
        Otherwise fall back to SQLite.
        """
        database_url = os.environ.get('DATABASE_URL') or os.environ.get('SUPABASE_DB_URL')

        if database_url and HAS_PSYCOPG2:
            self.db_type = 'postgres'
            self.conn = psycopg2.connect(database_url)
            self.conn.autocommit = False
            self.db_path = None
        else:
            self.db_type = 'sqlite'
            if db_path is None:
                project_root = Path(__file__).parent.parent
                db_path = project_root / "data" / "portfolio.db"
            self.db_path = Path(db_path)
            self.db_path.parent.mkdir(parents=True, exist_ok=True)
            self.conn = sqlite3.connect(str(self.db_path))
            self.conn.row_factory = sqlite3.Row

        self._init_tables()

    def _q(self, sql: str) -> str:
        """Adapt SQL for the current database backend."""
        if self.db_type == 'postgres':
            # Replace ? placeholders with %s for psycopg2
            sql = sql.replace('?', '%s')
            # Replace AUTOINCREMENT with PostgreSQL equivalent
            sql = sql.replace('INTEGER PRIMARY KEY AUTOINCREMENT', 'SERIAL PRIMARY KEY')
            # Replace INSERT OR REPLACE with PostgreSQL equivalent handled per-query
            # Replace date('now') and date('now', '...') with PostgreSQL equivalents
            sql = sql.replace("date('now')", "CURRENT_DATE")
            # Handle date('now', '-N days') patterns
            import re
            sql = re.sub(
                r"date\('now',\s*'-(\d+)\s+days'\)",
                r"(CURRENT_DATE - INTERVAL '\1 days')",
                sql
            )
            # Handle date(column, '+N days') patterns
            sql = re.sub(
                r"date\((\w+),\s*'\+(\d+)\s+days'\)",
                r"(\1::date + INTERVAL '\2 days')",
                sql
            )
            # VACUUM is not needed in PostgreSQL
            if sql.strip().upper() == 'VACUUM':
                return 'SELECT 1'
        return sql

    def _cursor(self):
        """Get a cursor appropriate for the database type."""
        if self.db_type == 'postgres':
            return self.conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        return self.conn.cursor()

    def _fetchone_dict(self, cursor, row) -> Optional[Dict]:
        """Convert a row to a dict regardless of backend."""
        if row is None:
            return None
        if self.db_type == 'postgres':
            return dict(row)
        return dict(row)

    def _lastrowid(self, cursor) -> int:
        """Get the last inserted row ID."""
        if self.db_type == 'postgres':
            try:
                row = cursor.fetchone()
                if row:
                    if isinstance(row, dict):
                        return list(row.values())[0]
                    return row[0]
            except Exception:
                pass
            return 0
        return cursor.lastrowid

    def _init_tables(self):
        """Create tables if they don't exist."""
        cursor = self.conn.cursor()

        if self.db_type == 'postgres':
            self._init_tables_postgres(cursor)
        else:
            self._init_tables_sqlite(cursor)

        self.conn.commit()

    def _init_tables_sqlite(self, cursor):
        """Create SQLite tables."""
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

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS watchlist (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ticker TEXT NOT NULL UNIQUE,
                added_date TEXT NOT NULL,
                notes TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)

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
                executive_summary TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS portfolio_config (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL,
                profile_id INTEGER DEFAULT 1,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS profiles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                avatar TEXT NOT NULL DEFAULT '🦊',
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Migration: add columns if not present
        try:
            cursor.execute("SELECT executive_summary FROM market_analysis LIMIT 1")
        except sqlite3.OperationalError:
            cursor.execute("ALTER TABLE market_analysis ADD COLUMN executive_summary TEXT")

        try:
            cursor.execute("SELECT profile_id FROM trade_history LIMIT 1")
        except sqlite3.OperationalError:
            cursor.execute("ALTER TABLE trade_history ADD COLUMN profile_id INTEGER DEFAULT 1")

        try:
            cursor.execute("SELECT profile_id FROM portfolio_config LIMIT 1")
        except sqlite3.OperationalError:
            cursor.execute("ALTER TABLE portfolio_config ADD COLUMN profile_id INTEGER DEFAULT 1")

        # Indexes
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_screener_date ON screener_results(date)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_screener_ticker ON screener_results(ticker)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_trades_date ON trade_history(date)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_trades_ticker ON trade_history(ticker)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_holdings_date ON holdings(date)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_market_analysis_date ON market_analysis(date)")

    def _init_tables_postgres(self, cursor):
        """Create PostgreSQL tables."""
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS weekly_snapshots (
                id SERIAL PRIMARY KEY,
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

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS screener_results (
                id SERIAL PRIMARY KEY,
                snapshot_id INTEGER NOT NULL REFERENCES weekly_snapshots(id),
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
                news_headline TEXT
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS trade_history (
                id SERIAL PRIMARY KEY,
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
                profile_id INTEGER DEFAULT 1,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS holdings (
                id SERIAL PRIMARY KEY,
                snapshot_id INTEGER NOT NULL REFERENCES weekly_snapshots(id),
                date TEXT NOT NULL,
                ticker TEXT NOT NULL,
                shares INTEGER NOT NULL,
                avg_cost REAL NOT NULL,
                current_price REAL NOT NULL,
                market_value REAL NOT NULL,
                gain_loss REAL,
                gain_loss_pct REAL,
                weight_pct REAL,
                days_held INTEGER
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS watchlist (
                id SERIAL PRIMARY KEY,
                ticker TEXT NOT NULL UNIQUE,
                added_date TEXT NOT NULL,
                notes TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS market_analysis (
                id SERIAL PRIMARY KEY,
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
                executive_summary TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS portfolio_config (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL,
                profile_id INTEGER DEFAULT 1,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS profiles (
                id SERIAL PRIMARY KEY,
                name TEXT NOT NULL,
                avatar TEXT NOT NULL DEFAULT '🦊',
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Indexes (CREATE INDEX IF NOT EXISTS works in PostgreSQL)
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_screener_date ON screener_results(date)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_screener_ticker ON screener_results(ticker)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_trades_date ON trade_history(date)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_trades_ticker ON trade_history(ticker)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_holdings_date ON holdings(date)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_market_analysis_date ON market_analysis(date)")

    # --- Snapshot Management ---

    def save_weekly_snapshot(self, date: str, portfolio_metrics: Dict) -> int:
        """Save weekly portfolio snapshot. Returns snapshot_id."""
        cursor = self.conn.cursor()

        if self.db_type == 'postgres':
            cursor.execute("""
                INSERT INTO weekly_snapshots
                (date, total_value, cash, invested, ytd_return, week_return,
                 month_return, year_return, holdings_count, benchmark_ytd, alpha_ytd)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (date) DO UPDATE SET
                    total_value = EXCLUDED.total_value, cash = EXCLUDED.cash,
                    invested = EXCLUDED.invested, ytd_return = EXCLUDED.ytd_return,
                    week_return = EXCLUDED.week_return, month_return = EXCLUDED.month_return,
                    year_return = EXCLUDED.year_return, holdings_count = EXCLUDED.holdings_count,
                    benchmark_ytd = EXCLUDED.benchmark_ytd, alpha_ytd = EXCLUDED.alpha_ytd
                RETURNING id
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
            return self._lastrowid(cursor)
        else:
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
        """Save screener results for this week."""
        cursor = self.conn.cursor()
        p = '%s' if self.db_type == 'postgres' else '?'

        for idx, row in stocks.iterrows():
            cursor.execute(f"""
                INSERT INTO screener_results
                (snapshot_id, date, ticker, rank, score, trending_score,
                 trending_classification, price, ma50, ma200, ma200_trend,
                 rs_rating, momentum_3m, momentum_6m, quality_score, news_headline)
                VALUES ({p}, {p}, {p}, {p}, {p}, {p}, {p}, {p}, {p}, {p}, {p}, {p}, {p}, {p}, {p}, {p})
            """, (
                snapshot_id, date, row.get('ticker'), idx + 1,
                row.get('score', 0), row.get('trending_score', 0),
                row.get('trending_classification', 'NEUTRAL'),
                row.get('price', 0), row.get('ma50', 0), row.get('ma200', 0),
                row.get('ma200_trend', 'UNKNOWN'), row.get('rs_rating', 0),
                row.get('momentum_3m', 0), row.get('momentum_6m', 0),
                row.get('quality_score', 0), row.get('news_headline', '')
            ))

        self.conn.commit()

    def save_trade(self, date: str, ticker: str, action: str, shares: int,
                   price: float, amount: float, reason: str = None,
                   kavastu_score: float = None, trending_score: float = None,
                   portfolio_value_before: float = None,
                   portfolio_value_after: float = None,
                   profile_id: int = 1):
        """Save individual trade to history."""
        cursor = self.conn.cursor()
        p = '%s' if self.db_type == 'postgres' else '?'

        cursor.execute(f"""
            INSERT INTO trade_history
            (date, ticker, action, shares, price, amount, reason,
             kavastu_score, trending_score, portfolio_value_before, portfolio_value_after, profile_id)
            VALUES ({p}, {p}, {p}, {p}, {p}, {p}, {p}, {p}, {p}, {p}, {p}, {p})
        """, (
            date, ticker, action, shares, price, amount, reason,
            kavastu_score, trending_score, portfolio_value_before, portfolio_value_after, profile_id
        ))

        self.conn.commit()

    def save_holdings(self, snapshot_id: int, date: str, holdings: List[Dict]):
        """Save current holdings for this snapshot."""
        cursor = self.conn.cursor()
        p = '%s' if self.db_type == 'postgres' else '?'

        for holding in holdings:
            cursor.execute(f"""
                INSERT INTO holdings
                (snapshot_id, date, ticker, shares, avg_cost, current_price,
                 market_value, gain_loss, gain_loss_pct, weight_pct, days_held)
                VALUES ({p}, {p}, {p}, {p}, {p}, {p}, {p}, {p}, {p}, {p}, {p})
            """, (
                snapshot_id, date, holding.get('ticker'),
                holding.get('shares', 0), holding.get('avg_cost', 0),
                holding.get('current_price', 0), holding.get('market_value', 0),
                holding.get('gain_loss', 0), holding.get('gain_loss_pct', 0),
                holding.get('weight_pct', 0), holding.get('days_held', 0)
            ))

        self.conn.commit()

    # --- Read Operations ---

    def get_latest_snapshot(self) -> Optional[Dict]:
        """Get the most recent portfolio snapshot."""
        cursor = self._cursor()
        cursor.execute("SELECT * FROM weekly_snapshots ORDER BY date DESC LIMIT 1")
        row = cursor.fetchone()
        return dict(row) if row else None

    def get_portfolio_history(self, days: int = 365) -> pd.DataFrame:
        """Get portfolio value history."""
        if self.db_type == 'postgres':
            query = f"""
                SELECT date, total_value, cash, invested, ytd_return,
                       week_return, month_return, year_return, benchmark_ytd, alpha_ytd
                FROM weekly_snapshots
                WHERE date >= (CURRENT_DATE - INTERVAL '{days} days')::text
                ORDER BY date ASC
            """
        else:
            query = f"""
                SELECT date, total_value, cash, invested, ytd_return,
                       week_return, month_return, year_return, benchmark_ytd, alpha_ytd
                FROM weekly_snapshots
                WHERE date >= date('now', '-{days} days')
                ORDER BY date ASC
            """
        return pd.read_sql_query(query, self.conn)

    def get_trade_history(self, ticker: str = None, days: int = 365, profile_id: int = None) -> pd.DataFrame:
        """Get trade history, optionally filtered by ticker and/or profile."""
        if self.db_type == 'postgres':
            conditions = [f"date >= (CURRENT_DATE - INTERVAL '{days} days')::text"]
        else:
            conditions = [f"date >= date('now', '-{days} days')"]
        params = []
        p = '%s' if self.db_type == 'postgres' else '?'

        if ticker:
            conditions.append(f"ticker = {p}")
            params.append(ticker)
        if profile_id is not None:
            conditions.append(f"profile_id = {p}")
            params.append(profile_id)

        where = " AND ".join(conditions)
        query = f"SELECT * FROM trade_history WHERE {where} ORDER BY date DESC"
        return pd.read_sql_query(query, self.conn, params=params if params else None)

    def get_screener_history(self, ticker: str = None, weeks: int = 12) -> pd.DataFrame:
        """Get screener results history."""
        days = weeks * 7
        if self.db_type == 'postgres':
            date_filter = f"date >= (CURRENT_DATE - INTERVAL '{days} days')::text"
        else:
            date_filter = f"date >= date('now', '-{days} days')"

        if ticker:
            p = '%s' if self.db_type == 'postgres' else '?'
            query = f"""
                SELECT * FROM screener_results
                WHERE ticker = {p} AND {date_filter}
                ORDER BY date DESC
            """
            return pd.read_sql_query(query, self.conn, params=(ticker,))
        else:
            query = f"""
                SELECT * FROM screener_results
                WHERE {date_filter}
                ORDER BY date DESC, rank ASC
            """
            return pd.read_sql_query(query, self.conn)

    def get_trending_performance_analysis(self) -> Dict:
        """Analyze performance of stocks by trending classification."""
        cursor = self._cursor()

        if self.db_type == 'postgres':
            date_calc = "(s.date::date + INTERVAL '7 days')::text"
        else:
            date_calc = "date(s.date, '+7 days')"

        query = f"""
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
                AND t.date <= {date_calc}
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

    # --- Watchlist ---

    def add_to_watchlist(self, ticker: str, notes: str = "") -> bool:
        """Add a stock to the watchlist. Returns True if added, False if already exists."""
        cursor = self.conn.cursor()
        try:
            if self.db_type == 'postgres':
                cursor.execute("""
                    INSERT INTO watchlist (ticker, added_date, notes)
                    VALUES (%s, CURRENT_DATE::text, %s)
                """, (ticker.upper(), notes))
            else:
                cursor.execute("""
                    INSERT INTO watchlist (ticker, added_date, notes)
                    VALUES (?, date('now'), ?)
                """, (ticker.upper(), notes))
            self.conn.commit()
            return True
        except (sqlite3.IntegrityError, Exception) as e:
            if 'unique' in str(e).lower() or 'duplicate' in str(e).lower() or isinstance(e, sqlite3.IntegrityError):
                self.conn.rollback() if self.db_type == 'postgres' else None
                return False
            raise

    def remove_from_watchlist(self, ticker: str) -> bool:
        """Remove a stock from the watchlist. Returns True if removed."""
        cursor = self.conn.cursor()
        p = '%s' if self.db_type == 'postgres' else '?'
        cursor.execute(f"DELETE FROM watchlist WHERE ticker = {p}", (ticker.upper(),))
        self.conn.commit()
        return cursor.rowcount > 0

    def update_watchlist_notes(self, ticker: str, notes: str) -> bool:
        """Update notes for a watchlist stock."""
        cursor = self.conn.cursor()
        p = '%s' if self.db_type == 'postgres' else '?'
        cursor.execute(f"UPDATE watchlist SET notes = {p} WHERE ticker = {p}", (notes, ticker.upper()))
        self.conn.commit()
        return cursor.rowcount > 0

    def get_watchlist(self) -> List[Dict]:
        """Get all watchlist stocks with their latest screener data if available."""
        cursor = self._cursor()
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
        cursor = self._cursor()
        p = '%s' if self.db_type == 'postgres' else '?'
        cursor.execute(f"SELECT 1 FROM watchlist WHERE ticker = {p}", (ticker.upper(),))
        return cursor.fetchone() is not None

    # --- Market Analysis ---

    def save_market_analysis(self, analysis: Dict) -> int:
        """Save a market analysis entry. Returns the ID."""
        cursor = self.conn.cursor()
        p = '%s' if self.db_type == 'postgres' else '?'
        returning = ' RETURNING id' if self.db_type == 'postgres' else ''

        cursor.execute(f"""
            INSERT INTO market_analysis
            (date, source, source_type, title, url, regime, summary,
             tickers_mentioned, buy_signals, sell_signals, targets, raw_content,
             executive_summary)
            VALUES ({p}, {p}, {p}, {p}, {p}, {p}, {p}, {p}, {p}, {p}, {p}, {p}, {p}){returning}
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
            analysis.get('raw_content', ''),
            analysis.get('executive_summary', '')
        ))
        self.conn.commit()
        if self.db_type == 'postgres':
            return self._lastrowid(cursor)
        return cursor.lastrowid

    def get_market_analyses(self, limit: int = 20, source: str = None) -> List[Dict]:
        """Get recent market analyses."""
        cursor = self._cursor()
        p = '%s' if self.db_type == 'postgres' else '?'

        if source:
            cursor.execute(f"""
                SELECT * FROM market_analysis
                WHERE source = {p}
                ORDER BY date DESC, created_at DESC LIMIT {p}
            """, (source, limit))
        else:
            cursor.execute(f"""
                SELECT * FROM market_analysis
                ORDER BY date DESC, created_at DESC LIMIT {p}
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
        cursor = self._cursor()
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
        cursor = self._cursor()
        cursor.execute("SELECT * FROM profiles ORDER BY id")
        return [dict(r) for r in cursor.fetchall()]

    def create_profile(self, name: str, avatar: str = '🦊') -> int:
        """Create a new profile. Returns profile id."""
        cursor = self.conn.cursor()
        p = '%s' if self.db_type == 'postgres' else '?'

        if self.db_type == 'postgres':
            cursor.execute(
                f"INSERT INTO profiles (name, avatar) VALUES ({p}, {p}) RETURNING id",
                (name, avatar)
            )
            self.conn.commit()
            return self._lastrowid(cursor)
        else:
            cursor.execute(
                f"INSERT INTO profiles (name, avatar) VALUES ({p}, {p})",
                (name, avatar)
            )
            self.conn.commit()
            return cursor.lastrowid

    def update_profile(self, profile_id: int, name: str = None, avatar: str = None) -> bool:
        """Update a profile's name or avatar."""
        cursor = self.conn.cursor()
        p = '%s' if self.db_type == 'postgres' else '?'
        if name is not None:
            cursor.execute(f"UPDATE profiles SET name = {p} WHERE id = {p}", (name, profile_id))
        if avatar is not None:
            cursor.execute(f"UPDATE profiles SET avatar = {p} WHERE id = {p}", (avatar, profile_id))
        self.conn.commit()
        return cursor.rowcount > 0

    def delete_profile(self, profile_id: int) -> bool:
        """Delete a profile and all its trades/config."""
        cursor = self.conn.cursor()
        p = '%s' if self.db_type == 'postgres' else '?'
        cursor.execute(f"DELETE FROM trade_history WHERE profile_id = {p}", (profile_id,))
        cursor.execute(f"DELETE FROM portfolio_config WHERE profile_id = {p}", (profile_id,))
        cursor.execute(f"DELETE FROM profiles WHERE id = {p}", (profile_id,))
        self.conn.commit()
        return cursor.rowcount > 0

    # --- Active Portfolio Management (per profile) ---

    def set_portfolio_config(self, key: str, value: str, profile_id: int = 1):
        """Set a portfolio config value for a profile."""
        cursor = self.conn.cursor()
        compound_key = f"{key}:{profile_id}"
        p = '%s' if self.db_type == 'postgres' else '?'

        if self.db_type == 'postgres':
            cursor.execute(f"""
                INSERT INTO portfolio_config (key, value, profile_id, updated_at)
                VALUES ({p}, {p}, {p}, CURRENT_TIMESTAMP)
                ON CONFLICT (key) DO UPDATE SET value = EXCLUDED.value,
                    profile_id = EXCLUDED.profile_id, updated_at = CURRENT_TIMESTAMP
            """, (compound_key, value, profile_id))
        else:
            cursor.execute("""
                INSERT OR REPLACE INTO portfolio_config (key, value, profile_id, updated_at)
                VALUES (?, ?, ?, CURRENT_TIMESTAMP)
            """, (compound_key, value, profile_id))
        self.conn.commit()

    def get_portfolio_config(self, key: str, default: str = None, profile_id: int = 1) -> Optional[str]:
        """Get a portfolio config value for a profile."""
        cursor = self._cursor()
        compound_key = f"{key}:{profile_id}"
        p = '%s' if self.db_type == 'postgres' else '?'

        cursor.execute(f"SELECT value FROM portfolio_config WHERE key = {p}", (compound_key,))
        row = cursor.fetchone()
        if row:
            return row['value'] if isinstance(row, dict) else row[0]
        # Fallback: try old-style key
        cursor.execute(f"SELECT value FROM portfolio_config WHERE key = {p} AND profile_id = {p}", (key, profile_id))
        row = cursor.fetchone()
        if row:
            return row['value'] if isinstance(row, dict) else row[0]
        return default

    def get_active_positions(self, profile_id: int = 1) -> List[Dict]:
        """Compute active stock positions from trade history for a profile."""
        cursor = self._cursor()
        p = '%s' if self.db_type == 'postgres' else '?'

        cursor.execute(f"""
            SELECT
                ticker,
                SUM(CASE WHEN action = 'BUY' THEN shares ELSE 0 END) as total_bought,
                SUM(CASE WHEN action = 'SELL' THEN shares ELSE 0 END) as total_sold,
                SUM(CASE WHEN action = 'BUY' THEN amount ELSE 0 END) as total_cost,
                SUM(CASE WHEN action = 'SELL' THEN amount ELSE 0 END) as total_proceeds,
                MIN(date) as first_buy_date,
                MAX(date) as last_trade_date
            FROM trade_history
            WHERE profile_id = {p}
            GROUP BY ticker
            HAVING SUM(CASE WHEN action = 'BUY' THEN shares ELSE 0 END) >
                   SUM(CASE WHEN action = 'SELL' THEN shares ELSE 0 END)
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
        cursor = self._cursor()
        p = '%s' if self.db_type == 'postgres' else '?'

        cursor.execute(f"""
            SELECT
                COALESCE(SUM(CASE WHEN action = 'BUY' THEN amount ELSE 0 END), 0) as total_buys,
                COALESCE(SUM(CASE WHEN action = 'SELL' THEN amount ELSE 0 END), 0) as total_sells
            FROM trade_history
            WHERE profile_id = {p}
        """, (profile_id,))

        row = cursor.fetchone()
        d = dict(row)
        return round(initial - d['total_buys'] + d['total_sells'], 2)

    def delete_trade(self, trade_id: int) -> bool:
        """Delete a trade by ID. Returns True if deleted."""
        cursor = self.conn.cursor()
        p = '%s' if self.db_type == 'postgres' else '?'
        cursor.execute(f"DELETE FROM trade_history WHERE id = {p}", (trade_id,))
        self.conn.commit()
        return cursor.rowcount > 0

    def cleanup_old_data(self, keep_weeks: int = 52):
        """Remove old screener results (keep portfolio/trade history forever)."""
        cursor = self.conn.cursor()
        days = keep_weeks * 7

        if self.db_type == 'postgres':
            cursor.execute(f"""
                DELETE FROM screener_results
                WHERE date < (CURRENT_DATE - INTERVAL '{days} days')::text
            """)
        else:
            cursor.execute(f"""
                DELETE FROM screener_results
                WHERE date < date('now', '-{days} days')
            """)

        deleted = cursor.rowcount
        self.conn.commit()

        if self.db_type == 'sqlite':
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
    print("Testing database module...")
    db_type = "PostgreSQL" if os.environ.get('DATABASE_URL') else "SQLite"
    print(f"Using: {db_type}")

    with PortfolioDB() as db:
        if db.db_path:
            print(f"  Database at: {db.db_path}")
        print(f"  Backend: {db.db_type}")
        print(f"  Tables initialized successfully")

        latest = db.get_latest_snapshot()
        if latest:
            print(f"  Latest snapshot: {latest['date']}, Value: {latest['total_value']:,.0f} SEK")
        else:
            print("  No snapshots yet")

        print("\n  Database module working!")
