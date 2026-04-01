# Bolt.new Prompt - Kavastu Dashboard

Copy everything below the line into Bolt.new:

---

Build a **stock trading dashboard** using Next.js 14 (App Router), React, TypeScript, and Tailwind CSS. The dashboard monitors a Swedish stock momentum trading system called "Kavastu".

## Tech Stack
- Next.js 14 with App Router
- TypeScript
- Tailwind CSS
- shadcn/ui components (use `npx shadcn-ui@latest init` and add: card, table, badge, tabs, separator)
- Recharts for charts
- lucide-react for icons

## Layout & Design
- **Dark theme** (slate-900 background, slate-800 cards)
- **iPad-optimized** - looks great at 1024x768 and 1366x1024
- Responsive: works on desktop and tablet
- Clean, professional financial dashboard aesthetic
- Use a sidebar navigation on desktop, bottom tabs on mobile/tablet

## API Configuration
Create a file `lib/api.ts` that fetches from a configurable API base URL:

```typescript
const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
```

All data comes from these API endpoints (already built):

```
GET /api/dashboard     → Full dashboard summary (snapshot, top stocks, trending, buy signals)
GET /api/screener      → All screener results (query params: limit, min_score, trending)
GET /api/stock/{ticker} → Stock detail with score history
GET /api/history       → Portfolio value history for charts (query param: days)
GET /api/trending      → Trending analysis (HOT/COLD/NEUTRAL breakdown)
GET /api/recommendations → Trade recommendations (BUY/SELL signals)
```

## API Response Types

```typescript
interface PortfolioSnapshot {
  date: string;
  total_value: number;
  cash: number;
  invested: number;
  ytd_return: number;
  week_return: number;
  holdings_count: number;
}

interface ScreenerStock {
  ticker: string;
  rank: number;
  score: number;           // 0-130 Kavastu score
  trending_score: number;  // 0-100 trending score
  trending_classification: string; // "HOT" | "COLD" | "NEUTRAL"
  price: number;
  ma200_trend?: string;
}

interface TradeSignal {
  ticker: string;
  action: string;    // "BUY" or "SELL"
  score: number;
  trending_score: number;
  trending_classification: string;
  price: number;
  reason: string;
}

interface DashboardSummary {
  snapshot: PortfolioSnapshot | null;
  top_stocks: ScreenerStock[];
  hot_stocks: ScreenerStock[];
  cold_stocks: ScreenerStock[];
  buy_signals: TradeSignal[];
  total_screened: number;
  last_updated: string;
}
```

## Pages to Build

### 1. Dashboard (/) — Main Overview
This is the primary page. Show:

**Top Row - 4 KPI Cards:**
- Portfolio Value (large number, formatted with spaces as thousands separator: "100 000 SEK")
- Week Return (percentage, green if positive, red if negative)
- Cash Available
- Active Holdings count

**Middle Section - Two columns:**

Left column (60%):
- **Top 10 Stocks Table**: Columns: Rank, Ticker, Kavastu Score (with a colored progress bar 0-130), Trending Score, Trending Badge (green "HOT", blue "NEUTRAL", red "COLD"), Price. Clicking a row navigates to the stock detail page.

Right column (40%):
- **Trade Signals Card**: List of BUY recommendations with green badges. Each shows ticker, score, trending classification, and the reason text. If no signals, show "No signals this week" in muted text.
- **Trending Summary Card**: Show counts - X HOT, Y COLD, Z NEUTRAL with colored badges. List the top 3 hottest stocks below.

**Bottom Section:**
- **Portfolio Value Chart**: Line chart using Recharts showing portfolio value over time (from /api/history). X-axis: dates. Y-axis: SEK value.

### 2. Screener (/screener) — Full Stock Rankings
- Full table of all screened stocks (fetched from /api/screener?limit=100)
- Sortable columns: Rank, Ticker, Score, Trending Score, Classification, Price
- Filter bar at top: dropdown to filter by trending (ALL / HOT / COLD / NEUTRAL), minimum score slider
- Color-coded score cells: green >= 100, yellow 80-99, red < 80
- Click any row to go to stock detail

### 3. Trending (/trending) — Trending Analysis
- Three sections: HOT, NEUTRAL, COLD (fetched from /api/trending)
- Each section shows stocks as cards in a grid
- HOT cards have a subtle red/orange glow border
- COLD cards have a subtle blue glow border
- Each card shows: Ticker, Trending Score (large), Kavastu Score, Price
- Summary bar at top showing the distribution as a horizontal stacked bar

### 4. Stock Detail (/stock/[ticker]) — Individual Stock
- Fetched from /api/stock/{ticker}
- Header: Ticker name, current price, Kavastu score badge, trending badge
- Score History Chart: Line chart showing Kavastu score over past 12 weeks
- Trending History: Show how trending classification changed over time
- Trade History Table: If any trades exist for this stock

### 5. History (/history) — Portfolio Performance
- Large portfolio value chart (from /api/history?days=365)
- Below: table of weekly snapshots showing date, value, week return, holdings count
- Toggle between 3 months / 6 months / 1 year / all time

## Specific UI Details

**Score Badge Component:**
Create a reusable ScoreBadge that shows the Kavastu score (0-130) with color:
- >= 110: bright green background
- >= 100: green background
- >= 80: yellow background
- < 80: red background

**Trending Badge Component:**
Create a reusable TrendingBadge:
- HOT: red/orange badge with flame icon
- COLD: blue badge with snowflake icon
- NEUTRAL: gray badge

**Number Formatting:**
- All SEK values use space as thousands separator: "100 000 SEK"
- Percentages show 2 decimal places with +/- prefix
- Scores show 1 decimal place

**Loading States:**
- Use skeleton loaders while API data loads
- Show a spinner on the main dashboard while fetching

**Empty States:**
- If no data yet: "No data available. Run the weekly automation to populate."
- If no buy signals: "No buy signals this week. Portfolio is healthy."

## Navigation
Sidebar (desktop) / bottom tabs (mobile) with these items:
- Dashboard (LayoutDashboard icon)
- Screener (Search icon)
- Trending (TrendingUp icon)
- History (LineChart icon)

Header bar shows "Kavastu" logo text + "Last updated: {date}" on the right.

## Important Notes
- Use `fetch()` with the API_BASE for all data - no mock data, no hardcoded values
- Handle loading and error states gracefully
- All monetary values are in SEK (Swedish Krona)
- The app should work even if the API returns empty data (show empty states)
- Use Swedish locale for number formatting where possible
