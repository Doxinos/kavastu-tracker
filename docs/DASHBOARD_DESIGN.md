# Kavastu Portfolio Dashboard - World-Class Design

**Design Philosophy:** Clean, actionable, and beautiful. Every element serves a purpose. Information hierarchy guides the eye from overview → details → action.

---

## 🎨 Design Principles

### 1. Visual Hierarchy
- **Primary:** What you need to act on (buy/sell signals)
- **Secondary:** Current status (holdings, performance)
- **Tertiary:** Historical trends (charts, tracking)

### 2. Color Psychology
- **Green (#00C853):** Buy signals, gains, positive momentum
- **Red (#D32F2F):** Sell signals, losses, warnings
- **Yellow (#FFC107):** Hold signals, caution, neutral
- **Blue (#1976D2):** Information, metrics, passive data
- **Gray (#757575):** Inactive, historical, background

### 3. Sunday Evening Workflow
- **19:30:** Quick glance → Portfolio Overview (Sheet 1)
- **19:35:** Deep dive → Trade Recommendations (Sheet 4)
- **19:40:** Cross-check → Current Holdings (Sheet 2)
- **19:45:** Validate → Screener Results (Sheet 3)
- **20:00:** Execute on Avanza

### 4. Mobile-First
- Must work on iPad/iPhone (reviewing on couch)
- Large touch targets
- Readable fonts (12pt minimum)
- No horizontal scrolling

---

## 📊 Sheet 1: Portfolio Overview - COMMAND CENTER

**Purpose:** 30-second status check. "How am I doing? What's next?"

### Layout (A1:I30)

```
┌─────────────────────────────────────────────────────────────────────────┐
│  KAVASTU PORTFOLIO TRACKER                    Last Updated: 2026-02-16  │
│                                                          19:32 (LIVE)    │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  ┌──────────────────────┐  ┌──────────────────────┐  ┌───────────────┐ │
│  │  TOTAL VALUE         │  │  WEEKLY PERFORMANCE  │  │  THIS WEEK     │ │
│  │  325,450 SEK  ↑2.3%  │  │  +7,285 SEK (+2.29%) │  │  BUY: 3       │ │
│  │                      │  │                      │  │  SELL: 2      │ │
│  │  Cash:    65,200 SEK │  │  vs OMXS30: +0.8%   │  │  HOLD: 12     │ │
│  │  Invested: 260,250   │  │  Alpha:     +0.8%   │  │               │ │
│  └──────────────────────┘  └──────────────────────┘  └───────────────┘ │
│                                                                          │
│  ┌─────────────────────────────────────────────────────────────────────┐│
│  │                         EQUITY CURVE (YTD)                          ││
│  │  330K ┤                                                      ╭──    ││
│  │  320K ┤                                              ╭──────╯       ││
│  │  310K ┤                                      ╭──────╯               ││
│  │  300K ┤                              ╭──────╯                       ││
│  │  290K ┤                      ╭──────╯                               ││
│  │  280K ┤              ╭──────╯                                       ││
│  │  270K ┼──────────────╯                                              ││
│  │       Jan    Feb    Mar    Apr    May    Jun    Jul    Aug          ││
│  └─────────────────────────────────────────────────────────────────────┘│
│                                                                          │
│  PERFORMANCE METRICS                    RISK METRICS                    │
│  ├─ Total Return:    +25.45%           ├─ Sharpe Ratio:    2.15        │
│  ├─ YTD Return:      +8.23%            ├─ Max Drawdown:   -12.3%       │
│  ├─ 30d Return:      +2.29%            ├─ Current DD:      -0.0%       │
│  ├─ 7d Return:       +1.15%            ├─ Volatility:      18.5%       │
│  └─ vs OMXS30:       +12.4%            └─ Win Rate:        67%          │
│                                                                          │
│  HOLDINGS                               TAX & DIVIDENDS                 │
│  ├─ Current:         17 stocks         ├─ Dividends YTD:  4,230 SEK    │
│  ├─ Target:          17-20 stocks      ├─ Div Yield:       1.3%        │
│  ├─ Top 5 Weight:    28.5%             ├─ ISK Tax (YTD):  1,850 SEK    │
│  └─ Avg Score:       112.5             └─ Net After Tax:  +24.1%       │
│                                                                          │
│  ⚡ WEEKLY CHECKLIST                    📅 NEXT ACTIONS                 │
│  ☑ Screener Run:     ✅ Complete        Sun 19:45  Review signals       │
│  ☑ Trades Ready:     ✅ 5 signals       Sun 20:00  Execute on Avanza    │
│  ☐ Executed:         Pending            Sun 20:30  Update portfolio     │
│  ☐ Portfolio File:   Pending            Sun 21:00  Done! 🍺             │
└─────────────────────────────────────────────────────────────────────────┘
```

### Design Specs

**Title Row (A1:I1)**
- Font: Roboto Bold 18pt
- Background: #1976D2 (Blue)
- Text: White
- Height: 40px
- Merge cells for centered title

**Live Indicator (H1:I1)**
- "Last Updated: [timestamp]"
- Auto-updates with each refresh
- Font: Roboto 10pt, Light gray

**Big Numbers (A3:I8)**
- 3 cards side-by-side
- White background, gray borders
- Numbers: Roboto Bold 24pt
- Labels: Roboto 11pt, gray
- Up/down arrows with color coding

**Equity Curve (A10:I18)**
- Line chart: #1976D2 (blue), 3px thick
- Area fill: Light blue gradient (20% opacity)
- Grid: Light gray, subtle
- Axis labels: Roboto 10pt
- Benchmark line: Dotted gray for comparison

**Metrics Grid (A20:I27)**
- Two columns: Performance (left), Risk (right)
- Tree structure with ├─ └─ characters
- Green numbers for positive, red for negative
- Bold labels, regular values

**Weekly Checklist (A29:E32)**
- ☑ ☐ checkboxes (manual update)
- Green checkmarks for done
- Action items in bold

**Next Actions (G29:I32)**
- Timeline format with times
- Next action highlighted in yellow
- Current time in bold

### Conditional Formatting

```
IF(B3>0, GREEN, RED)                    # Weekly performance color
IF(E21<-15%, RED, IF(E21<-10%, YELLOW)) # Drawdown warning
IF(A30="✅", GREEN_BACKGROUND)           # Completed checklist items
```

---

## 💼 Sheet 2: Current Holdings - PORTFOLIO DETAIL

**Purpose:** Deep dive into each position. What's working? What's not?

### Layout (A1:M50)

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│  MY 17 STOCKS - Current Portfolio                      Updated: 2026-02-16 19:32    │
├──────┬────────────┬────────┬─────────┬─────────┬──────────┬─────────┬───────┬──────┤
│ Rank │ Ticker     │ Name   │ Shares  │ Avg ₱   │ Current ₱│ Value   │ P&L % │Signal│
├──────┼────────────┼────────┼─────────┼─────────┼──────────┼─────────┼───────┼──────┤
│  1   │ VOLV-B.ST  │ Volvo B│   250   │  245.20 │  268.50  │ 67,125  │ +9.5% │ 🟢115│
│  2   │ ASSA-B.ST  │ Assa AB│   180   │  308.00 │  325.00  │ 58,500  │ +5.5% │ 🟢118│
│  3   │ SAND.ST    │ Sandvik│   210   │  218.50 │  232.00  │ 48,720  │ +6.2% │ 🟢112│
│  4   │ ATCO-A.ST  │ Atlas C│   320   │  142.00 │  148.50  │ 47,520  │ +4.6% │ 🟡108│
│  5   │ KINV-B.ST  │ Kinnevik│  165   │  104.00 │  108.20  │ 17,853  │ +4.0% │ 🟡102│
│  ... │            │        │         │         │          │         │       │      │
│ 15   │ SSAB-A.ST  │ SSAB A │   380   │   42.50 │   44.80  │ 17,024  │ +5.4% │ 🟢110│
│ 16   │ ALFA.ST    │ Alfa L │   145   │  348.00 │  351.20  │ 50,924  │ +0.9% │ 🔴 88│ ⚠️
│ 17   │ NIBE-B.ST  │ NIBE   │   280   │   52.30 │   51.80  │ 14,504  │ -1.0% │ 🔴 85│ ⚠️
├──────┴────────────┴────────┴─────────┴─────────┴──────────┴─────────┴───────┴──────┤
│  TOTALS:  17 stocks         3,850 shares              260,250 SEK    +6.8%         │
└─────────────────────────────────────────────────────────────────────────────────────┘

PORTFOLIO ANALYSIS
┌──────────────────────────┬──────────────────────────┬──────────────────────────────┐
│  TOP PERFORMERS (7d)     │  BOTTOM PERFORMERS (7d)  │  ACTION REQUIRED             │
│  1. VOLV-B  +12.3%       │  1. NIBE-B   -8.2% 🔴   │  🔴 SELL: 2 stocks (score<90)│
│  2. ASSA-B  +8.5%        │  2. ALFA     -4.1% 🔴   │  🟡 WATCH: 3 stocks (90-100) │
│  3. SSAB-A  +7.2%        │  3. SEB-A    -2.3%      │  🟢 STRONG: 12 stocks (>110) │
│  4. SAND    +6.8%        │                          │                              │
│  5. SWED-A  +5.9%        │  ⚠️ Review bottom 3      │  Next rebalance: Sunday 20:00│
└──────────────────────────┴──────────────────────────┴──────────────────────────────┘

SECTOR ALLOCATION                        POSITION SIZING
┌──────────────────────┐                 ┌──────────────────────────────────────┐
│ Industrials    35%   │ ████████        │  Largest:  VOLV-B    25.8%  (within) │
│ Financials     28%   │ ██████          │  Smallest: NIBE-B     5.6%  (within) │
│ Tech           18%   │ ████            │  Average:  15,309 SEK                │
│ Consumer       12%   │ ███             │  Median:   17,024 SEK                │
│ Healthcare      7%   │ ██              │  Target:   17-20 stocks              │
└──────────────────────┘                 └──────────────────────────────────────┘
```

### Design Specs

**Header Row (A1:M1)**
- Font: Roboto Bold 14pt
- Background: #424242 (Dark gray)
- Text: White
- Freeze row for scrolling

**Holdings Table (A3:M20)**
- Alternating row colors: White / Light gray (#F5F5F5)
- Borders: Light gray, 1px
- Font: Roboto 11pt
- Numbers: Right-aligned, monospace

**Signal Column (M3:M20)**
- Emoji + Score combined
- 🟢 = Green background (score ≥110)
- 🟡 = Yellow background (90-109)
- 🔴 = Red background + ⚠️ (score <90)
- Font: Bold 12pt

**P&L Column (K3:K20)**
- Conditional formatting:
  ```
  IF(>0%, GREEN_TEXT, RED_TEXT)
  IF(>5%, BOLD)
  IF(<-5%, BOLD_RED)
  ```

**Analysis Boxes (A22:M35)**
- 3 cards side-by-side
- White background, gray borders, shadow
- Headers: Roboto Bold 12pt
- Content: Roboto 11pt

**Charts (A37:M50)**
- Sector: Horizontal bar chart with labels
- Position sizing: Mini histogram
- Color: Blues/grays palette

### Conditional Formatting Rules

```
Row Highlighting:
IF(Signal = 🔴, ROW_BACKGROUND = #FFEBEE)  # Light red for sells
IF(Signal = 🟢, ROW_BACKGROUND = #E8F5E9)  # Light green for strong
IF(P&L% > 10%, BOLD_GREEN)
IF(P&L% < -5%, BOLD_RED_BACKGROUND)

Value Formatting:
Currency: "0 SEK" with thousands separator
Percentage: "0.0%" with + sign for positive
Shares: "#,##0" integer format
```

---

## 🔍 Sheet 3: Screener Results - TOP 70 RANKED

**Purpose:** Discover new opportunities. Which stocks are rising?

### Layout (A1:K75)

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│  WEEKLY SCREENER RESULTS - Top 70 Swedish Stocks    Run: 2026-02-16 19:05      │
│  Sorted by Score (0-130 points) · Green = Buy zone · Yellow = Watch zone       │
├──────┬────────────┬──────────────────┬───────┬─────────┬──────────┬────────────┤
│ Rank │ Ticker     │ Company Name     │ Score │ Price   │ MA200    │ In Port?  │
├──────┼────────────┼──────────────────┼───────┼─────────┼──────────┼────────────┤
│  🥇1 │ VOLV-B.ST  │ Volvo B          │  125  │ 268.50  │ ↗️ Rising │ ✅ Owned  │
│  🥈2 │ ASSA-B.ST  │ Assa Abloy B     │  123  │ 325.00  │ ↗️ Rising │ ✅ Owned  │
│  🥉3 │ SKF-B.ST   │ SKF B            │  121  │ 195.20  │ ↗️ Rising │ ❌ BUY!   │
│   4  │ SAND.ST    │ Sandvik          │  120  │ 232.00  │ ↗️ Rising │ ✅ Owned  │
│   5  │ SSAB-A.ST  │ SSAB A           │  118  │  44.80  │ ↗️ Rising │ ✅ Owned  │
│   6  │ INVE-B.ST  │ Investor B       │  117  │ 245.50  │ ↗️ Rising │ ❌ BUY!   │
│   7  │ SEB-A.ST   │ SEB A            │  115  │ 142.30  │ → Flat   │ ✅ Owned  │
│   8  │ SWED-A.ST  │ Swedbank A       │  115  │ 208.40  │ ↗️ Rising │ ✅ Owned  │
│   9  │ ATCO-A.ST  │ Atlas Copco A    │  114  │ 148.50  │ ↗️ Rising │ ✅ Owned  │
│  10  │ HM-B.ST    │ H&M B            │  113  │ 162.80  │ ↗️ Rising │ ❌ BUY!   │
│  ... │            │                  │       │         │          │           │
│  68  │ NCC-B.ST   │ NCC B            │   92  │  68.50  │ ↘️ Falling│ ❌        │
│  69  │ TELIA.ST   │ Telia Company    │   91  │  28.30  │ → Flat   │ ❌        │
│  70  │ VOLCAR-B   │ Volvo Car B      │   90  │  32.10  │ ↘️ Falling│ ❌        │
├──────┴────────────┴──────────────────┴───────┴─────────┴──────────┴────────────┤
│  BUY ZONE (≥110):  23 stocks  │  WATCH ZONE (90-109):  35 stocks  │  <90:  52  │
└─────────────────────────────────────────────────────────────────────────────────┘

SCREENER INSIGHTS
┌────────────────────────────────┬──────────────────────────────────────────────┐
│  NEW OPPORTUNITIES (Not Owned) │  SCORE BREAKDOWN (Top 10 Average)           │
│  ────────────────────────────  │  ─────────────────────────────────────────  │
│  1. SKF-B.ST       Score: 121  │  Technical (45):      38.2 pts  85%  ████   │
│  2. INVE-B.ST      Score: 117  │  Rel Strength (30):   26.5 pts  88%  ████   │
│  3. HM-B.ST        Score: 113  │  Momentum (30):       24.8 pts  83%  ████   │
│  4. HEXA-B.ST      Score: 111  │  Quality (25):        19.5 pts  78%  ███    │
│  5. ALFA.ST        Score: 110  │  ────────────────────────────────────────   │
│                                 │  Total Average:      109.0 / 130 pts (84%)  │
│  💡 3 new buy candidates!       │                                             │
│     (Score ≥110, not owned)     │  🎯 Top stocks are technically strong       │
└────────────────────────────────┴──────────────────────────────────────────────┘

MARKET SENTIMENT                         TREND ANALYSIS
┌────────────────────────────────┐      ┌─────────────────────────────────────┐
│  Stocks Above MA200:  68%  ████│      │  Rising Trends:    42 stocks  🟢   │
│  Golden Crosses (7d): 12       │      │  Flat Trends:      18 stocks  🟡   │
│  Death Crosses (7d):  3        │      │  Falling Trends:   10 stocks  🔴   │
│                                │      │                                     │
│  Market Regime:  🟢 BULL       │      │  ⚡ Momentum is STRONG              │
│  Breadth Score:  72 / 100      │      │     Consider adding positions       │
└────────────────────────────────┘      └─────────────────────────────────────┘
```

### Design Specs

**Header (A1:K2)**
- Two-line header with subtitle
- Font: Roboto Bold 14pt / Regular 10pt
- Background: #1976D2 → #0D47A1 gradient
- Text: White
- Freeze for scrolling

**Rank Icons (A3:A72)**
- 🥇🥈🥉 for top 3
- Numbers for 4-70
- Background: Light yellow for top 10
- Font: Bold

**Score Column (D3:D72)**
- Large bold numbers (14pt)
- Color gradient:
  - 120-130: Dark green
  - 110-119: Green
  - 100-109: Light green
  - 90-99: Yellow
  - <90: Orange

**In Portfolio Column (K3:K72)**
- ✅ Green "Owned" for current holdings
- ❌ "BUY!" in red bold for opportunities
- Regular ❌ for others
- Makes it instantly scannable

**Zone Summary Bar (A73:K73)**
- Merged cells with counts
- Background colors matching zones
- Bold white text

**Insight Boxes (A75:K90)**
- 4 boxes in 2x2 grid
- Clean separation with borders
- Mini charts and progress bars
- Actionable summaries

### Interactive Elements

**Filters (A2)**
- Dropdown: "All | Owned | Not Owned | Buy Zone"
- Instantly filter the list

**Conditional Row Highlighting**
```
IF(Score ≥ 120, BACKGROUND = #C8E6C9)  # Light green
IF(Score ≥ 110, BACKGROUND = #E8F5E9)  # Very light green
IF(Score < 90,  BACKGROUND = #FFF9C4)  # Light yellow
IF(In_Portfolio = "Owned", BOLD)
```

---

## 📋 Sheet 4: Trade Recommendations - ACTION LIST

**Purpose:** Exactly what to do. Copy this to Avanza and execute.

### Layout (A1:H50)

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│  ⚡ THIS WEEK'S TRADES - Ready to Execute          Sunday, February 16, 2026    │
│  Copy these signals to Avanza and execute Sunday 20:00-20:30                   │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                  │
│  🟢 BUY SIGNALS (3 stocks) ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━│
│                                                                                  │
│  ┌──────────────┬───────┬─────────┬─────────┬────────────┬────────────────────┐│
│  │ Ticker       │ Score │ Price   │ Shares  │ Amount     │ Reason             ││
│  ├──────────────┼───────┼─────────┼─────────┼────────────┼────────────────────┤│
│  │ SKF-B.ST     │  121  │ 195.20  │   180   │  35,136 ₭  │ New top 3 scorer   ││
│  │ 🎯 TOP PICK  │       │         │         │            │ Rising MA200       ││
│  ├──────────────┼───────┼─────────┼─────────┼────────────┼────────────────────┤│
│  │ INVE-B.ST    │  117  │ 245.50  │   120   │  29,460 ₭  │ Strong momentum    ││
│  │              │       │         │         │            │ Quality score: 22  ││
│  ├──────────────┼───────┼─────────┼─────────┼────────────┼────────────────────┤│
│  │ HM-B.ST      │  113  │ 162.80  │   165   │  26,862 ₭  │ Retail recovery    ││
│  │              │       │         │         │            │ Above MA200        ││
│  └──────────────┴───────┴─────────┴─────────┴────────────┴────────────────────┘│
│                                                                                  │
│  💰 Total Buy Amount: 91,458 SEK  (Available Cash: 65,200 SEK) ⚠️ NEED TO SELL!│
│                                                                                  │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                  │
│  🔴 SELL SIGNALS (2 stocks) ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━│
│                                                                                  │
│  ┌──────────────┬───────┬─────────┬─────────┬────────────┬────────────────────┐│
│  │ Ticker       │ Score │ Value   │ Shares  │ Proceeds   │ Reason             ││
│  ├──────────────┼───────┼─────────┼─────────┼────────────┼────────────────────┤│
│  │ NIBE-B.ST    │   85  │ 51.80   │   280   │  14,504 ₭  │ Score < 90         ││
│  │ ⚠️ PRIORITY  │       │         │         │            │ Falling trend      ││
│  ├──────────────┼───────┼─────────┼─────────┼────────────┼────────────────────┤│
│  │ ALFA.ST      │   88  │ 351.20  │   145   │  50,924 ₭  │ Score dropped      ││
│  │              │       │         │         │            │ Out of top 70      ││
│  └──────────────┴───────┴─────────┴─────────┴────────────┴────────────────────┘│
│                                                                                  │
│  💵 Total Sell Proceeds: 65,428 SEK  →  Enough for all 3 buys! ✅               │
│                                                                                  │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                  │
│  📊 TRADE SUMMARY & IMPACT                                                      │
│                                                                                  │
│  Current Portfolio:  17 stocks  →  18 stocks (after trades)                    │
│  Net Cash Flow:      -26,030 SEK                                               │
│  New Cash Balance:   39,170 SEK (after trades)                                │
│  Portfolio Value:    ~325,450 SEK  →  ~332,735 SEK (estimated)                │
│                                                                                  │
│  Expected Changes:                                                              │
│  ✅ Average Score:    112.5  →  114.2  (+1.7 improvement)                      │
│  ✅ Top 70 Coverage:  94%    →  100%  (all holdings in top 70)                 │
│  ⚠️  Concentration:   Top 5 = 28.5%  →  29.2%  (within limits)                 │
│                                                                                  │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                  │
│  ✓ EXECUTION CHECKLIST                                                         │
│                                                                                  │
│  Sunday 20:00 - Execute on Avanza:                                             │
│  ☐ 1. SELL NIBE-B.ST   (280 shares @ market) Priority!                        │
│  ☐ 2. SELL ALFA.ST     (145 shares @ market)                                  │
│  ☐ 3. BUY SKF-B.ST     (180 shares @ limit 196.00)                            │
│  ☐ 4. BUY INVE-B.ST    (120 shares @ limit 246.50)                            │
│  ☐ 5. BUY HM-B.ST      (165 shares @ limit 163.50)                            │
│                                                                                  │
│  Sunday 20:30 - After execution:                                               │
│  ☐ 6. Update config/active_portfolio.csv with actual fills                     │
│  ☐ 7. Check Sheet 2 (Current Holdings) for accuracy                            │
│  ☐ 8. Mark this sheet as "✅ EXECUTED - 2026-02-16"                            │
│                                                                                  │
│  💡 TIP: Use limit orders 0.5-1% above/below market to ensure fills            │
│                                                                                  │
└─────────────────────────────────────────────────────────────────────────────────┘
```

### Design Specs

**Header (A1:H2)**
- Font: Roboto Bold 16pt
- Background: Lightning bolt pattern
- Urgency: This is the ACTION sheet
- Date prominent

**BUY Section (A4:H20)**
- Background: Light green (#E8F5E9)
- Border: 3px green (#00C853)
- Table: Clean, bold headers
- Top pick highlighted with 🎯

**SELL Section (A22:H35)**
- Background: Light red (#FFEBEE)
- Border: 3px red (#D32F2F)
- Priority items marked with ⚠️

**Cash Flow Warning (A21)**
- If buy amount > cash: Red background
- Shows you MUST sell first
- Large bold text

**Impact Summary (A37:H48)**
- White background, gray border
- Before → After arrows
- Green ✅ for improvements
- Yellow ⚠️ for cautions

**Execution Checklist (A50:H65)**
- Large checkboxes ☐
- Numbered steps
- Specific prices and shares
- Color code: Sells in red, buys in green

### Smart Features

**Auto-Generated Limit Prices**
```
Buy Limit = Current Price × 1.005    # 0.5% above market
Sell Limit = Current Price × 0.995   # 0.5% below market (market order)
```

**Progress Tracking**
- Each week gets marked "✅ EXECUTED - [DATE]"
- Archive old weeks to "Trade History" tab
- Easy to see execution rate

**Risk Checks**
- Warns if buying more than cash available
- Flags if portfolio goes >20 stocks
- Alerts if any position >6% weight

---

## 📈 Sheet 5: Performance Tracking - EQUITY CURVE

**Purpose:** Am I beating the benchmark? What's my Sharpe ratio?

### Layout (A1:L200)

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│  PERFORMANCE TRACKING - Historical Equity Curve                                 │
│  ════════════════════════════════════════════════════════════════════════════   │
│                                                                                  │
│  📈 EQUITY CURVE (Since Inception) ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━│
│                                                                                  │
│  340K ┤                                                              ╭────      │
│  320K ┤                                                      ╭──────╯           │
│  300K ┤                                              ╭──────╯                   │
│  280K ┤                                      ╭──────╯                           │
│  260K ┤                              ╭──────╯                                   │
│  240K ┤                      ╭──────╯         ┈┈┈┈┈┈┈┈┈ OMXS30                 │
│  220K ┤              ╭──────╯        ╱                                          │
│  200K ┤      ╭──────╯         ╱                                                 │
│  180K ┤ ╭───╯         ╱                                                         │
│  160K ┤╱      ╱                                                                 │
│  140K ┼──────────────────────────────────────────────────────────────────────  │
│   Jan  Feb  Mar  Apr  May  Jun  Jul  Aug  Sep  Oct  Nov  Dec  Jan  Feb        │
│        2025                                                      2026            │
│                                                                                  │
│  ─────  Your Portfolio (28.06% CAGR)    ┈┈┈┈  OMXS30 Benchmark (8.83% CAGR)   │
│                                                                                  │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                  │
│  📊 KEY METRICS                          📉 RISK ANALYSIS                       │
│                                                                                  │
│  Time Period:    12.5 months             Sharpe Ratio:     2.15  🏆            │
│  Total Return:   +125,450 SEK (+62.7%)   Max Drawdown:    -27.90%             │
│  CAGR:           28.06%                   Current Drawdown: -0.0%              │
│  vs OMXS30:      +20.23% alpha           Volatility:        18.5%              │
│  Win Weeks:      34 / 52 (65%)           Sortino Ratio:     3.21               │
│  Best Week:      +8.2% (Mar 12)          Calmar Ratio:      1.01               │
│  Worst Week:     -12.3% (Oct 8)          95% VaR:          -3.2%               │
│                                                                                  │
└─────────────────────────────────────────────────────────────────────────────────┘

WEEKLY PERFORMANCE LOG
┌──────┬──────────────┬─────────────┬─────────────┬─────────────┬────────┬────────┐
│ Week │ Date         │ Value       │ Cash        │ Invested    │ Return │ OMXS30 │
├──────┼──────────────┼─────────────┼─────────────┼─────────────┼────────┼────────┤
│  52  │ 2026-02-16   │  325,450    │   65,200    │  260,250    │ +2.29% │ +1.5%  │
│  51  │ 2026-02-09   │  318,165    │   62,400    │  255,765    │ +1.82% │ +1.2%  │
│  50  │ 2026-02-02   │  312,485    │   58,200    │  254,285    │ -0.45% │ -0.8%  │
│  ... │              │             │             │             │        │        │
│   2  │ 2025-01-12   │  103,250    │   25,800    │   77,450    │ +3.25% │ +2.1%  │
│   1  │ 2025-01-05   │  100,000    │  100,000    │       0     │  0.00% │  0.0%  │
└──────┴──────────────┴─────────────┴─────────────┴─────────────┴────────┴────────┘

MONTHLY SUMMARY (Rolling 12 Months)
┌────────────┬──────────────┬─────────────┬────────────┬──────────────────────────┐
│ Month      │ Start Value  │ End Value   │ Return %   │ vs OMXS30                │
├────────────┼──────────────┼─────────────┼────────────┼──────────────────────────┤
│ Feb 2026   │  312,485     │  325,450    │   +4.15%   │  +2.65%  🟢 Outperformed │
│ Jan 2026   │  298,600     │  312,485    │   +4.65%   │  +3.15%  🟢 Outperformed │
│ Dec 2025   │  285,200     │  298,600    │   +4.70%   │  +2.20%  🟢 Outperformed │
│ Nov 2025   │  272,100     │  285,200    │   +4.81%   │  +1.31%  🟢 Outperformed │
│ Oct 2025   │  245,300     │  272,100    │  +10.93%   │  +2.43%  🟢 Outperformed │
│ Sep 2025   │  251,800     │  245,300    │   -2.58%   │  -1.08%  🔴 Underperform │
│ Aug 2025   │  242,150     │  251,800    │   +3.98%   │  +1.48%  🟢 Outperformed │
│ ...        │              │             │            │                          │
└────────────┴──────────────┴─────────────┴────────────┴──────────────────────────┘

QUARTERLY BREAKDOWN
┌───────────┬──────────────┬────────────┬──────────────┬────────────────┐
│ Quarter   │ Return %     │ OMXS30 %   │ Alpha        │ Sharpe         │
├───────────┼──────────────┼────────────┼──────────────┼────────────────┤
│ Q4 2025   │   +15.8%     │   +6.2%    │   +9.6%      │  2.35          │
│ Q3 2025   │   +12.4%     │   +4.8%    │   +7.6%      │  1.98          │
│ Q2 2025   │   +18.2%     │   +7.1%    │  +11.1%      │  2.42          │
│ Q1 2025   │   +16.3%     │   +5.9%    │  +10.4%      │  2.18          │
└───────────┴──────────────┴────────────┴──────────────┴────────────────┘
```

### Design Specs

**Equity Curve Chart (A3:L20)**
- Dual-axis line chart
- Your portfolio: Thick blue line (#1976D2), 4px
- OMXS30: Dotted gray line, 2px
- Area fill under portfolio line (20% opacity)
- Grid: Light gray, subtle
- X-axis: Monthly labels
- Y-axis: 20K intervals, SEK format
- Legend: Bottom right

**Metrics Dashboard (A22:L30)**
- Two columns: Performance | Risk
- Green/red color coding for good/bad
- Trophy 🏆 for exceptional metrics (Sharpe >2.0)
- Large bold numbers (16pt)
- Small gray labels (10pt)

**Weekly Log Table (A32:G100)**
- Reverse chronological (newest first)
- Freeze header row
- Alternating row colors
- Conditional formatting on Return %:
  ```
  >2%: Green background
  0-2%: Light green
  -2-0%: Light red
  <-2%: Red background
  ```
- OMXS30 column for comparison

**Monthly Summary (A102:E115)**
- Last 12 months only
- 🟢/🔴 icons for outperform/underperform
- Bold for current month
- Totals row at bottom

**Quarterly Breakdown (A117:E122)**
- Rolled up from weekly data
- Larger view for trends
- Sharpe per quarter to see consistency

### Charts & Visualizations

**Drawdown Chart** (below equity curve)
```
  0% ─────────────────────────────────────────────────────────────────────────
-5%  ╲                    ╱
-10%  ╲                  ╱
-15%   ╲                ╱
-20%    ╲              ╱
-25%     ╲            ╱
-30%      ╲__________╱
```

**Monthly Returns Heat Map**
```
        Jan   Feb   Mar   Apr   May   Jun   Jul   Aug   Sep   Oct   Nov   Dec
2025    🟢    🟢    🟢    🟢    🟡    🟢    🟢    🟢    🔴    🟢    🟢    🟢
2026    🟢    🟢
```

---

## 💰 Sheet 6: Dividend Tracker - PASSIVE INCOME

**Purpose:** When am I getting paid? How much dividend income YTD?

### Layout (A1:J50)

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│  💰 DIVIDEND TRACKER - Passive Income Stream                                    │
│  Track upcoming dividends and annual yield                                      │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                  │
│  📊 DIVIDEND SUMMARY (YTD 2026)                                                 │
│                                                                                  │
│  ┌─────────────────────────┬──────────────────────────┬──────────────────────┐ │
│  │ Total Received YTD      │ Expected Next Quarter    │ Annual Yield         │ │
│  │ 4,230 SEK               │ 2,850 SEK                │ 1.3%                 │ │
│  └─────────────────────────┴──────────────────────────┴──────────────────────┘ │
│                                                                                  │
│  ┌────────────────────────────────────────────────────────────────────────────┐ │
│  │                        DIVIDEND CALENDAR 2026                              │ │
│  │                                                                            │ │
│  │  Q1     ██████ 6,200 SEK  (Mar dividends paid)                            │ │
│  │  Q2     ████── 2,850 SEK  (Expected: Apr-Jun)                             │ │
│  │  Q3     ────── 0 SEK      (Expected: Jul-Sep)                             │ │
│  │  Q4     ────── 0 SEK      (Expected: Oct-Dec)                             │ │
│  │                                                                            │ │
│  │  Projected Annual: 9,050 SEK  (~2.8% yield)                               │ │
│  └────────────────────────────────────────────────────────────────────────────┘ │
│                                                                                  │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                  │
│  📅 UPCOMING DIVIDENDS (Next 90 Days)                                           │
│                                                                                  │
│  ┌────────────┬──────────────┬──────────┬───────────┬──────────┬─────────────┐ │
│  │ Ticker     │ Company      │ Ex-Date  │ Pay Date  │ Per Share│ You Get     │ │
│  ├────────────┼──────────────┼──────────┼───────────┼──────────┼─────────────┤ │
│  │ VOLV-B.ST  │ Volvo B      │ Mar 20   │ Mar 28    │ 5.50 ₭   │ 1,375 ₭ ✅  │ │
│  │ ASSA-B.ST  │ Assa Abloy   │ Apr 5    │ Apr 12    │ 4.20 ₭   │   756 ₭ ⏳  │ │
│  │ SAND.ST    │ Sandvik      │ Apr 18   │ Apr 25    │ 3.80 ₭   │   798 ₭ ⏳  │ │
│  │ SEB-A.ST   │ SEB A        │ May 2    │ May 9     │ 7.50 ₭   │ 1,050 ₭ ⏳  │ │
│  │ SWED-A.ST  │ Swedbank A   │ May 15   │ May 22    │ 8.20 ₭   │ 1,148 ₭ ⏳  │ │
│  └────────────┴──────────────┴──────────┴───────────┴──────────┴─────────────┘ │
│                                                                                  │
│  💡 Total Expected (Next 90 Days): 5,127 SEK                                    │
│                                                                                  │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                  │
│  📜 DIVIDEND HISTORY (Last 12 Months)                                           │
│                                                                                  │
│  ┌────────────┬──────────────┬──────────┬───────────┬──────────┬─────────────┐ │
│  │ Date       │ Ticker       │ Shares   │ Per Share │ Received │ Status      │ │
│  ├────────────┼──────────────┼──────────┼───────────┼──────────┼─────────────┤ │
│  │ 2026-03-28 │ VOLV-B.ST    │   250    │   5.50 ₭  │ 1,375 ₭  │ ✅ Received │ │
│  │ 2026-03-15 │ ATCO-A.ST    │   320    │   4.80 ₭  │ 1,536 ₭  │ ✅ Received │ │
│  │ 2026-02-28 │ SSAB-A.ST    │   380    │   2.30 ₭  │   874 ₭  │ ✅ Received │ │
│  │ 2025-12-20 │ ASSA-B.ST    │   180    │   4.20 ₭  │   756 ₭  │ ✅ Received │ │
│  │ 2025-11-30 │ SAND.ST      │   210    │   3.80 ₭  │   798 ₭  │ ✅ Received │ │
│  │ ...        │              │          │           │          │             │ │
│  └────────────┴──────────────┴──────────┴───────────┴──────────┴─────────────┘ │
│                                                                                  │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                  │
│  🏆 TOP DIVIDEND PAYERS (Current Holdings)                                      │
│                                                                                  │
│  ┌────────────┬──────────────┬──────────────┬──────────────┬────────────────┐  │
│  │ Ticker     │ Company      │ Annual Div   │ Yield        │ YTD Received   │  │
│  ├────────────┼──────────────┼──────────────┼──────────────┼────────────────┤  │
│  │ SWED-A.ST  │ Swedbank A   │  16.40 ₭     │  7.9%  🏆    │  2,296 ₭       │  │
│  │ SEB-A.ST   │ SEB A        │  15.00 ₭     │  5.3%        │  2,100 ₭       │  │
│  │ VOLV-B.ST  │ Volvo B      │  11.00 ₭     │  4.1%        │  2,750 ₭       │  │
│  │ ASSA-B.ST  │ Assa Abloy   │   8.40 ₭     │  2.6%        │  1,512 ₭       │  │
│  │ SAND.ST    │ Sandvik      │   7.60 ₭     │  3.3%        │  1,596 ₭       │  │
│  └────────────┴──────────────┴──────────────┴──────────────┴────────────────┘  │
│                                                                                  │
│  💡 Focus on dividend aristocrats for steady income stream!                     │
│                                                                                  │
└─────────────────────────────────────────────────────────────────────────────────┘
```

### Design Specs

**Summary Cards (A3:J10)**
- 3 large metric cards
- Numbers: 20pt bold
- Icons: 💰📊🏆
- Green for positive growth

**Calendar Chart (A12:J20)**
- Horizontal bar chart
- Quarters on Y-axis
- Green bars for received, gray for expected
- Projected annual in bold at bottom

**Upcoming Table (A22:J32)**
- Sorted by ex-date (nearest first)
- Status icons: ✅ (confirmed) ⏳ (pending)
- Dates in bold
- Highlight rows within 30 days (yellow)

**History Table (A34:J48)**
- Reverse chronological
- ✅ for all received dividends
- Running total at bottom
- Link to tax sheet for ISK impact

**Top Payers (A50:J58)**
- Sorted by yield (high to low)
- 🏆 for yields >7%
- Shows both per-share and total received
- Helps identify best dividend stocks

### Auto-Calculations

```
Annual Yield = (Total Dividends YTD / Average Portfolio Value) × (365 / Days Elapsed)
Projected Annual = (Dividends YTD / Days Elapsed) × 365
Expected Next 90 = SUM(upcoming dividends with ex-date < today+90)
```

---

## 🧮 Sheet 7: ISK Tax Calculator - SIMPLE TAX

**Purpose:** How much tax will I pay? ISK vs regular account comparison.

### Layout (A1:H40)

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│  🧮 ISK TAX CALCULATOR - Swedish Investment Savings Account                     │
│  Simple, predictable tax on portfolio value (not gains!)                        │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                  │
│  📋 ISK TAX BASICS (2026)                                                       │
│                                                                                  │
│  Tax Rate:        1.065% per year (on portfolio value)                         │
│  Tax Basis:       Portfolio value × government interest rate (4.26% for 2026)  │
│  Calculation:     Portfolio Value × 0.04 26 × 0.30 (tax rate) = 1.065% × Value│
│  Payment:         Automatic quarterly deduction by your broker                  │
│  Capital Gains:   TAX FREE! ✅                                                  │
│  Dividends:       TAX FREE! ✅                                                  │
│  Trading:         TAX FREE! ✅ Perfect for active strategies                    │
│                                                                                  │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                  │
│  💰 YOUR ISK TAX (2026 YTD)                                                     │
│                                                                                  │
│  ┌───────────────────────┬──────────────────────┬──────────────────────────┐   │
│  │ Current Portfolio     │ Annual Tax           │ Effective Rate           │   │
│  │ 325,450 SEK           │ 3,466 SEK            │ 1.065%                   │   │
│  └───────────────────────┴──────────────────────┴──────────────────────────┘   │
│                                                                                  │
│  Quarterly Breakdown (Automatic Deductions):                                    │
│  ├─ Q1 2026:  867 SEK   ✅ Paid (Jan-Mar)                                       │
│  ├─ Q2 2026:  867 SEK   ⏳ Due April 30                                         │
│  ├─ Q3 2026:  867 SEK   ⏳ Due July 31                                          │
│  └─ Q4 2026:  865 SEK   ⏳ Due Oct 31                                           │
│                                                                                  │
│  Monthly Impact: ~289 SEK  (automatic deduction from cash)                      │
│                                                                                  │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                  │
│  📊 ISK vs REGULAR ACCOUNT (2026 Comparison)                                    │
│                                                                                  │
│  Scenario: 28% CAGR Strategy with High Turnover (Weekly Trading)               │
│                                                                                  │
│  ┌─────────────────────────┬──────────────────┬──────────────────────────────┐ │
│  │ Metric                  │ ISK Account      │ Regular Account              │ │
│  ├─────────────────────────┼──────────────────┼──────────────────────────────┤ │
│  │ Starting Capital        │  100,000 SEK     │  100,000 SEK                 │ │
│  │ Annual Return (Gross)   │   28,000 SEK     │   28,000 SEK                 │ │
│  │                         │                  │                              │ │
│  │ Capital Gains Tax       │   0 SEK ✅       │   8,400 SEK  (30% of gains)  │ │
│  │ Dividend Tax            │   0 SEK ✅       │     390 SEK  (30% of divs)   │ │
│  │ ISK Tax                 │  1,065 SEK       │   0 SEK                      │ │
│  │                         │                  │                              │ │
│  │ Total Tax Paid          │  1,065 SEK       │   8,790 SEK                  │ │
│  │ Net After Tax           │ 26,935 SEK       │  19,210 SEK                  │ │
│  │                         │                  │                              │ │
│  │ Effective Tax Rate      │  3.8% 🟢        │  31.4% 🔴                    │ │
│  │ Tax Savings             │  7,725 SEK       │  -                           │ │
│  └─────────────────────────┴──────────────────┴──────────────────────────────┘ │
│                                                                                  │
│  🏆 ISK SAVES YOU 7,725 SEK PER YEAR! (on 100K portfolio with 28% returns)     │
│                                                                                  │
│  At 325K portfolio: ~25,000 SEK tax savings per year! 🚀                        │
│                                                                                  │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                  │
│  ✅ WHY ISK IS PERFECT FOR KAVASTU STRATEGY                                    │
│                                                                                  │
│  │ Weekly Trading           │ No tax on frequent trades ✅                      │
│  │ High Turnover            │ Regular account would be taxed 30% on every sale │
│  │ Momentum Strategy        │ Compound returns without drag from cap gains tax │
│  │ Dividend Reinvestment    │ Dividends reinvest tax-free ✅                    │
│  │ Simple Reporting         │ One annual tax line, no trade tracking needed    │
│  │ Predictable Costs        │ Always 1.065% - easy to budget                   │
│                                                                                  │
│  💡 With ISK, more of your returns stay invested and compound!                  │
│                                                                                  │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                  │
│  📈 TAX IMPACT ON LONG-TERM WEALTH                                              │
│                                                                                  │
│  Starting: 100,000 SEK  |  28% Annual Returns  |  10 Years                     │
│                                                                                  │
│  ISK Account:                                                                   │
│  Year 1:   128,000 SEK - 1,065 SEK tax = 126,935 SEK                           │
│  Year 5:   389,450 SEK - 4,148 SEK tax = 385,302 SEK                           │
│  Year 10: 1,152,850 SEK -12,288 SEK tax = 1,140,562 SEK ✅                     │
│                                                                                  │
│  Regular Account:                                                               │
│  Year 1:   119,600 SEK  (30% tax on 28K gain)                                  │
│  Year 5:   285,420 SEK  (tax drag compounds)                                   │
│  Year 10:  673,850 SEK  (massive tax drag) 🔴                                  │
│                                                                                  │
│  🏆 ISK ADVANTAGE AFTER 10 YEARS: +466,712 SEK! (+69% more wealth!)            │
│                                                                                  │
└─────────────────────────────────────────────────────────────────────────────────┘
```

### Design Specs

**Info Section (A3:H12)**
- Clean bullet points
- Green ✅ for tax-free benefits
- Yellow highlight for key numbers
- Font: Roboto 11pt

**Tax Summary Cards (A14:H22)**
- Large bold numbers (18pt)
- Current quarter highlighted
- ✅ for paid, ⏳ for pending
- Green borders for cards

**Comparison Table (A24:H36)**
- Side-by-side: ISK | Regular
- Green cells for ISK advantages
- Red cells for Regular disadvantages
- Trophy 🏆 for savings amount

**Long-Term Projection (A38:H50)**
- 10-year comparison
- Shows compounding effect
- Massive difference highlighted
- Motivational (stay in ISK!)

### Auto-Calculations

```
Annual ISK Tax = Portfolio Value × 0.01065
Quarterly Tax = Annual Tax / 4
Monthly Impact = Annual Tax / 12
Regular Account Tax = (Capital Gains × 0.30) + (Dividends × 0.30)
Tax Savings = Regular Tax - ISK Tax
```

---

## 🎨 Global Design System

### Color Palette

**Primary Colors**
```css
--primary-blue:    #1976D2  /* Headers, charts, info */
--success-green:   #00C853  /* Buy signals, gains */
--warning-yellow:  #FFC107  /* Hold signals, caution */
--danger-red:      #D32F2F  /* Sell signals, losses */
--neutral-gray:    #757575  /* Inactive, text */
```

**Backgrounds**
```css
--bg-white:        #FFFFFF
--bg-light-gray:   #F5F5F5  /* Alternating rows */
--bg-light-green:  #E8F5E9  /* Buy zones, positive */
--bg-light-red:    #FFEBEE  /* Sell zones, negative */
--bg-light-yellow: #FFF9C4  /* Warnings, hold */
--bg-dark-gray:    #424242  /* Headers */
```

**Signals (Consistent Across All Sheets)**
```
🟢 Score ≥ 110  (BUY)    → Green background #C8E6C9
🟡 Score 90-109 (HOLD)   → Yellow background #FFF9C4
🔴 Score < 90   (SELL)   → Red background #FFCDD2
```

### Typography

**Font Family:** Roboto (Google Fonts, clean and professional)

**Font Sizes:**
- Headers: 18pt Bold
- Subheaders: 14pt Bold
- Section Titles: 12pt Bold
- Body Text: 11pt Regular
- Small Text: 10pt Regular
- Large Numbers: 20-24pt Bold

**Number Formatting:**
```
Currency:    "0 SEK" or "0,000 SEK"
Percentage:  "+0.00%" (always show sign)
Shares:      "#,##0" (integer, thousands separator)
Score:       "0" (integer, no decimals)
Dates:       "MMM DD" or "YYYY-MM-DD"
```

### Icons & Emojis

**Consistent Use:**
- 🟢 Buy / Strong / Positive
- 🟡 Hold / Caution / Neutral
- 🔴 Sell / Weak / Negative
- ✅ Completed / Confirmed / Success
- ⏳ Pending / In Progress
- ⚠️ Warning / Attention Needed
- 🏆 Exceptional / Top Performer
- 💰 Money / Dividends / Cash
- 📊 Charts / Data / Analysis
- 🎯 Target / Goal / Focus
- ⚡ Action / Urgent / Priority

### Responsive Design

**Column Widths (Standard)**
```
A (Rank/Date):     80px
B (Ticker):        120px
C (Name):          150-180px
D (Score/Numbers): 80px
E-H (Data):        100-120px each
I-J (Additional):  100px each
```

**Mobile Optimization**
- Minimum font: 11pt (readable on phone)
- No horizontal scroll (max 8-10 columns visible)
- Large touch targets (40px min)
- Freeze first row + first column
- Hide less important columns on small screens

---

## 📱 Mobile Experience (iPad/iPhone)

### Sheet 1: Portfolio Overview
- **Perfect for quick glance**
- Big numbers readable from couch
- Equity curve chart auto-scales
- Checklist has large tap targets

### Sheet 4: Trade Recommendations
- **Copy signals to Avanza app**
- Large checkboxes for tapping
- Clear buy/sell sections
- One-handed operation

### Sheet 2: Current Holdings
- Swipe to see all columns
- Sorted by size (biggest first)
- Signal column always visible
- Quick P&L check

### Sheets 3, 5, 6, 7
- Desktop-first (detailed analysis)
- Still readable on tablet
- Landscape mode recommended

---

## 🎯 Key Success Metrics

### Dashboard Effectiveness

**Speed Metrics:**
- 0-30s: Quick status check (Sheet 1)
- 30s-2min: Understand trade signals (Sheet 4)
- 2-5min: Deep analysis if needed (Sheets 2, 3)
- 5-10min: Review performance (Sheet 5)

**Usability:**
- Zero horizontal scrolling (mobile)
- All actions within 2 clicks
- Color coding immediately visible
- No need to calculate anything manually

**Decision Quality:**
- Trade recommendations have 95%+ execution rate
- No missed buy signals from confusion
- Clear risk indicators prevent overtrading
- Historical tracking builds confidence

### Design Philosophy Summary

> "Show me what to do, why to do it, and how it's working - in 30 seconds or less."

Every element serves this goal.

---

**Next Step:** Create the actual dashboard! Run `setup_dashboard.py` to bring this design to life. 🚀
