"""
AI Summary Generator - Generate executive summaries and structured analysis
from MarketMate transcripts.

Uses Anthropic's Claude API to produce structured Swedish-language summaries
and extract regime classification, signals, and tickers in a single call.
"""
import json
import os
from typing import Dict, Optional

try:
    import anthropic
    HAS_ANTHROPIC = True
except ImportError:
    HAS_ANTHROPIC = False


SUMMARY_SYSTEM_PROMPT = """Du är en erfaren finansanalytiker som sammanfattar marknadsanalyser på svenska.
Givet ett transkript från en YouTube-video om börsen, skapa en koncis executive summary.

Strukturera sammanfattningen med dessa rubriker (använd markdown):

## Marknadsläge
Beskriv den övergripande marknadssituationen i 2-3 meningar.

## Teknisk analys
- Viktigaste tekniska signalerna (divergenser, stöd/motstånd, trender)
- Tidshorisont (daglig vs vecko)

## Aktier & Sektorer
- Nämn specifika aktier och deras signaler (köp/sälj/avvakta)
- Inkludera kursmål och stoploss om de nämns

## Handlingsplan
2-3 konkreta punkter om vad investeraren bör göra just nu.

Regler:
- Skriv på svenska
- Var koncis men informativ (max 300 ord)
- Fokusera på actionable insights
- Om transkriptet är otydligt, notera det"""


FULL_ANALYSIS_SYSTEM_PROMPT = """Du är en erfaren finansanalytiker. Analysera detta YouTube-transkript om börsen och returnera ett JSON-objekt med följande struktur:

{
  "regime": "ETT AV: BULL, BULL_WITH_SHORT_TERM_PULLBACK, NEUTRAL, BEAR",
  "summary": "1-2 meningar på svenska som sammanfattar marknadens aktuella läge och vad investeraren bör göra. Fokusera BARA på vad som är relevant just nu, inte historiska händelser.",
  "tickers_mentioned": ["SAND.ST", "ABB.ST"],
  "buy_signals": [{"ticker": "SAND.ST", "source": "MarketMate YouTube"}],
  "sell_signals": [{"ticker": "ERIC-B.ST", "source": "MarketMate YouTube", "type": "short"}],
  "targets": {"sp500_target": 6750},
  "executive_summary": "Full markdown-sammanfattning med ## Marknadsläge, ## Teknisk analys, ## Aktier & Sektorer, ## Handlingsplan"
}

REGLER FÖR REGIME:
- BULL: Stark upptrend, inga varningssignaler, köpläge
- BULL_WITH_SHORT_TERM_PULLBACK: Grundtrend uppåt men kortsiktig rekyl väntad
- NEUTRAL: Osäkert läge, sidledes marknad, motstridiga signaler
- BEAR: Nedtrend, säljsignaler dominerar, riskavvikelse

REGLER FÖR SUMMARY:
- Skriv på svenska
- Max 2 meningar
- Fokusera på NULÄGET, inte historiska händelser
- Om analytikern nämner säsongseffekter (sportlov, optionslösen etc), inkludera BARA om de är aktuella/kommande, inte om de redan passerat
- Inkludera S&P 500 target om det nämns

REGLER FÖR TICKERS:
Mappa svenska bolagsnamn till Yahoo Finance-tickers:
- Sandvik → SAND.ST, Volvo → VOLV-B.ST, ABB → ABB.ST
- Hexagon → HEXA-B.ST, SAAB → SAAB-B.ST
- Atlas Copco → ATCO-A.ST, Ericsson → ERIC-B.ST
- SEB → SEB-A.ST, Handelsbanken → SHB-A.ST, Swedbank → SWED-A.ST
- Evolution → EVO.ST, NIBE → NIBE-B.ST
- Investor → INVE-B.ST, Epiroc → EPI-A.ST
- MTG → MTG.ST, Telia → TELIA.ST, H&M → HM-B.ST
- Microsoft → MSFT, Oracle → ORCL, Nasdaq 100 → QQQ
- Danske Bank → DANSKE.CO, ISS → ISS.CO
- För andra svenska aktier, använd formatet TICKER.ST

REGLER FÖR BUY/SELL SIGNALS:
- Inkludera bara explicita köp/sälj-rekommendationer, inte bara omnämnanden
- "köper X" → buy_signal, "shortar X" / "säljer X" → sell_signal

REGLER FÖR TARGETS:
- Om S&P 500 target nämns → {"sp500_target": värde}
- Om OMX target nämns → {"omx_target": värde}
- Kursmål för enskilda aktier → {"TICKER.ST_target": värde}

REGLER FÖR EXECUTIVE_SUMMARY:
- Strukturera med markdown-rubriker: ## Marknadsläge, ## Teknisk analys, ## Aktier & Sektorer, ## Handlingsplan
- Max 300 ord
- Skriv på svenska
- Fokusera på actionable insights

VIKTIGT: Svara BARA med JSON-objektet, ingen annan text."""


def _get_client() -> Optional['anthropic.Anthropic']:
    """Get Anthropic client if available."""
    if not HAS_ANTHROPIC:
        print("anthropic package not installed - skipping AI analysis")
        return None
    api_key = os.environ.get('ANTHROPIC_API_KEY')
    if not api_key:
        print("ANTHROPIC_API_KEY not set - skipping AI analysis")
        return None
    return anthropic.Anthropic(api_key=api_key)


def _truncate_transcript(transcript: str, max_chars: int = 15000) -> str:
    """Truncate transcript to stay within token limits."""
    if len(transcript) > max_chars:
        return transcript[:max_chars] + "... [trunkerad]"
    return transcript


def generate_executive_summary(transcript: str, video_title: str = "") -> Optional[str]:
    """
    Generate an AI executive summary from a MarketMate transcript.
    Kept for backward compatibility — prefer generate_full_analysis().
    """
    client = _get_client()
    if not client:
        return None

    transcript = _truncate_transcript(transcript)
    user_message = f"Video: {video_title}\n\nTranskript:\n{transcript}"

    try:
        response = client.messages.create(
            model="claude-haiku-4-5",
            max_tokens=1024,
            system=SUMMARY_SYSTEM_PROMPT,
            messages=[{"role": "user", "content": user_message}],
        )
        return response.content[0].text
    except Exception as e:
        print(f"AI summary generation failed: {e}")
        return None


def generate_full_analysis(transcript: str, video_title: str = "") -> Optional[Dict]:
    """
    Generate a complete AI analysis from a MarketMate transcript.

    Returns dict with: regime, summary, tickers_mentioned, buy_signals,
    sell_signals, targets, executive_summary — or None if unavailable.
    """
    client = _get_client()
    if not client:
        return None

    transcript = _truncate_transcript(transcript)
    user_message = f"Video: {video_title}\n\nTranskript:\n{transcript}"

    try:
        response = client.messages.create(
            model="claude-haiku-4-5",
            max_tokens=2048,
            system=FULL_ANALYSIS_SYSTEM_PROMPT,
            messages=[{"role": "user", "content": user_message}],
        )
        raw = response.content[0].text.strip()

        # Strip markdown code fences if present
        if raw.startswith("```"):
            raw = raw.split("\n", 1)[1] if "\n" in raw else raw[3:]
            if raw.endswith("```"):
                raw = raw[:-3]
            raw = raw.strip()

        result = json.loads(raw)

        # Validate regime is a known value
        valid_regimes = {'BULL', 'BULL_WITH_SHORT_TERM_PULLBACK', 'NEUTRAL', 'BEAR'}
        if result.get('regime') not in valid_regimes:
            result['regime'] = 'NEUTRAL'

        # Ensure required fields exist
        result.setdefault('summary', '')
        result.setdefault('tickers_mentioned', [])
        result.setdefault('buy_signals', [])
        result.setdefault('sell_signals', [])
        result.setdefault('targets', {})
        result.setdefault('executive_summary', '')

        return result
    except json.JSONDecodeError as e:
        print(f"AI analysis JSON parse failed: {e}")
        return None
    except Exception as e:
        print(f"AI full analysis failed: {e}")
        return None
