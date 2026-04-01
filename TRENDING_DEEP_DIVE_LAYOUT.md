# Trending Deep Dive Sheet - Visual Layout Reference

## Layer 2: iPad Landscape View

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    TRENDING STOCKS DEEP DIVE                                │
│                   (Blue header - RGB 0.3, 0.5, 0.9)                         │
├─────────────────────────────────────────────────────────────────────────────┤
│ Last Updated: 2026-02-14 12:45                                              │
│                                                                             │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│ 🔥 HOT STOCKS - DETAILED ANALYSIS (Top 10)                                 │
│ (Orange header - RGB 1.0, 0.85, 0.7)                                        │
│                                                                             │
│ ┌───────────────────────────────────────────────────────────────────────┐   │
│ │ 1. CTM.ST - Castellum                          Score: 100/100         │   │
│ │    (Gray background)                      (Orange badge: RGB 1.0,0.9,0.7)│   │
│ ├───────────────────────────────────────────────────────────────────────┤   │
│ │   Kavastu Score: 125/130 | Price: 265.50 SEK                         │   │
│ │   (10pt font)                                                         │   │
│ ├───────────────────────────────────────────────────────────────────────┤   │
│ │   4-week return +36.0%, outperforming OMXS30 by 36.0%, volume up 66% │   │
│ │   (10pt italic)                                                       │   │
│ ├───────────────────────────────────────────────────────────────────────┤   │
│ │   📰 Latest News:                                                     │   │
│ │     🟢 Castellum reports strong Q4 earnings...                        │   │
│ │     🟢 Analyst upgrade to "Strong Buy"...                             │   │
│ │     🟡 Commercial real estate outlook improving...                    │   │
│ │   (9pt font)                                                          │   │
│ ├───────────────────────────────────────────────────────────────────────┤   │
│ │   💡 Should You Buy?                                                  │   │
│ │   (Light yellow background - RGB 1.0, 1.0, 0.9)                       │   │
│ │     ✅ YES - Strong momentum, high Kavastu score (125)               │   │
│ │     ⚠️  Monitor: Already up 36.0%, watch for pullback                │   │
│ └───────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│ ┌───────────────────────────────────────────────────────────────────────┐   │
│ │ 2. TEL2-B.ST - Tele2 B                         Score: 95/100          │   │
│ ├───────────────────────────────────────────────────────────────────────┤   │
│ │   Kavastu Score: 118/130 | Price: 145.20 SEK                         │   │
│ ├───────────────────────────────────────────────────────────────────────┤   │
│ │   4-week return +18.6%, outperforming OMXS30 by 18.6%, volume up 41% │   │
│ ├───────────────────────────────────────────────────────────────────────┤   │
│ │   📰 Latest News:                                                     │   │
│ │     🟢 Tele2 beats Q4 estimates...                                    │   │
│ │     🟡 Nordic telecom sector update...                                │   │
│ │     🟢 Strong subscriber growth reported...                           │   │
│ ├───────────────────────────────────────────────────────────────────────┤   │
│ │   💡 Should You Buy?                                                  │   │
│ │     ✅ YES - Strong momentum, high Kavastu score (118)               │   │
│ │     🎯 Entry: Good entry point at current levels                      │   │
│ └───────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│ [... 8 more hot stocks ...]                                                │
│                                                                             │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│ ❄️  COLD STOCKS - DETAILED ANALYSIS (Top 5)                                │
│ (Light blue header - RGB 0.8, 0.9, 1.0)                                    │
│                                                                             │
│ ┌───────────────────────────────────────────────────────────────────────┐   │
│ │ 1. BOUL.ST - Boliden                            Score: 0/100          │   │
│ │    (Gray background)                      (Blue badge: RGB 0.8,0.9,1.0)│   │
│ ├───────────────────────────────────────────────────────────────────────┤   │
│ │   Kavastu Score: 85/130 | Price: 295.00 SEK                          │   │
│ ├───────────────────────────────────────────────────────────────────────┤   │
│ │   4-week return -15.8%, underperforming by 15.8%, volume down 10%    │   │
│ ├───────────────────────────────────────────────────────────────────────┤   │
│ │   📰 Latest News:                                                     │   │
│ │     🔴 Copper prices under pressure...                                │   │
│ │     🟡 Company maintains guidance...                                  │   │
│ ├───────────────────────────────────────────────────────────────────────┤   │
│ │   💡 Should You Sell (if owned)?                                      │   │
│ │   (Light red background - RGB 1.0, 0.95, 0.95)                        │   │
│ │     ⚠️  WATCH - Cold trend, marginal score (85)                      │   │
│ │     🎯 Action: Monitor closely, sell if score drops below 90          │   │
│ └───────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│ [... 4 more cold stocks ...]                                               │
│                                                                             │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│ 📝 Note: This is Layer 2 detailed analysis. For quick Sunday trading,      │
│         use Executive Summary (Layer 1).                                   │
│ (Light blue background - RGB 0.95, 0.95, 1.0)                              │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Buy Recommendation Logic (Hot Stocks)

### ✅ YES - Strong Buy
**Conditions:**
- Trending score ≥ 75
- Kavastu score ≥ 110

**Message:**
- If 4-week return > 30%: "Monitor: Already up X%, watch for pullback"
- Otherwise: "Entry: Good entry point at current levels"

**Example:**
```
💡 Should You Buy?
  ✅ YES - Strong momentum, high Kavastu score (125)
  ⚠️  Monitor: Already up 36.0%, watch for pullback
```

### ⚠️ MAYBE - Conditional Buy
**Conditions:**
- Trending score ≥ 75
- Kavastu score < 110

**Message:**
- "Wait: Monitor for Kavastu score to improve above 110"

**Example:**
```
💡 Should You Buy?
  ⚠️  MAYBE - Strong trending but lower score (105)
  🎯 Wait: Monitor for Kavastu score to improve above 110
```

### ℹ️ WATCH - Not Priority
**Conditions:**
- Trending score < 75

**Message:**
- "Better opportunities exist in higher-scored stocks"

**Example:**
```
💡 Should You Buy?
  ℹ️  WATCH - Moderate momentum, not top priority
  🎯 Better opportunities exist in higher-scored stocks
```

## Sell Recommendation Logic (Cold Stocks)

### ❌ YES - Sell Now
**Conditions:**
- Kavastu score < 90

**Message:**
- "Action: Sell on next trading day"

**Example:**
```
💡 Should You Sell (if owned)?
  ❌ YES - Below 90 threshold (current: 85)
  🎯 Action: Sell on next trading day
```

### ⚠️ WATCH - Monitor Closely
**Conditions:**
- Trending score ≤ 25
- Kavastu score 90-100

**Message:**
- "Action: Monitor closely, sell if score drops below 90"

**Example:**
```
💡 Should You Sell (if owned)?
  ⚠️  WATCH - Cold trend, marginal score (95)
  🎯 Action: Monitor closely, sell if score drops below 90
```

### ℹ️ HOLD - Keep for Now
**Conditions:**
- Kavastu score ≥ 100
- (Even if trending cold)

**Message:**
- "Action: Keep for now, watch for improvement"

**Example:**
```
💡 Should You Sell (if owned)?
  ℹ️  HOLD - Weak trend but acceptable score (102)
  🎯 Action: Keep for now, watch for improvement
```

## Color Reference

### Backgrounds
```python
# Header
header_blue = {'red': 0.3, 'green': 0.5, 'blue': 0.9}

# Section Headers
hot_orange = {'red': 1.0, 'green': 0.85, 'blue': 0.7}
cold_blue = {'red': 0.8, 'green': 0.9, 'blue': 1.0}

# Stock Rows
light_gray = {'red': 0.95, 'green': 0.95, 'blue': 0.95}

# Score Badges
hot_badge = {'red': 1.0, 'green': 0.9, 'blue': 0.7}
cold_badge = {'red': 0.8, 'green': 0.9, 'blue': 1.0}

# Recommendations
buy_rec = {'red': 1.0, 'green': 1.0, 'blue': 0.9}  # Light yellow
sell_rec = {'red': 1.0, 'green': 0.95, 'blue': 0.95}  # Light red

# Footer
footer_blue = {'red': 0.95, 'green': 0.95, 'blue': 1.0}
```

### Text
```python
# Header Text
header_text = {'red': 1, 'green': 1, 'blue': 1}  # White

# All other text: Default black
```

## Font Sizes

```python
# Main header
header_size = 16  # Bold, white text

# Section headers (Hot/Cold)
section_header_size = 14  # Bold

# Stock names
stock_name_size = 12  # Bold

# Score badges
score_badge_size = 11  # Bold

# Metrics and recommendations
content_size = 10  # Regular or bold for headers

# News articles
news_size = 9  # Regular

# Footer note
footer_size = 9  # Italic
```

## News Sentiment Emojis

```python
'positive': '🟢'  # Green circle
'negative': '🔴'  # Red circle
'neutral': '🟡'   # Yellow circle
```

## Data Flow

```
update_dashboard.py
    ↓
extract_trending_stocks(screener_results)
    ↓
trending_data = {
    'hot_stocks': [...],   # Top 10 by trending_score
    'cold_stocks': [...]   # Bottom 10 by trending_score
}
    ↓
update_google_sheets()
    ↓
manager.update_trending_deep_dive(trending_data, screener_results)
    ↓
For each hot stock:
    - Fetch 3 news articles
    - Display metrics
    - Generate buy recommendation
    ↓
For each cold stock:
    - Fetch 2 news articles
    - Display metrics
    - Generate sell recommendation
    ↓
Google Sheet updated with formatted content
```

## iPad Landscape Optimization

### Screen Real Estate
- **Target resolution:** 2388 × 1668 (iPad Air/Pro 11")
- **Columns used:** A-H (8 columns)
- **Rows:** Dynamic (150-200 rows typical)

### Scrolling Behavior
- **Vertical scrolling:** Yes (main navigation)
- **Horizontal scrolling:** Minimal (wide enough for landscape)

### Reading Pattern
1. Header (quick timestamp check)
2. Scan hot stocks (look for ✅ YES recommendations)
3. Scan cold stocks (check owned positions)
4. Read news for stocks of interest
5. Make trading decisions

### Touch Targets
- All text is readable at arm's length
- No interactive elements (read-only sheet)
- Links would be added in future if needed

## Use Case Scenarios

### Scenario 1: Sunday Trading
**User:** Peter (every Sunday 19:00)
**Goal:** Execute weekly trades
**Sheet Used:** Executive Summary (Layer 1)
**Why:** Quick 2-minute glance, all trades visible at once

### Scenario 2: Market Crash
**User:** Peter (during sudden -5% OMXS30 drop)
**Goal:** Understand which holdings are falling hardest
**Sheet Used:** Trending Deep Dive (Layer 2)
**Flow:**
1. Open iPad in landscape
2. Navigate to Trending Deep Dive
3. Scroll to cold stocks section
4. Check if any owned stocks appear
5. Read news to understand why
6. Decide: Hold or sell based on recommendation

### Scenario 3: Research New Buy
**User:** Peter (mid-week research)
**Goal:** Deep dive into hot stock before buying
**Sheet Used:** Trending Deep Dive (Layer 2)
**Flow:**
1. Executive Summary shows CTM.ST as hot
2. Switch to Trending Deep Dive
3. Find CTM.ST detailed card
4. Read all 3 news articles
5. Check buy recommendation
6. Note: Already up 36%, wait for pullback

### Scenario 4: Portfolio Review
**User:** Peter (monthly)
**Goal:** Review all positions for weakness
**Sheet Used:** Both layers
**Flow:**
1. Layer 1: Check overall performance
2. Layer 2: Scan all cold stocks
3. Cross-reference with Current Holdings sheet
4. Identify positions at risk
5. Add to sell watchlist if score approaching 90

## Implementation Notes

### Row Management
- Each hot stock: ~12-15 rows (header + metrics + news + rec)
- Each cold stock: ~10-12 rows
- Total rows: ~200 (allows for 10 hot + 5 cold + spacing)

### Update Frequency
- Weekly (Sunday afternoon before market opens)
- Same schedule as Executive Summary
- Both layers updated together

### Performance
- Update time: ~30-45 seconds
- News fetching: Parallelizable but currently sequential
- Caching: 6-hour TTL reduces redundant fetches

### Error Handling
- No news available: Shows "No recent news"
- Missing stock data: Skipped from list
- API timeout: Cached data used if available
- Formatting errors: Logged but don't block update

## Future Enhancements (Not Implemented)

### Nice-to-Have
1. Click stock ticker → Open Avanza
2. Expandable news articles (full text)
3. Historical trending score chart
4. Sector heatmap
5. Volume profile charts

### Advanced Features
1. Real-time updates (not needed for weekly strategy)
2. Custom alerts (email when score drops)
3. Recommendation tracking (accuracy %)
4. Backtested returns per recommendation

---

**Note:** This is Layer 2 (deep dive). For quick Sunday trading, use Layer 1 (Executive Summary).
