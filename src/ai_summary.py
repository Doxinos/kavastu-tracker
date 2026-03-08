"""
AI Summary Generator - Generate executive summaries from MarketMate transcripts.

Uses Anthropic's Claude API to produce structured Swedish-language summaries
of YouTube video transcripts, extracting key market insights.
"""
import os
from typing import Optional

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


def generate_executive_summary(transcript: str, video_title: str = "") -> Optional[str]:
    """
    Generate an AI executive summary from a MarketMate transcript.

    Args:
        transcript: The video transcript text
        video_title: Optional video title for context

    Returns:
        Markdown-formatted executive summary, or None if unavailable
    """
    if not HAS_ANTHROPIC:
        print("anthropic package not installed - skipping AI summary")
        return None

    api_key = os.environ.get('ANTHROPIC_API_KEY')
    if not api_key:
        print("ANTHROPIC_API_KEY not set - skipping AI summary")
        return None

    # Truncate very long transcripts to stay within token limits
    max_chars = 15000
    if len(transcript) > max_chars:
        transcript = transcript[:max_chars] + "... [trunkerad]"

    user_message = f"Video: {video_title}\n\nTranskript:\n{transcript}"

    try:
        client = anthropic.Anthropic(api_key=api_key)
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
