"""
LLM Service - Tiered AI integration for trade analysis.

AI Tier Strategy:
- DeepSeek: General data digestion, bulk processing, quick analysis (cheapest)
- Claude Haiku: Medium-level analysis, routine decisions (fast + affordable)
- Claude Sonnet: Deep thinking, complex analysis, critical decisions (best quality)
"""

import logging
import json
import httpx
from typing import Dict, Optional, Any
from dataclasses import dataclass
from enum import Enum

import anthropic
from openai import OpenAI

# Database for learning context
try:
    from src.database import get_db
    DB_AVAILABLE = True
except ImportError:
    DB_AVAILABLE = False

logger = logging.getLogger(__name__)


class DeepSeekProxyClient:
    """Client that calls DeepSeek through Supabase Edge Function proxy.

    This keeps the DeepSeek API key secure on the server side.
    Only authenticated Vista users can access the proxy.
    """

    def __init__(self, proxy_url: str, auth_token: str):
        self.proxy_url = proxy_url
        self.auth_token = auth_token
        self.timeout = 30.0

    def _call_proxy(self, messages: list, model: str = "deepseek-chat", max_tokens: int = 800) -> dict:
        """Make a request to the DeepSeek proxy."""
        try:
            with httpx.Client(timeout=self.timeout) as client:
                response = client.post(
                    self.proxy_url,
                    headers={
                        "Authorization": f"Bearer {self.auth_token}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": model,
                        "messages": messages,
                        "max_tokens": max_tokens
                    }
                )

                if response.status_code == 401:
                    raise Exception("Authentication failed - please login again")
                elif response.status_code != 200:
                    raise Exception(f"Proxy error: {response.status_code} - {response.text}")

                return response.json()
        except httpx.TimeoutException:
            raise Exception("DeepSeek proxy timeout")
        except Exception as e:
            raise Exception(f"Proxy request failed: {e}")

    @property
    def chat(self):
        """Return self to mimic OpenAI client structure."""
        return self

    @property
    def completions(self):
        """Return self to mimic OpenAI client structure."""
        return self

    def create(self, model: str, messages: list, max_tokens: int = 800, **kwargs) -> Any:
        """Create a chat completion via proxy."""
        result = self._call_proxy(messages, model, max_tokens)

        # Convert to OpenAI-like response object
        class Choice:
            def __init__(self, content):
                self.message = type('Message', (), {'content': content})()

        class Usage:
            def __init__(self, data):
                self.total_tokens = data.get('total_tokens', 0)
                self.prompt_tokens = data.get('prompt_tokens', 0)
                self.completion_tokens = data.get('completion_tokens', 0)

        class Response:
            def __init__(self, data):
                self.choices = [Choice(data['choices'][0]['message']['content'])]
                self.usage = Usage(data.get('usage', {}))

        return Response(result)


class AITier(Enum):
    """AI model tiers for different task complexities."""
    TIER1_BULK = "deepseek"       # General data digestion, cheap bulk processing
    TIER2_MEDIUM = "haiku"        # Medium-level analysis, routine decisions
    TIER3_DEEP = "sonnet"         # Deep thinking, complex analysis, critical decisions


@dataclass
class TradeSignal:
    """Trade signal from LLM analysis."""
    action: str  # "long", "short", "hold"
    confidence: float  # 0.0 to 1.0
    reasoning: str
    thesis_summary: str = ""  # Short action summary for the bot to follow
    entry_price: Optional[float] = None
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    model_used: str = ""  # Track which model made the decision


@dataclass
class SLTPDecision:
    """SL/TP levels decided by LLM with leverage-aware risk management."""
    stop_loss: float
    take_profit: float
    reasoning: str
    max_position_loss_pct: float  # Expected max loss on position (leverage-adjusted)
    risk_reward_ratio: float
    model_used: str = ""


def format_candles_for_llm(candles: list, num_candles: int = 10) -> str:
    """Format recent candles into a readable string for LLM trend analysis.

    Shows the last N candles with OHLC data so LLM can see:
    - Higher highs / higher lows (uptrend)
    - Lower highs / lower lows (downtrend)
    - Candle body sizes and directions
    - Wicks showing rejection

    Args:
        candles: List of candle dicts with OHLC
        num_candles: How many recent candles to show

    Returns:
        Formatted string showing candle structure
    """
    if not candles or len(candles) < 2:
        return "No candle data available"

    recent = candles[-num_candles:] if len(candles) >= num_candles else candles
    lines = []

    prev_close = None
    for i, c in enumerate(recent):
        o, h, l, close = c.get("open", 0), c.get("high", 0), c.get("low", 0), c.get("close", 0)

        # Determine candle type
        body_pct = abs(close - o) / o * 100 if o > 0 else 0
        is_bullish = close > o

        # Candle description
        if body_pct > 0.5:
            candle_type = "🟢 BULL" if is_bullish else "🔴 BEAR"
        elif body_pct > 0.2:
            candle_type = "🟢 bull" if is_bullish else "🔴 bear"
        else:
            candle_type = "⚪ doji"

        # Direction from previous
        direction = ""
        if prev_close:
            if close > prev_close:
                direction = "↑"
            elif close < prev_close:
                direction = "↓"
            else:
                direction = "→"

        # Upper/lower wick analysis
        upper_wick = h - max(o, close)
        lower_wick = min(o, close) - l
        body = abs(close - o)

        wick_note = ""
        if body > 0:
            if upper_wick > body * 1.5:
                wick_note = "(rejection at top)"
            elif lower_wick > body * 1.5:
                wick_note = "(rejection at bottom)"

        lines.append(f"  [{i+1}] {candle_type} O:{o:,.0f} H:{h:,.0f} L:{l:,.0f} C:{close:,.0f} {direction} {wick_note}")
        prev_close = close

    # Analyze trend from candles
    if len(recent) >= 4:
        first_half_closes = [c["close"] for c in recent[:len(recent)//2]]
        second_half_closes = [c["close"] for c in recent[len(recent)//2:]]
        first_avg = sum(first_half_closes) / len(first_half_closes)
        second_avg = sum(second_half_closes) / len(second_half_closes)

        if second_avg > first_avg * 1.002:
            trend_summary = "📈 UPTREND (closes rising)"
        elif second_avg < first_avg * 0.998:
            trend_summary = "📉 DOWNTREND (closes falling)"
        else:
            trend_summary = "↔️ RANGING (no clear direction)"
    else:
        trend_summary = "Insufficient data for trend"

    return f"{trend_summary}\n" + "\n".join(lines)


def analyze_mtf_structure(market_data: Dict[str, Any]) -> str:
    """Analyze multi-timeframe price structure for LLM.

    Returns a comprehensive summary across ALL timeframes: 1m, 5m, 30m, 1h, 4h, 1d.
    """
    lines = []

    # Get candle data and EMA signals for all timeframes
    candles_1m = market_data.get("candles_1m", [])
    candles_5m = market_data.get("candles_5m", [])
    candles_15m = market_data.get("candles_15m", [])
    candles_30m = market_data.get("candles_30m", [])
    candles_1h = market_data.get("candles_1h", [])
    candles_4h = market_data.get("candles_4h", [])
    candles_1d = market_data.get("candles_1d", [])

    # EMA signals per timeframe
    ema_1m = market_data.get("ema_1m_signal", "neutral")
    ema_5m = market_data.get("ema_fast_signal", "neutral")
    ema_15m = market_data.get("ema_mid_signal", "neutral")
    ema_30m = market_data.get("ema_30m_signal", "neutral")
    ema_1h = market_data.get("ema_macro_signal", "neutral")
    ema_4h = market_data.get("ema_4h_signal", "neutral")
    ema_1d = market_data.get("ema_1d_signal", "neutral")

    # RSI per timeframe
    rsi_1m = market_data.get("rsi_1m")
    rsi_5m = market_data.get("rsi")  # Default RSI is 5m
    rsi_30m = market_data.get("rsi_30m")
    rsi_1h = market_data.get("rsi_1h")
    rsi_4h = market_data.get("rsi_4h")
    rsi_1d = market_data.get("rsi_1d")

    # === TREND ALIGNMENT SUMMARY (Top-down analysis) ===
    lines.append("=" * 60)
    lines.append("📊 MULTI-TIMEFRAME TREND ANALYSIS (TOP-DOWN)")
    lines.append("=" * 60)

    # Build trend table
    tf_data = [
        ("1D", ema_1d, rsi_1d, candles_1d, "MAJOR TREND"),
        ("4H", ema_4h, rsi_4h, candles_4h, "PRIMARY TREND"),
        ("1H", ema_1h, rsi_1h, candles_1h, "SWING TREND"),
        ("30M", ema_30m, rsi_30m, candles_30m, "INTERMEDIATE"),
        ("15M", ema_15m, None, candles_15m, "SHORT-TERM"),
        ("5M", ema_5m, rsi_5m, candles_5m, "ENTRY TIMING"),
        ("1M", ema_1m, rsi_1m, candles_1m, "MICRO MOMENTUM"),
    ]

    bullish_count = 0
    bearish_count = 0

    for tf_name, ema, rsi, candles, purpose in tf_data:
        # Determine trend direction
        if ema == "bullish":
            trend_icon = "🟢 BULLISH"
            bullish_count += 1
        elif ema == "bearish":
            trend_icon = "🔴 BEARISH"
            bearish_count += 1
        else:
            trend_icon = "⚪ NEUTRAL"

        # RSI status
        rsi_str = ""
        if rsi is not None:
            if rsi > 70:
                rsi_str = f"RSI:{rsi:.0f} ⚠️OB"
            elif rsi < 30:
                rsi_str = f"RSI:{rsi:.0f} ⚠️OS"
            else:
                rsi_str = f"RSI:{rsi:.0f}"

        # Recent candle momentum
        momentum = ""
        if candles and len(candles) >= 3:
            last_3 = candles[-3:]
            green = sum(1 for c in last_3 if c.get("close", 0) > c.get("open", 0))
            if green >= 2:
                momentum = "↑↑"
            elif green <= 1:
                momentum = "↓↓"
            else:
                momentum = "↔"

        lines.append(f"  {tf_name:4} | {trend_icon:12} | {rsi_str:12} | {momentum:4} | {purpose}")

    lines.append("-" * 60)

    # Trend alignment score
    total_tf = bullish_count + bearish_count
    if total_tf > 0:
        alignment_pct = abs(bullish_count - bearish_count) / max(total_tf, 1) * 100
        dominant = "BULLISH" if bullish_count > bearish_count else "BEARISH" if bearish_count > bullish_count else "MIXED"
        lines.append(f"🎯 TREND ALIGNMENT: {dominant} ({alignment_pct:.0f}% aligned)")
        lines.append(f"   Bullish TFs: {bullish_count}/7 | Bearish TFs: {bearish_count}/7")

        if bullish_count >= 5:
            lines.append("   ✅ STRONG BULLISH CONFLUENCE - Favor LONG entries")
        elif bearish_count >= 5:
            lines.append("   ✅ STRONG BEARISH CONFLUENCE - Favor SHORT entries")
        elif bullish_count >= 4 and bearish_count <= 2:
            lines.append("   📈 BULLISH BIAS - Look for pullback longs")
        elif bearish_count >= 4 and bullish_count <= 2:
            lines.append("   📉 BEARISH BIAS - Look for rally shorts")
        else:
            lines.append("   ⚠️ MIXED SIGNALS - Be selective, tighter stops")

    lines.append("")

    # === DETAILED CANDLE STRUCTURE BY TIMEFRAME ===
    # 1D structure (major S/R and trend)
    if candles_1d and len(candles_1d) >= 5:
        lines.append("=== 1D CANDLES (Major Trend + Key S/R) ===")
        lines.append(format_candles_for_llm(candles_1d, 5))

    # 4H structure (primary trend)
    if candles_4h and len(candles_4h) >= 5:
        lines.append("\n=== 4H CANDLES (Primary Trend) ===")
        lines.append(format_candles_for_llm(candles_4h, 5))

    # 1H structure (swing trend)
    if candles_1h and len(candles_1h) >= 6:
        lines.append("\n=== 1H CANDLES (Swing Trend) ===")
        lines.append(format_candles_for_llm(candles_1h, 6))

    # 30m structure (intermediate)
    if candles_30m and len(candles_30m) >= 6:
        lines.append("\n=== 30M CANDLES (Intermediate Structure) ===")
        lines.append(format_candles_for_llm(candles_30m, 6))

    # 5m structure (entry timing)
    if candles_5m and len(candles_5m) >= 8:
        lines.append("\n=== 5M CANDLES (Entry Timing) ===")
        lines.append(format_candles_for_llm(candles_5m, 8))

    # 1m structure (micro momentum)
    if candles_1m and len(candles_1m) >= 10:
        lines.append("\n=== 1M CANDLES (Micro Momentum) ===")
        lines.append(format_candles_for_llm(candles_1m, 10))

    if len(lines) <= 3:
        return "No multi-timeframe candle data available"

    return "\n".join(lines)


class LLMService:
    """Service for AI-powered trade analysis using tiered AI models.

    Tier Strategy:
    - DeepSeek (Tier 1): Data digestion, market summaries, bulk processing
    - Claude Haiku (Tier 2): Technical analysis, routine decisions, quick Q&A
    - Claude Sonnet (Tier 3): Trading decisions, risk analysis, complex reasoning
    """

    # Model identifiers
    DEEPSEEK_MODEL = "deepseek-chat"
    HAIKU_MODEL = "claude-3-5-haiku-20241022"  # Fast and affordable
    SONNET_MODEL = "claude-sonnet-4-20250514"  # Deep thinking

    def __init__(
        self,
        anthropic_api_key: str,
        deepseek_api_key: str = None,
        deepseek_proxy_url: str = None,
        auth_token: str = None
    ):
        self.anthropic_client = anthropic.Anthropic(api_key=anthropic_api_key)

        # DeepSeek client - use proxy if available, otherwise direct
        if deepseek_proxy_url and auth_token:
            # Secure mode: calls go through Supabase Edge Function
            # API key is stored as a server-side secret
            self.deepseek_client = DeepSeekProxyClient(deepseek_proxy_url, auth_token)
            logger.info("Using DeepSeek proxy (secure mode)")
        elif deepseek_api_key:
            # Direct mode: for local development / trading bot
            self.deepseek_client = OpenAI(
                api_key=deepseek_api_key,
                base_url="https://api.deepseek.com",
                timeout=30.0
            )
            logger.info("Using DeepSeek directly")
        else:
            raise ValueError("Either deepseek_api_key or (deepseek_proxy_url + auth_token) required")

        # Track API usage for cost monitoring
        self.usage_stats = {
            "deepseek_calls": 0,
            "haiku_calls": 0,
            "sonnet_calls": 0,
            "deepseek_tokens": 0,
            "haiku_tokens": 0,
            "sonnet_tokens": 0
        }
        
    # ==================== TIERED ANALYSIS METHODS ====================

    def analyze_with_sonnet(self, market_data: Dict[str, Any]) -> TradeSignal:
        """TIER 3 (DEEP): Use Claude Sonnet for critical trading decisions.

        Best for: Entry/exit decisions, risk assessment, complex market analysis
        Cost: Higher, but best reasoning quality
        """
        try:
            prompt = self._build_analysis_prompt(market_data)

            response = self.anthropic_client.messages.create(
                model=self.SONNET_MODEL,
                max_tokens=1024,
                messages=[{"role": "user", "content": prompt}],
                system=self._get_system_prompt()
            )

            # Track usage
            self.usage_stats["sonnet_calls"] += 1
            if hasattr(response, 'usage'):
                self.usage_stats["sonnet_tokens"] += response.usage.input_tokens + response.usage.output_tokens

            result = response.content[0].text
            signal = self._parse_signal(result)
            signal.model_used = "sonnet"
            logger.info(f"🧠 Sonnet (Deep): {signal.action} @ {signal.confidence:.0%}")
            return signal

        except Exception as e:
            logger.error(f"Sonnet analysis failed: {e}")
            return TradeSignal(action="hold", confidence=0.0, reasoning=f"Error: {e}", model_used="sonnet")

    def analyze_with_haiku(self, market_data: Dict[str, Any]) -> TradeSignal:
        """TIER 2 (MEDIUM): Use Claude Haiku for routine analysis.

        Best for: Technical confirmations, routine checks, Q&A
        Cost: Fast and affordable
        """
        try:
            prompt = self._build_analysis_prompt(market_data)

            response = self.anthropic_client.messages.create(
                model=self.HAIKU_MODEL,
                max_tokens=1024,
                messages=[{"role": "user", "content": prompt}],
                system=self._get_system_prompt()
            )

            # Track usage
            self.usage_stats["haiku_calls"] += 1
            if hasattr(response, 'usage'):
                self.usage_stats["haiku_tokens"] += response.usage.input_tokens + response.usage.output_tokens

            result = response.content[0].text
            signal = self._parse_signal(result)
            signal.model_used = "haiku"
            logger.info(f"⚡ Haiku (Medium): {signal.action} @ {signal.confidence:.0%}")
            return signal

        except Exception as e:
            logger.error(f"Haiku analysis failed: {e}")
            return TradeSignal(action="hold", confidence=0.0, reasoning=f"Error: {e}", model_used="haiku")

    def analyze_with_deepseek(self, market_data: Dict[str, Any]) -> TradeSignal:
        """PRIMARY DECISION ENGINE: DeepSeek for quantitative analysis.

        Handles 95%+ of all trading decisions with a structured, quantitative approach.
        Uses pre-calculated quant_score to anchor decisions.
        """
        try:
            # Use quantitative system prompt for more consistent decisions
            prompt = self._build_quant_analysis_prompt(market_data)

            response = self.deepseek_client.chat.completions.create(
                model=self.DEEPSEEK_MODEL,
                messages=[
                    {"role": "system", "content": self._get_quant_system_prompt()},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=800  # Shorter, more focused responses
            )

            # Track usage
            self.usage_stats["deepseek_calls"] += 1
            if hasattr(response, 'usage'):
                self.usage_stats["deepseek_tokens"] += response.usage.total_tokens

            result = response.choices[0].message.content
            signal = self._parse_signal(result)
            signal.model_used = "deepseek"
            return signal

        except Exception as e:
            logger.error(f"DeepSeek analysis failed: {e}")
            return TradeSignal(action="hold", confidence=0.0, reasoning=f"Error: {e}", model_used="deepseek")

    def decide_sltp(
        self,
        symbol: str,
        side: str,
        entry_price: float,
        leverage: int,
        market_data: Dict[str, Any],
        signal_reasoning: str = ""
    ) -> SLTPDecision:
        """Have Claude decide optimal SL/TP levels based on full context and leverage.

        This is called AFTER entry decision is made, to set intelligent risk levels.
        Claude considers:
        - Leverage (higher leverage = tighter stops to limit position loss)
        - Support/resistance levels (place SL beyond key levels)
        - ATR/volatility (wider stops in volatile conditions)
        - The original trade thesis (why we entered)
        - Risk:Reward ratio optimization
        """
        try:
            prompt = self._build_sltp_prompt(
                symbol, side, entry_price, leverage, market_data, signal_reasoning
            )

            response = self.anthropic_client.messages.create(
                model=self.SONNET_MODEL,  # Use Sonnet for critical risk decisions
                max_tokens=800,
                messages=[{"role": "user", "content": prompt}],
                system=self._get_sltp_system_prompt()
            )

            self.usage_stats["sonnet_calls"] += 1
            if hasattr(response, 'usage'):
                self.usage_stats["sonnet_tokens"] += response.usage.input_tokens + response.usage.output_tokens

            result = response.content[0].text
            decision = self._parse_sltp_decision(result, entry_price, side, leverage)
            decision.model_used = "sonnet"

            logger.info(f"🎯 Claude SL/TP: SL=${decision.stop_loss:,.2f} | TP=${decision.take_profit:,.2f} | R:R={decision.risk_reward_ratio:.1f}")
            return decision

        except Exception as e:
            logger.error(f"Claude SL/TP decision failed: {e}, using fallback")
            return self._fallback_sltp(entry_price, side, leverage, market_data)

    def _get_sltp_system_prompt(self) -> str:
        """System prompt for SL/TP decision making."""
        return """You are an EXPERT RISK MANAGER deciding Stop Loss and Take Profit levels.

YOUR GOAL: Set DYNAMIC TP based on market structure, momentum, and realistic targets.

KEY PRINCIPLE - LEVERAGE-AWARE STOPS:
- 10x leverage: 1% price move = 10% margin P&L
- 20x leverage: 1% price move = 20% margin P&L
- 40x leverage: 1% price move = 40% margin P&L
- 50x leverage: 1% price move = 50% margin P&L

STOP LOSS RULES (STRICT 3% MAX MARGIN LOSS):
1. Max MARGIN loss CAPPED at 3% (not position loss - MARGIN loss)
2. Calculate: max_sl_distance = 3% / leverage
   - At 40x: max SL = 3%/40 = 0.075% price move
   - At 50x: max SL = 3%/50 = 0.06% price move
3. Place SL BEYOND support (longs) or resistance (shorts) but WITHIN max distance
4. NEVER exceed 3% margin loss - this is a HARD LIMIT

TAKE PROFIT - DYNAMIC CALCULATION:
Your TP should be INTELLIGENT based on ALL the data provided:

1. PRIMARY TP TARGETS (use the closest realistic one):
   - For LONG: Next resistance level, previous swing high, or Fibonacci extension
   - For SHORT: Next support level, previous swing low, or Fibonacci extension

2. ADJUST TP BASED ON:
   - TREND STRENGTH (ADX): Strong trend (ADX>30) = extend TP further (1.5x-2x)
   - MOMENTUM (RSI): RSI with room to run = extend TP; RSI at extreme = conservative TP
   - VOLATILITY (ATR): High ATR = wider TP targets; Low ATR = tighter TP
   - VOLUME: High volume confirms move = extend TP
   - MARKET REGIME: Trending = let it run; Ranging = take profits at range boundary

3. TP DISTANCE GUIDELINES:
   - Minimum: 2x the SL distance (2:1 R:R)
   - Trending market: 3x-4x SL distance
   - High momentum (RSI divergence, volume spike): 4x-5x SL distance
   - Ranging/choppy: 2x-2.5x SL distance (conservative)

4. USE THE STRUCTURE:
   - Multiple S/R levels provided - pick the most realistic target
   - If strong trend, target BEYOND first resistance/support
   - If weak/ranging, target just before key level (safe exit)

OUTPUT FORMAT (JSON only):
{
  "stop_loss": <price>,
  "take_profit": <price>,
  "sl_reasoning": "<why this SL level - reference specific support/resistance>",
  "tp_reasoning": "<why this TP level - explain which level you're targeting and why based on trend/momentum>",
  "position_risk_pct": <expected position loss % if SL hit>,
  "risk_reward": <R:R ratio>,
  "tp_confidence": "<high/medium/low - how likely is TP to be reached>"
}"""

    def _build_sltp_prompt(
        self,
        symbol: str,
        side: str,
        entry_price: float,
        leverage: int,
        market_data: Dict[str, Any],
        signal_reasoning: str
    ) -> str:
        """Build comprehensive prompt for dynamic SL/TP decision."""
        atr = market_data.get('atr', entry_price * 0.02)
        atr_pct = (atr / entry_price) * 100

        # Support/Resistance - get ALL levels, not just nearest
        nearest_support = market_data.get('nearest_support', entry_price * 0.98)
        nearest_resistance = market_data.get('nearest_resistance', entry_price * 1.02)
        all_supports = market_data.get('supports', [nearest_support])
        all_resistances = market_data.get('resistances', [nearest_resistance])

        # Visual levels from chart analysis
        visual_support = market_data.get('visual_support')
        visual_resistance = market_data.get('visual_resistance')

        # Calculate max allowed SL distance based on leverage
        max_margin_loss = 3  # 3% max MARGIN loss (STRICT)
        max_sl_distance_pct = max_margin_loss / leverage  # e.g., 3%/40 = 0.075%

        if side == "long":
            max_sl_price = entry_price * (1 - max_sl_distance_pct / 100)
        else:
            max_sl_price = entry_price * (1 + max_sl_distance_pct / 100)

        # Trend & Momentum indicators
        rsi = market_data.get('rsi', 50)
        adx = market_data.get('adx', 20)
        macd_signal = market_data.get('macd_signal', 'neutral')
        ema_5m = market_data.get('ema_fast_signal', 'neutral')
        ema_15m = market_data.get('ema_mid_signal', 'neutral')
        ema_1h = market_data.get('ema_macro_signal', 'neutral')
        bb_position = market_data.get('bb_position', 0.5)

        # Volume & Order Flow
        volume_ratio = market_data.get('volume_ratio', 1.0)
        cvd_signal = market_data.get('cvd_signal', 'neutral')
        ob_bias = market_data.get('ob_bias', 'neutral')

        # Market Regime
        adaptive_regime = market_data.get('adaptive_regime', 'unknown')
        regime_strength = market_data.get('regime_strength', 0)

        # Divergences & Special Conditions
        rsi_divergence = market_data.get('rsi_divergence', 'none')
        volume_exhaustion = market_data.get('volume_exhaustion', 'none')

        # Format S/R levels
        supports_str = ", ".join([f"${s:,.0f}" for s in all_supports[:4]]) if all_supports else "N/A"
        resistances_str = ", ".join([f"${r:,.0f}" for r in all_resistances[:4]]) if all_resistances else "N/A"

        return f"""Set DYNAMIC SL/TP for this {side.upper()} trade:

═══════════════════════════════════════════════════════════════
POSITION DETAILS
═══════════════════════════════════════════════════════════════
- Symbol: {symbol}
- Side: {side.upper()}
- Entry Price: ${entry_price:,.2f}
- Leverage: {leverage}x
- ⚠️ HARD CAP: Max SL distance = {max_sl_distance_pct:.3f}% (${max_sl_price:,.2f}) for 3% max MARGIN loss

═══════════════════════════════════════════════════════════════
VOLATILITY & ATR
═══════════════════════════════════════════════════════════════
- ATR (14-period): ${atr:,.2f} ({atr_pct:.3f}%)
- Typical move per candle: ${atr:,.2f}
- Suggested SL buffer: {atr_pct * 1.5:.3f}% (1.5x ATR)

═══════════════════════════════════════════════════════════════
ALL SUPPORT/RESISTANCE LEVELS (for TP targeting)
═══════════════════════════════════════════════════════════════
RESISTANCES (potential TP targets for LONG): {resistances_str}
- Nearest: ${nearest_resistance:,.2f} ({((nearest_resistance - entry_price) / entry_price * 100):+.2f}% from entry)

SUPPORTS (potential TP targets for SHORT): {supports_str}
- Nearest: ${nearest_support:,.2f} ({((entry_price - nearest_support) / entry_price * 100):+.2f}% from entry)

{f'Visual Support (chart pattern): ${visual_support:,.2f}' if visual_support else ''}
{f'Visual Resistance (chart pattern): ${visual_resistance:,.2f}' if visual_resistance else ''}

═══════════════════════════════════════════════════════════════
TREND ANALYSIS (use to adjust TP distance)
═══════════════════════════════════════════════════════════════
- ADX (trend strength): {adx:.1f} {'(STRONG TREND - extend TP)' if adx > 30 else '(WEAK/RANGING - conservative TP)' if adx < 20 else '(MODERATE)'}
- 5m EMA trend: {ema_5m}
- 15m EMA trend: {ema_15m}
- 1H EMA trend: {ema_1h}
- MACD signal: {macd_signal}
- Market Regime: {adaptive_regime} (strength: {regime_strength:.0%})

═══════════════════════════════════════════════════════════════
MOMENTUM INDICATORS (use to adjust TP aggressiveness)
═══════════════════════════════════════════════════════════════
- RSI: {rsi:.1f} {'(OVERBOUGHT - TP may hit fast for LONG)' if rsi > 70 else '(OVERSOLD - TP may hit fast for SHORT)' if rsi < 30 else ''}
- BB Position: {bb_position:.0%} {'(at upper band)' if bb_position > 0.8 else '(at lower band)' if bb_position < 0.2 else '(mid-range)'}
- RSI Divergence: {rsi_divergence} {'⚠️ REVERSAL SIGNAL' if rsi_divergence != 'none' else ''}
- Volume Exhaustion: {volume_exhaustion}

═══════════════════════════════════════════════════════════════
VOLUME & ORDER FLOW
═══════════════════════════════════════════════════════════════
- Volume Ratio (vs avg): {volume_ratio:.2f}x {'(HIGH VOLUME - confirms move, extend TP)' if volume_ratio > 1.5 else '(LOW VOLUME - be conservative)' if volume_ratio < 0.7 else ''}
- CVD Signal: {cvd_signal}
- Order Book Bias: {ob_bias}

═══════════════════════════════════════════════════════════════
TRADE THESIS
═══════════════════════════════════════════════════════════════
{signal_reasoning or 'Standard setup based on technical signals'}

═══════════════════════════════════════════════════════════════
YOUR TASK: Set DYNAMIC TP based on above data
═══════════════════════════════════════════════════════════════
1. SL: Place beyond nearest S/R with buffer, but NEVER exceed {max_sl_distance_pct:.3f}%
2. TP: Pick realistic target from S/R levels above. Adjust based on:
   - Strong trend (ADX>{30}) + aligned timeframes → target FURTHER resistance/support
   - High volume → extends potential move → wider TP
   - Ranging market or divergence → conservative TP (first S/R level)
   - RSI extreme → may reverse soon → tighter TP

Output JSON only with your analysis."""

    def _parse_sltp_decision(
        self,
        response: str,
        entry_price: float,
        side: str,
        leverage: int
    ) -> SLTPDecision:
        """Parse Claude's SL/TP decision from response.

        CRITICAL: Enforces HARD CAP of 5% max position loss regardless of what Claude returns.
        """
        # HARD CAP: Maximum 5% position loss (non-negotiable)
        MAX_POSITION_LOSS_PCT = 5.0
        max_sl_distance_pct = MAX_POSITION_LOSS_PCT / leverage

        try:
            # Extract JSON from response
            import re
            json_match = re.search(r'\{[^{}]*\}', response, re.DOTALL)
            if json_match:
                data = json.loads(json_match.group())

                stop_loss = float(data.get('stop_loss', 0))
                take_profit = float(data.get('take_profit', 0))

                # Validate prices make sense
                if side == "long":
                    if stop_loss >= entry_price:
                        stop_loss = entry_price * 0.99  # Fallback
                    if take_profit <= entry_price:
                        take_profit = entry_price * 1.02  # Fallback
                else:
                    if stop_loss <= entry_price:
                        stop_loss = entry_price * 1.01  # Fallback
                    if take_profit >= entry_price:
                        take_profit = entry_price * 0.98  # Fallback

                # Calculate actual risk metrics
                sl_distance_pct = abs(entry_price - stop_loss) / entry_price * 100

                # ====== HARD ENFORCEMENT: CAP SL AT 5% MAX LOSS ======
                if sl_distance_pct > max_sl_distance_pct:
                    old_sl = stop_loss
                    if side == "long":
                        stop_loss = entry_price * (1 - max_sl_distance_pct / 100)
                    else:
                        stop_loss = entry_price * (1 + max_sl_distance_pct / 100)
                    sl_distance_pct = max_sl_distance_pct
                    logger.warning(f"⚠️ SL CAPPED: Claude suggested ${old_sl:,.2f} ({abs(entry_price - old_sl) / entry_price * 100:.2f}% = {abs(entry_price - old_sl) / entry_price * 100 * leverage:.1f}% loss) -> Capped to ${stop_loss:,.2f} ({max_sl_distance_pct:.2f}% = {MAX_POSITION_LOSS_PCT}% max loss)")

                tp_distance_pct = abs(take_profit - entry_price) / entry_price * 100
                position_loss_pct = sl_distance_pct * leverage
                risk_reward = tp_distance_pct / sl_distance_pct if sl_distance_pct > 0 else 2.0

                reasoning = f"SL: {data.get('sl_reasoning', 'N/A')} | TP: {data.get('tp_reasoning', 'N/A')}"

                return SLTPDecision(
                    stop_loss=stop_loss,
                    take_profit=take_profit,
                    reasoning=reasoning,
                    max_position_loss_pct=position_loss_pct,
                    risk_reward_ratio=risk_reward
                )
        except Exception as e:
            logger.warning(f"Failed to parse SL/TP response: {e}")

        # Fallback
        return self._fallback_sltp(entry_price, side, leverage, {})

    def _fallback_sltp(
        self,
        entry_price: float,
        side: str,
        leverage: int,
        market_data: Dict[str, Any]
    ) -> SLTPDecision:
        """Fallback SL/TP calculation when Claude fails.

        STRICT: Max 3% MARGIN loss cap.
        """
        # STRICT: Max 3% MARGIN loss (not position loss)
        max_margin_loss = 3  # 3% max margin loss cap
        max_sl_distance_pct = max_margin_loss / leverage  # e.g., 3%/40 = 0.075%

        # Use ATR if available, else use max distance
        atr = market_data.get('atr', entry_price * (max_sl_distance_pct / 100))
        atr_pct = (atr / entry_price) * 100

        # SL at 1.5 ATR or max allowed, whichever is SMALLER (never exceed 3% margin loss)
        sl_distance_pct = min(atr_pct * 1.5, max_sl_distance_pct)
        tp_distance_pct = sl_distance_pct * 2.5  # 2.5:1 R:R

        if side == "long":
            stop_loss = entry_price * (1 - sl_distance_pct / 100)
            take_profit = entry_price * (1 + tp_distance_pct / 100)
        else:
            stop_loss = entry_price * (1 + sl_distance_pct / 100)
            take_profit = entry_price * (1 - tp_distance_pct / 100)

        margin_loss_pct = sl_distance_pct * leverage

        return SLTPDecision(
            stop_loss=stop_loss,
            take_profit=take_profit,
            reasoning=f"Fallback: {sl_distance_pct:.3f}% SL ({margin_loss_pct:.1f}% margin risk, {leverage}x leverage), 2.5:1 R:R",
            max_position_loss_pct=margin_loss_pct,
            risk_reward_ratio=2.5
        )

    def _get_micro_system_prompt(self) -> str:
        """INSTITUTIONAL MICRO STRATEGY - Capital preservation + asymmetric returns."""
        return """You are an INSTITUTIONAL-GRADE MICRO TRADER. CAPITAL PRESERVATION FIRST.

=== PRIME DIRECTIVE ===
"The goal is NOT to be right. The goal is to extract ASYMMETRIC RETURNS while AVOIDING RUIN."
SURVIVAL > PROFIT. If in doubt, HOLD.

=== CORE RULES (NON-NEGOTIABLE) ===
1. NO TRADE without clear structure (trending/ranging/breakout)
2. NO TRADE without minimum 2 confluences
3. NO TRADE with R:R below 1:2
4. NO TRADE against HTF (4H/1H) trend
5. CASH IS A POSITION - no setup = no trade

=== MARKET REGIME IDENTIFICATION (MANDATORY) ===
Before ANY trade, classify the regime:
- TRENDING: Clear direction, EMAs aligned → Trade WITH trend only
- RANGING: Sideways, no clear bias → Fade extremes only at S/R
- VOLATILE: Event-driven, erratic → REDUCE SIZE or NO TRADE
- CHOPPY: No structure → NO TRADE

=== CONFLUENCE REQUIREMENTS (MINIMUM 2) ===
Count these factors. Need 2+ in same direction:
□ HTF trend alignment (4H/1H bias matches trade)
□ Technical confirmation (RSI, MACD, EMA cross)
□ Structure confirmation (higher low for long / lower high for short)
□ Volume/order flow confirmation
□ S/R level confirmation (at key level, not mid-range)

Score: 4-5 confluences = A+ setup | 2-3 = B setup | <2 = NO TRADE

=== VALID LONG CONDITIONS ===
ALL must be true:
✅ 4H/1H trend is BULLISH or NEUTRAL (not bearish)
✅ Price at/near support OR breaking resistance
✅ RSI not overbought (< 70 on 1H)
✅ Minimum 2 confluences aligned bullish
✅ R:R >= 1:2 (risk to nearest structure)

=== VALID SHORT CONDITIONS ===
ALL must be true:
✅ 4H/1H trend is BEARISH or NEUTRAL (not bullish)
✅ Price at/near resistance OR breaking support
✅ RSI not oversold (> 30 on 1H)
✅ Minimum 2 confluences aligned bearish
✅ R:R >= 1:2 (risk to nearest structure)

=== HOLD (NO TRADE) CONDITIONS ===
ANY of these = NO TRADE:
❌ Regime unclear (choppy price action)
❌ Confluence < 2
❌ Against HTF trend
❌ R:R < 1:2
❌ At mid-range (not at S/R)
❌ Parabolic/exhaustion candles (5+ same color)
❌ High volatility event incoming

=== CONFIDENCE CALIBRATION ===
- 0.75-0.85: A+ setup - HTF aligned, 4+ confluences, clear structure, R:R > 1:3
- 0.65-0.74: B setup - HTF aligned, 2-3 confluences, decent structure, R:R > 1:2
- 0.55-0.64: C setup - Marginal, some conflict → SKIP or tiny size
- Below 0.55: NO TRADE - confidence too low

=== OUTPUT FORMAT (JSON only) ===
{
  "action": "long" | "short" | "hold",
  "confidence": 0.0-1.0,
  "reasoning": "REGIME: X | HTF: Y | CONFLUENCE: N/5 | R:R: X:Y | DECISION: reason",
  "entry_price": price_number
}

REMEMBER: Better to miss a trade than take a bad one. Live to trade another day."""

    def _build_micro_prompt(self, market_data: Dict[str, Any]) -> str:
        """Build INSTITUTIONAL TRADING prompt with ALL context data."""
        symbol = market_data.get("symbol", "BTC")
        price = market_data.get("price", 0)
        atr = market_data.get("atr", price * 0.01)
        atr_pct = market_data.get("atr_pct", 1.0)

        # Momentum indicators
        rsi = market_data.get("rsi", 50)
        macd_signal = market_data.get("macd_signal", "neutral")
        macd_hist = market_data.get("macd_histogram", 0)
        bb_position = market_data.get("bb_position", 0.5)

        # S/R levels
        nearest_support = market_data.get("nearest_support", price * 0.997)
        nearest_resistance = market_data.get("nearest_resistance", price * 1.003)
        sr_signal = market_data.get("sr_signal", "mid_range")

        # Trend data (multi-timeframe)
        ema_4h = market_data.get("ema_4h_signal", "neutral")
        ema_1h = market_data.get("ema_macro_signal", "neutral")
        ema_mid = market_data.get("ema_mid_signal", "neutral")
        trend_5m = market_data.get("trend_5m", {})
        trend_15m = market_data.get("trend_15m", {})

        # Smart Money Concepts
        smc_bias = market_data.get("smc_bias", "neutral")
        smc_conf = market_data.get("smc_confidence", 0)

        # Bayesian signal
        bayesian_dir = market_data.get("bayesian_direction", "neutral")
        bayesian_conf = market_data.get("bayesian_confidence", 0)
        bayesian_rec = market_data.get("bayesian_recommendation", "WAIT")

        # Volume Profile
        vp_bias = market_data.get("vp_bias", "neutral")
        vp_poc = market_data.get("vp_poc", price)
        vp_position = market_data.get("vp_position", "inside_value")

        # Liquidation zones
        liq_signal = market_data.get("liquidation_signal", "neutral")
        liq_long_zone = market_data.get("liquidation_long_zone")
        liq_short_zone = market_data.get("liquidation_short_zone")

        # Quant score (technical confluence)
        quant_score = market_data.get("quant_score", {})
        quant_points = quant_score.get("score", 50) if isinstance(quant_score, dict) else 50
        quant_dir = quant_score.get("direction", "neutral") if isinstance(quant_score, dict) else "neutral"

        # Trendline
        trendline = market_data.get("trendline_signal", "neutral")

        # Get 5m candle analysis
        candles_5m = market_data.get("candles_5m", [])
        candle_analysis = self._analyze_recent_candles(candles_5m, 10) if candles_5m else "No 5m data"
        consecutive = self._count_consecutive_candles(candles_5m) if candles_5m else {"green": 0, "red": 0}

        # MTF context
        mtf_candles = analyze_mtf_structure(market_data)

        prompt = f"""═══════════════════════════════════════════════════════════════
{symbol} INSTITUTIONAL ANALYSIS @ ${price:,.2f}
═══════════════════════════════════════════════════════════════

=== 1. MARKET REGIME (4H/1H Trend) ===
4H Trend: {ema_4h.upper()} | 1H Trend: {ema_1h.upper()} | 30m: {ema_mid.upper()}
Position: {sr_signal.upper().replace('_', ' ')}
{"🟢 BULLISH REGIME - Favor LONGS" if ema_4h == "bullish" and ema_1h == "bullish" else ""}
{"🔴 BEARISH REGIME - Favor SHORTS" if ema_4h == "bearish" and ema_1h == "bearish" else ""}
{"⚪ NEUTRAL/MIXED - Be selective" if ema_4h != ema_1h else ""}

=== 2. TECHNICAL INDICATORS ===
RSI: {rsi:.1f} {"🔴 OVERBOUGHT - NO LONGS" if rsi > 70 else "🟢 OVERSOLD - NO SHORTS" if rsi < 30 else "📊 Neutral"}
MACD: {macd_signal} (histogram: {macd_hist:+.2f})
Bollinger: {bb_position:.0%} {"(at upper band)" if bb_position > 0.8 else "(at lower band)" if bb_position < 0.2 else "(mid-band)"}
ATR: ${atr:,.2f} ({atr_pct:.2f}%)

=== 3. QUANT TECHNICAL SCORE ===
Score: {quant_points}/100 | Direction: {quant_dir.upper()}
{"✅ STRONG TECHNICAL SETUP" if quant_points >= 70 else "⚠️ WEAK SETUP - CAUTION" if quant_points < 50 else "📊 Moderate setup"}

=== 4. SMART MONEY CONCEPTS ===
SMC Bias: {smc_bias.upper()} | Confidence: {smc_conf:.0%}
{"⚠️ SMC CONFLICT WARNING" if (smc_bias == "bearish" and ema_1h == "bullish") or (smc_bias == "bullish" and ema_1h == "bearish") else ""}

=== 5. BAYESIAN AGGREGATION ===
Direction: {bayesian_dir.upper()} | Confidence: {bayesian_conf:.0%}
Recommendation: {bayesian_rec}

=== 6. VOLUME PROFILE ===
Bias: {vp_bias.upper()} | POC: ${vp_poc:,.2f} | Position: {vp_position}

=== 7. KEY LEVELS ===
Support: ${nearest_support:,.2f} ({(price-nearest_support)/price*100:.2f}% below)
Resistance: ${nearest_resistance:,.2f} ({(nearest_resistance-price)/price*100:.2f}% above)
Trendline: {trendline.upper().replace('_', ' ')}

=== 8. LIQUIDATION RISK ===
Signal: {liq_signal}
Long Cascade Zone: {f"${liq_long_zone:,.0f}" if liq_long_zone else "N/A"}
Short Squeeze Zone: {f"${liq_short_zone:,.0f}" if liq_short_zone else "N/A"}

=== 9. RECENT CANDLE STRUCTURE ===
{candle_analysis}
Consecutive: {consecutive['green']} green, {consecutive['red']} red
{"⚠️ EXHAUSTION: 5+ same-color candles" if max(consecutive['green'], consecutive['red']) >= 5 else ""}

=== 10. MULTI-TIMEFRAME CONTEXT ===
{mtf_candles}

═══════════════════════════════════════════════════════════════
MAKE YOUR DECISION NOW
═══════════════════════════════════════════════════════════════

Apply your institutional mandate:
1. Identify MARKET REGIME first
2. Check for minimum 2 CONFLUENCES
3. Ensure R:R >= 1:2
4. If uncertain → HOLD (cash is a position)

Output format required:
action: [long/short/hold]
confidence: [0.0-1.0]
entry_price: [price or "market"]
stop_loss: [price]
take_profit: [price]
reasoning: [Your institutional analysis]"""

        return prompt

    def _analyze_recent_candles(self, candles: list, num: int = 8) -> str:
        """Analyze recent candles for pattern recognition."""
        if not candles or len(candles) < 3:
            return "Insufficient candle data"

        recent = candles[-num:] if len(candles) >= num else candles
        lines = []

        for i, c in enumerate(recent):
            o, h, l, close = c.get("open", 0), c.get("high", 0), c.get("low", 0), c.get("close", 0)
            body = abs(close - o)
            total_range = h - l if h > l else 1
            body_pct = (body / o * 100) if o > 0 else 0

            # Determine candle type
            is_bullish = close > o

            # Pattern detection
            upper_wick = h - max(o, close)
            lower_wick = min(o, close) - l

            pattern = ""
            if body_pct > 0.3:
                pattern = "STRONG " + ("🟢" if is_bullish else "🔴")
            elif body_pct > 0.15:
                pattern = "🟢" if is_bullish else "🔴"
            else:
                if lower_wick > body * 2:
                    pattern = "⚡ HAMMER (bullish reversal!)"
                elif upper_wick > body * 2:
                    pattern = "💫 SHOOTING STAR (bearish reversal!)"
                else:
                    pattern = "⚪ DOJI (indecision)"

            lines.append(f"  [{i+1}] {pattern} O:{o:,.0f} H:{h:,.0f} L:{l:,.0f} C:{close:,.0f} ({body_pct:+.2f}%)")

        # Trend summary
        first_close = recent[0].get("close", 0)
        last_close = recent[-1].get("close", 0)

        if last_close > first_close * 1.002:
            trend = "📈 UPTREND forming"
        elif last_close < first_close * 0.998:
            trend = "📉 DOWNTREND forming"
        else:
            trend = "↔️ RANGING"

        # Check for reversal
        if len(recent) >= 3:
            c1, c2, c3 = recent[-3], recent[-2], recent[-1]
            c1_bull = c1.get("close", 0) > c1.get("open", 0)
            c2_bull = c2.get("close", 0) > c2.get("open", 0)
            c3_bull = c3.get("close", 0) > c3.get("open", 0)

            if not c1_bull and not c2_bull and c3_bull:
                trend += " | ⚡ BULLISH REVERSAL SIGNAL!"
            elif c1_bull and c2_bull and not c3_bull:
                trend += " | 💫 BEARISH REVERSAL SIGNAL!"

        return trend + "\n" + "\n".join(lines)

    def _count_consecutive_candles(self, candles: list) -> dict:
        """Count consecutive green/red candles from the end."""
        if not candles:
            return {"green": 0, "red": 0}

        green_count = 0
        red_count = 0

        # Count from end
        for c in reversed(candles[-10:]):
            is_bullish = c.get("close", 0) > c.get("open", 0)
            if is_bullish:
                if red_count > 0:
                    break
                green_count += 1
            else:
                if green_count > 0:
                    break
                red_count += 1

        return {"green": green_count, "red": red_count}

    def _detect_pattern_regime(self, candles: list, market_data: Dict[str, Any]) -> str:
        """Detect current market pattern regime for pro trading."""
        if not candles or len(candles) < 10:
            return "⚠️ Insufficient data for pattern detection"

        recent = candles[-10:]
        highs = [c.get("high", 0) for c in recent]
        lows = [c.get("low", 0) for c in recent]
        closes = [c.get("close", 0) for c in recent]

        # Calculate basic metrics
        highest = max(highs)
        lowest = min(lows)
        price_range = highest - lowest
        current_price = closes[-1] if closes else 0

        # Higher highs / higher lows / lower highs / lower lows
        hh = highs[-1] > highs[-5] > highs[-10] if len(highs) >= 10 else False
        hl = lows[-1] > lows[-5] > lows[-10] if len(lows) >= 10 else False
        lh = highs[-1] < highs[-5] < highs[-10] if len(highs) >= 10 else False
        ll = lows[-1] < lows[-5] < lows[-10] if len(lows) >= 10 else False

        # Volatility squeeze (BB data)
        bb_width = market_data.get("bb_width", 0)
        volatility_squeeze = bb_width < 0.02 if bb_width else False

        # RSI divergence check
        rsi = market_data.get("rsi", 50)

        # Count colors
        greens = sum(1 for c in recent if c.get("close", 0) > c.get("open", 0))
        reds = len(recent) - greens

        # Pattern detection logic
        patterns = []

        # === TREND IDENTIFICATION ===
        if hh and hl:
            patterns.append("📈 UPTREND (HH+HL) - Look for bull flags, pullback longs")
        elif lh and ll:
            patterns.append("📉 DOWNTREND (LH+LL) - Look for bear flags, rally shorts")

        # === FLAG/PENNANT DETECTION ===
        # Strong move followed by consolidation
        first_half = recent[:5]
        second_half = recent[5:]
        first_range = max([c.get("high", 0) for c in first_half]) - min([c.get("low", 0) for c in first_half])
        second_range = max([c.get("high", 0) for c in second_half]) - min([c.get("low", 0) for c in second_half])

        if first_range > 0 and second_range < first_range * 0.5:
            first_bullish = sum(1 for c in first_half if c.get("close", 0) > c.get("open", 0)) >= 3
            if first_bullish:
                patterns.append("🏳️ BULL FLAG forming (impulse + tight consolidation)")
            else:
                patterns.append("🏳️ BEAR FLAG forming (impulse + tight consolidation)")

        # === COMPRESSION / SQUEEZE ===
        if volatility_squeeze:
            patterns.append("🔶 VOLATILITY SQUEEZE - Breakout imminent!")

        # Range compression (triangle-like)
        if price_range > 0:
            range_5_early = highs[2] - lows[2] if len(highs) > 2 else 0
            range_5_late = highs[-2] - lows[-2] if len(highs) > 2 else 0
            if range_5_late < range_5_early * 0.6:
                patterns.append("🔺 COMPRESSION (contracting range) - Breakout pending")

        # === REVERSAL PATTERNS ===
        last_3 = recent[-3:] if len(recent) >= 3 else recent
        c1_bull = last_3[-3].get("close", 0) > last_3[-3].get("open", 0) if len(last_3) >= 3 else False
        c2_bull = last_3[-2].get("close", 0) > last_3[-2].get("open", 0) if len(last_3) >= 2 else False
        c3_bull = last_3[-1].get("close", 0) > last_3[-1].get("open", 0) if len(last_3) >= 1 else False

        # Morning star (bearish → indecision → bullish)
        if len(last_3) >= 3:
            c2_body = abs(last_3[-2].get("close", 0) - last_3[-2].get("open", 0))
            c2_small = c2_body < price_range * 0.02  # Small body
            if not c1_bull and c2_small and c3_bull:
                patterns.append("⭐ MORNING STAR (bullish reversal) → LONG setup")

            # Evening star
            if c1_bull and c2_small and not c3_bull:
                patterns.append("⭐ EVENING STAR (bearish reversal) → SHORT setup")

        # Engulfing patterns
        if len(recent) >= 2:
            prev = recent[-2]
            curr = recent[-1]
            prev_body = abs(prev.get("close", 0) - prev.get("open", 0))
            curr_body = abs(curr.get("close", 0) - curr.get("open", 0))
            prev_bull = prev.get("close", 0) > prev.get("open", 0)
            curr_bull = curr.get("close", 0) > curr.get("open", 0)

            if not prev_bull and curr_bull and curr_body > prev_body * 1.5:
                patterns.append("🟢 BULLISH ENGULFING → LONG setup")
            elif prev_bull and not curr_bull and curr_body > prev_body * 1.5:
                patterns.append("🔴 BEARISH ENGULFING → SHORT setup")

        # === EXHAUSTION WARNING ===
        if greens >= 6:
            patterns.append("⚠️ EXHAUSTION: 6+ green candles - pullback likely, avoid new longs")
        elif reds >= 6:
            patterns.append("⚠️ EXHAUSTION: 6+ red candles - bounce likely, avoid new shorts")

        # === RSI DIVERGENCE ===
        if hh and rsi < 50:
            patterns.append("📊 BEARISH DIVERGENCE: Price higher, RSI lower → reversal risk")
        elif ll and rsi > 50:
            patterns.append("📊 BULLISH DIVERGENCE: Price lower, RSI higher → reversal risk")

        if not patterns:
            patterns.append("⚪ NO CLEAR PATTERN - Wait for setup to form")

        return "\n".join(patterns)

    # ==================== MACRO STRATEGY (Claude) ====================

    def _get_macro_system_prompt(self) -> str:
        """MACRO STRATEGY: Claude deep analysis + gatekeeping (1h/4h/1D, hold 1-5d)."""
        return """You are a MACRO TRADER and GATEKEEPER for longer-term trades (1h/4h/1D, hold 1-5d).

Your role: Deep analysis, conflict resolution, and macro validation.

TIMEFRAMES: 1h/4h/1D | HOLD: 1-5 days

=== TREND INDICATORS ===
- Ichimoku Cloud: Price above cloud = uptrend, below = downtrend
- ADX > 25: Strong trend (trending market)
- ADX < 20: Weak/no trend (ranging market)
- Multi-day EMAs as dynamic S/R

=== MACRO LONG CONDITIONS ===
✓ 1h/4h/1D all bullish (price above Ichimoku cloud, rising Tenkan/Kijun)
✓ RSI > 50 on all timeframes
✓ ADX indicating strong uptrend (>25)
✓ Pullback into macro support (cloud, trendline, VWAP)
✓ Bullish order flow (absorption of sell pressure)
✓ Sentiment NOT at extreme greed (F&G < 80)
✓ Funding rate NOT overheated

=== MACRO SHORT CONDITIONS ===
✓ Macro trend down (below Ichimoku cloud)
✓ RSI < 50 on higher TFs
✓ ADX strong on down moves
✓ Rally into known overhead resistance
✓ Bearish order flow (buyers absorbed)
✓ Skip shorts during extreme fear (F&G < 20) - short squeeze risk

=== CONFLUENCE REQUIREMENTS ===
Trade ONLY at confluence zones:
- Pullback touching multiple supports (trendline + cloud + VWAP)
- Rejection at multiple resistances (pivot + cloud + POC)

=== MULTI-TIMEFRAME ALIGNMENT ===
ALL higher timeframes must agree (no macro contradictions).
- If 1D up but 4h choppy → SKIP
- If 4h down but 1h bouncing → WAIT for confirmation

=== SENTIMENT CHECKS (CRITICAL) ===
- Fear & Greed > 80: Extra caution on longs, tighten stops
- Fear & Greed < 20: Extra caution on shorts (squeeze risk)
- Funding extreme positive: Longs crowded, fade potential
- Funding extreme negative: Shorts crowded, squeeze potential

=== STOP LOSS & RUNNER ===
- Stop: Beyond macro S/R zone OR 2x ATR on daily
- Trail: Wider ATR trailing stop for larger moves
- Scale out: Take partial at intermediate TF S/R

=== TRADE INVALIDATION ===
Exit if:
- Pullback extends beyond safe level (breaks below cloud/support on daily)
- Higher-TF sentiment shifts (funding spike, F&G extreme)
- Whale selling detected (large outflows)

=== GATEKEEPER ROLE ===
Score the trade conviction by aggregating:
1. Multi-timeframe signal alignment
2. Sentiment/macro context
3. Order flow confirmation
4. Risk/reward at current level

SKIP weak setups. Only approve HIGH-CONVICTION macro trades.

OUTPUT FORMAT (JSON only):
{
  "action": "long" | "short" | "hold",
  "confidence": 0.50-0.95,
  "reasoning": "MACRO: [TF alignment]. [Sentiment check]. [Confluence]. [Risk/reward].",
  "thesis_summary": "[MACRO LONG/SHORT] @ $[price] | Stop $[sl] (2xATR) | Target $[tp]",
  "entry_price": float,
  "stop_loss": float,
  "take_profit": float,
  "invalidation": "string describing macro invalidation criteria",
  "sentiment_warning": "string if any sentiment flags"
}"""

    def _build_macro_prompt(self, market_data: Dict[str, Any]) -> str:
        """Build MACRO strategy prompt for Claude (1h/4h/1D analysis)."""
        symbol = market_data.get("symbol", "BTC")
        price = market_data.get("price", 0)

        # Get daily ATR for wider stops
        atr = market_data.get("atr", price * 0.02)
        atr_pct = market_data.get("atr_pct", 2.0)

        # Higher timeframe trends
        ema_1h = market_data.get("ema_macro_signal", "neutral")
        ema_4h = market_data.get("ema_4h_signal", market_data.get("ema_macro_signal", "neutral"))

        # Ichimoku
        ichimoku = market_data.get("ichimoku", {})
        cloud_signal = ichimoku.get("signal", "neutral")
        price_vs_cloud = ichimoku.get("price_position", "in_cloud")

        # ADX for trend strength
        adx = market_data.get("adx", 20)
        trend_strength = "STRONG" if adx and adx > 25 else "WEAK" if adx and adx < 20 else "MODERATE"

        # Sentiment
        fear_greed = market_data.get("fear_greed_value", 50)
        fg_signal = market_data.get("fear_greed_signal", "neutral")
        funding = market_data.get("funding_rate_8h", 0)
        funding_pct = funding * 100 if funding else 0

        # RSI on higher TFs
        rsi = market_data.get("rsi", 50)
        rsi_1h = market_data.get("rsi_1h", rsi)

        # S/R levels
        nearest_support = market_data.get("nearest_support", price * 0.95)
        nearest_resistance = market_data.get("nearest_resistance", price * 1.05)

        # Order flow / whale activity
        ob_bias = market_data.get("ob_bias", "neutral")
        whale_signal = market_data.get("alpha_signals", {}).get("whale_tracking", {}).get("signal", "neutral")

        # Calculate macro stops (2x ATR)
        long_stop = price - (atr * 2.0)
        long_target = price + (atr * 4.0)
        short_stop = price + (atr * 2.0)
        short_target = price - (atr * 4.0)

        # Sentiment warnings
        sentiment_flags = []
        if fear_greed > 75:
            sentiment_flags.append(f"⚠️ GREED WARNING: F&G={fear_greed} (caution on longs)")
        if fear_greed < 25:
            sentiment_flags.append(f"⚠️ FEAR WARNING: F&G={fear_greed} (squeeze risk on shorts)")
        if funding_pct > 0.05:
            sentiment_flags.append(f"⚠️ FUNDING HIGH: {funding_pct:.3f}% (longs crowded)")
        if funding_pct < -0.05:
            sentiment_flags.append(f"⚠️ FUNDING LOW: {funding_pct:.3f}% (shorts crowded)")

        prompt = f"""=== {symbol} MACRO ANALYSIS (1h/4h/1D) ===

PRICE: ${price:,.2f} | ATR: ${atr:,.2f} ({atr_pct:.2f}%)

=== HIGHER TIMEFRAME TRENDS ===
1H EMA: {ema_1h}
4H EMA: {ema_4h}
Ichimoku: {cloud_signal} | Price {price_vs_cloud}

=== TREND STRENGTH ===
ADX: {adx:.0f} → {trend_strength} TREND
RSI (1H): {rsi_1h:.1f}

=== SENTIMENT & MACRO ===
Fear & Greed: {fear_greed}/100 ({fg_signal})
Funding (8h): {funding_pct:.4f}%
Whale Activity: {whale_signal}

{chr(10).join(sentiment_flags) if sentiment_flags else "No sentiment warnings"}

=== PRICE STRUCTURE ===
Support: ${nearest_support:,.2f}
Resistance: ${nearest_resistance:,.2f}
Order Book: {ob_bias}

=== MACRO ATR-BASED LEVELS ===
LONG: Entry ${price:,.2f} | Stop ${long_stop:,.2f} | Target ${long_target:,.2f}
SHORT: Entry ${price:,.2f} | Stop ${short_stop:,.2f} | Target ${short_target:,.2f}

AS GATEKEEPER:
1. Are all higher TFs aligned? (1h + 4h must agree)
2. Is sentiment supportive? (No extreme greed/fear against trade)
3. Is there confluence at current level?
4. Is risk/reward favorable?

Provide your MACRO trading decision with conviction score."""

        return prompt

    # ==================== STRATEGY ANALYSIS METHODS ====================

    def analyze_micro(self, market_data: Dict[str, Any]) -> TradeSignal:
        """MICRO STRATEGY: DeepSeek fast signal scanning (5m/15m/30m)."""
        try:
            prompt = self._build_micro_prompt(market_data)

            response = self.deepseek_client.chat.completions.create(
                model=self.DEEPSEEK_MODEL,
                messages=[
                    {"role": "system", "content": self._get_micro_system_prompt()},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=600
            )

            self.usage_stats["deepseek_calls"] += 1
            if hasattr(response, 'usage'):
                self.usage_stats["deepseek_tokens"] += response.usage.total_tokens

            result = response.choices[0].message.content
            signal = self._parse_signal(result)
            signal.model_used = "deepseek_micro"
            logger.info(f"⚡ MICRO (DeepSeek): {signal.action} @ {signal.confidence:.0%}")
            return signal

        except Exception as e:
            logger.error(f"MICRO analysis failed: {e}")
            return TradeSignal(action="hold", confidence=0.0, reasoning=f"Error: {e}", model_used="deepseek_micro")

    def analyze_exit(self, position_data: Dict[str, Any], market_data: Dict[str, Any]) -> Dict[str, Any]:
        """DEEPSEEK EXIT ANALYZER - Should we take profit now?

        Called for profitable positions to decide if we should exit or let it run.
        Returns: {"action": "hold"/"exit", "confidence": float, "reasoning": str}
        """
        try:
            prompt = self._build_exit_prompt(position_data, market_data)

            response = self.deepseek_client.chat.completions.create(
                model=self.DEEPSEEK_MODEL,
                messages=[
                    {"role": "system", "content": self._get_exit_system_prompt()},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=500
            )

            self.usage_stats["deepseek_calls"] += 1
            if hasattr(response, 'usage'):
                self.usage_stats["deepseek_tokens"] += response.usage.total_tokens

            result = response.choices[0].message.content
            decision = self._parse_exit_decision(result)
            logger.info(f"🎯 EXIT ANALYSIS: {decision['action'].upper()} @ {decision['confidence']:.0%}")
            return decision

        except Exception as e:
            logger.error(f"Exit analysis failed: {e}")
            return {"action": "hold", "confidence": 0.0, "reasoning": f"Error: {e}"}

    def _get_exit_system_prompt(self) -> str:
        """System prompt for exit decisions - protect gains, let winners run."""
        return """You are an INSTITUTIONAL EXIT MANAGER. Your job is to protect unrealized gains while letting winners run.

=== PRIME DIRECTIVE ===
"Let winners run. Take profit when momentum exhausts, not at arbitrary targets."

=== EXIT DECISION FRAMEWORK ===

HOLD the position (let it run) when:
✅ Trend is still intact on primary timeframe (5m/15m)
✅ Price making higher highs (longs) or lower lows (shorts)
✅ RSI not at extreme exhaustion (not >80 for longs, not <20 for shorts)
✅ No reversal candle patterns (no engulfing, no pin bars against us)
✅ Volume supporting the move

EXIT (take profit) when:
🔴 RSI hitting extreme exhaustion (>80 longs, <20 shorts)
🔴 Strong reversal candle (engulfing, shooting star, hammer against position)
🔴 Divergence forming (price higher but RSI/momentum lower)
🔴 Key resistance/support hit with rejection
🔴 3+ consecutive candles against position direction
🔴 Volume spike with reversal (potential climax)
🔴 Profit > 5% and momentum clearly fading

=== CONFIDENCE LEVELS ===
- 0.90+: STRONG exit signal - multiple reversal signs
- 0.70-0.89: EXIT - clear exhaustion or reversal pattern
- 0.50-0.69: Consider partial exit - mixed signals
- Below 0.50: HOLD - let it run

=== OUTPUT FORMAT ===
action: [hold/exit]
confidence: [0.0-1.0]
reasoning: [Why exit or why hold]

Remember: Don't exit just because we're profitable. Exit when the EDGE is gone."""

    def _build_exit_prompt(self, position_data: Dict[str, Any], market_data: Dict[str, Any]) -> str:
        """Build prompt for exit decision."""
        side = position_data.get("side", "long")
        entry_price = position_data.get("entry_price", 0)
        pnl_pct = position_data.get("pnl_pct", 0)
        best_price = position_data.get("best_price", entry_price)
        entry_time = position_data.get("entry_time")

        # Market context
        price = market_data.get("price", 0)
        rsi = market_data.get("rsi", 50)
        macd_signal = market_data.get("macd_signal", "neutral")
        macd_hist = market_data.get("macd_histogram", 0)
        ema_5m = market_data.get("ema_fast_signal", "neutral")
        ema_15m = market_data.get("ema_mid_signal", "neutral")
        bb_position = market_data.get("bb_position", 0.5)

        # Recent candles
        candles_5m = market_data.get("candles_5m", [])
        candle_analysis = ""
        if candles_5m:
            recent = candles_5m[-5:] if len(candles_5m) >= 5 else candles_5m
            greens = sum(1 for c in recent if c.get("close", 0) > c.get("open", 0))
            reds = len(recent) - greens
            candle_analysis = f"Last 5 candles: {greens} green, {reds} red"

            # Check for reversal patterns
            last = recent[-1] if recent else {}
            prev = recent[-2] if len(recent) >= 2 else {}
            if last and prev:
                last_body = abs(last.get("close", 0) - last.get("open", 0))
                prev_body = abs(prev.get("close", 0) - prev.get("open", 0))
                last_bullish = last.get("close", 0) > last.get("open", 0)
                prev_bullish = prev.get("close", 0) > prev.get("open", 0)

                if last_body > prev_body * 1.5 and last_bullish != prev_bullish:
                    candle_analysis += " | ⚠️ ENGULFING PATTERN DETECTED"

        # Support/resistance
        nearest_support = market_data.get("nearest_support", price * 0.99)
        nearest_resistance = market_data.get("nearest_resistance", price * 1.01)

        # Calculate drawdown from peak
        drawdown_pct = 0
        if best_price > 0:
            if side == "long":
                drawdown_pct = ((best_price - price) / best_price * 100) if price < best_price else 0
            else:
                drawdown_pct = ((price - best_price) / best_price * 100) if price > best_price else 0

        return f"""═══════════════════════════════════════════════════════════════
POSITION EXIT ANALYSIS
═══════════════════════════════════════════════════════════════

=== CURRENT POSITION ===
Side: {side.upper()}
Entry: ${entry_price:,.2f}
Current: ${price:,.2f}
P&L: {pnl_pct:+.2f}%
Best Price: ${best_price:,.2f} (Peak P&L)
Drawdown from Peak: {drawdown_pct:.2f}%

=== MOMENTUM INDICATORS ===
RSI: {rsi:.1f} {"🔴 OVERBOUGHT!" if rsi > 75 else "🟢 OVERSOLD!" if rsi < 25 else ""}
MACD: {macd_signal} (histogram: {macd_hist:+.3f})
Bollinger: {bb_position:.0%}

=== TREND STATUS ===
5m Trend: {ema_5m}
15m Trend: {ema_15m}
{"⚠️ TREND FLIPPING AGAINST POSITION" if (side == "long" and ema_5m == "bearish") or (side == "short" and ema_5m == "bullish") else "✅ Trend aligned"}

=== CANDLE STRUCTURE ===
{candle_analysis}

=== KEY LEVELS ===
Support: ${nearest_support:,.2f}
Resistance: ${nearest_resistance:,.2f}

═══════════════════════════════════════════════════════════════
DECISION: Should we EXIT (take profit) or HOLD (let it run)?
═══════════════════════════════════════════════════════════════

Consider:
1. Is momentum exhausting?
2. Is there a reversal pattern forming?
3. Has profit exceeded 5% with fading momentum?
4. Is RSI at extreme levels with divergence?
5. Are we giving back too much from peak (drawdown > 2%)?

Output your decision:
action: [hold/exit]
confidence: [0.0-1.0]
reasoning: [Your analysis]"""

    def _parse_exit_decision(self, response: str) -> Dict[str, Any]:
        """Parse exit decision from DeepSeek response."""
        response_lower = response.lower()

        # Default
        decision = {
            "action": "hold",
            "confidence": 0.5,
            "reasoning": response[:200]
        }

        # Parse action
        if "action:" in response_lower:
            if "exit" in response_lower.split("action:")[1][:20]:
                decision["action"] = "exit"
            elif "hold" in response_lower.split("action:")[1][:20]:
                decision["action"] = "hold"
        elif "exit" in response_lower[:100]:
            decision["action"] = "exit"

        # Parse confidence
        import re
        conf_patterns = [
            r'confidence[:\s]*([0-9]*\.?[0-9]+)',
            r'(\d+)%\s*confidence',
        ]
        for pattern in conf_patterns:
            match = re.search(pattern, response_lower)
            if match:
                val = float(match.group(1))
                if val > 1:
                    val = val / 100
                decision["confidence"] = min(1.0, max(0.0, val))
                break

        # Parse reasoning
        if "reasoning:" in response_lower:
            reasoning_start = response_lower.index("reasoning:") + 10
            decision["reasoning"] = response[reasoning_start:reasoning_start + 300].strip()

        return decision

    def analyze_macro(self, market_data: Dict[str, Any]) -> TradeSignal:
        """MACRO STRATEGY: Claude deep analysis + gatekeeping (1h/4h/1D)."""
        try:
            prompt = self._build_macro_prompt(market_data)

            response = self.anthropic_client.messages.create(
                model=self.SONNET_MODEL,
                max_tokens=800,
                messages=[{"role": "user", "content": prompt}],
                system=self._get_macro_system_prompt()
            )

            self.usage_stats["sonnet_calls"] += 1
            if hasattr(response, 'usage'):
                self.usage_stats["sonnet_tokens"] += response.usage.input_tokens + response.usage.output_tokens

            result = response.content[0].text
            signal = self._parse_signal(result)
            signal.model_used = "claude_macro"
            logger.info(f"🧠 MACRO (Claude): {signal.action} @ {signal.confidence:.0%}")
            return signal

        except Exception as e:
            logger.error(f"MACRO analysis failed: {e}")
            return TradeSignal(action="hold", confidence=0.0, reasoning=f"Error: {e}", model_used="claude_macro")

    # ==================== LEGACY ALIASES ====================

    def analyze_with_claude(self, market_data: Dict[str, Any]) -> TradeSignal:
        """Legacy alias - now routes to MACRO analysis."""
        return self.analyze_macro(market_data)

    def analyze_with_deepseek(self, market_data: Dict[str, Any]) -> TradeSignal:
        """Legacy alias - now routes to MICRO analysis."""
        return self.analyze_micro(market_data)

    def _get_system_prompt(self) -> str:
        """Proactive trader system prompt - thinks like a real trader, not a filter."""
        return """You are a PROACTIVE SWING TRADER managing a live trading account. Think like a trader who WANTS to make money, not avoid losses.

YOUR TRADING EDGE:
- Risk:Reward = 3.2x (risk 2.5% to make 8%)
- You ADD to winners (pyramid at +2%)
- Trailing stops protect gains (activate +3%, trail 2.5%)
- You take partial profits at +4% (33%) and let the rest run

HOW YOU THINK:
1. "What's the OPPORTUNITY here?" - Look for setups, not reasons to avoid
2. "What's the TREND saying?" - Trade with momentum, not against it
3. "Where's the EDGE?" - Entry near support (longs) or resistance (shorts)
4. "What's my THESIS?" - Clear reason: "Long because X, target Y, stop Z"
5. "Is risk DEFINED?" - Know your stop before entry

=== CRITICAL: COUNTER-TREND PREVENTION ===
HARD RULES - NEVER VIOLATE:
🚫 NO LONGS when RSI > 75 (overbought - price likely to reverse DOWN)
🚫 NO SHORTS when RSI < 25 (oversold - price likely to bounce UP)
🚫 NO LONGS when 1H AND 4H trends are BOTH bearish
🚫 NO SHORTS when 1H AND 4H trends are BOTH bullish

TREND-AWARE ORDER PLACEMENT:
- BULLISH macro (1H+4H bullish): Place LONGS at support, place SHORTS higher (above resistance)
- BEARISH macro (1H+4H bearish): Place SHORTS at resistance, place LONGS lower (below support)
- NEUTRAL/MIXED: Place both at S/R levels with tight stops

PROACTIVE SETUP SCANNING:
Look for these HIGH-PROBABILITY setups:
- Pullback to support in uptrend → LONG
- Bounce off EMA 21 in uptrend → LONG
- Break of resistance with volume → LONG
- Rejection at resistance in downtrend → SHORT
- Break of support with volume → SHORT
- RSI divergence at extremes → Reversal trade

CONFIDENCE = PROBABILITY OF SUCCESS:
- 0.85-1.0: A+ SETUP - Multiple confirmations, clear trend, high conviction
- 0.70-0.84: B+ SETUP - Good probability, tradeable with normal size
- 0.55-0.69: C SETUP - Possible but needs more confirmation
- Below 0.55: NO EDGE - Pass on this one

WHAT MAKES A TRADE (need 2-3 of these):
✓ Trend aligned on 1h timeframe (EMA direction)
✓ Price at good level (support/resistance/EMA)
✓ Momentum confirming (RSI, MACD direction)
✓ Volume supporting the move
✓ Visual chart pattern (if available)
✓ Alpha signals aligned (fear/greed, funding, whales)

DON'T OVERTRADE - Skip if:
✗ Price in no-man's land (middle of range)
✗ Choppy/sideways action with no direction
✗ Against major trend on 4h timeframe
✗ RSI extreme without reversal signal
✗ RSI > 75 for longs or RSI < 25 for shorts

YOUR RISK IS MANAGED AUTOMATICALLY:
- Stop Loss: 3% MAX MARGIN LOSS (tight risk per trade)
- Partial Profit: 33% at +4%
- Trailing Stop: Activates +3%, trails 2.5%
- Full Target: +8%
- Emergency Stop: -5% max

🎯 ENTRY PRICE STRATEGY (LIMIT ORDERS):
When you signal LONG or SHORT, specify your DESIRED ENTRY PRICE:
- Don't just use current market price
- For LONGS: Bid at or below support levels (pullback entry)
- For SHORTS: Offer at or above resistance levels
- Target 0.1% - 0.5% better than market for good fill
- If setup is urgent/breakout: entry_price = current price (market order)

Example entry logic:
- If price is $90,000 and you want long at support:
  → entry_price: $89,500 (bid near support)
- If breakout is happening NOW:
  → entry_price: $90,000 (take it now)

THESIS FORMAT - Be specific:
"LONG BTC @ $94,500 | Thesis: Uptrend intact, price pulled back to 1h EMA21, RSI 45 turning up, funding negative (longs get paid). Target: $102,000 (+8%). Stop: $92,100 (-2.5%). Invalidation: Break below $91,000."

COOLDOWNS: 2 hours general, 6 hours same direction. If thesis is still valid, you CAN re-enter.

OUTPUT: Valid JSON only. Be decisive - good traders ACT on good setups."""

    def _get_quant_system_prompt(self) -> str:
        """MASTER INSTITUTIONAL SYSTEM PROMPT - Capital preservation first."""
        return """You are an INSTITUTIONAL-GRADE QUANTITATIVE TRADING AGENT with a CAPITAL-PRESERVATION-FIRST mandate.
Your primary objective is to maximize RISK-ADJUSTED RETURNS over time - NOT win rate, NOT trade frequency, NOT short-term PnL spikes.

=== CORE PRINCIPLES (NON-NEGOTIABLE) ===

1. CAPITAL PRESERVATION IS ABSOLUTE
   - Never risk more than predefined percentage per trade
   - Avoid trades where downside is asymmetric or undefined
   - SURVIVAL > PROFIT

2. PROBABILISTIC THINKING ONLY
   - You do NOT predict; you assess probability distributions
   - Every trade MUST have: Defined entry, Defined invalidation, Expected Value > 0

3. PROCESS OVER OUTCOME
   - A losing trade executed correctly is a SUCCESS
   - A winning trade executed outside rules is a FAILURE

4. NO OVERTRADING
   - If no high-quality setup exists, REMAIN FLAT
   - CASH IS A POSITION

=== MARKET CONTEXT AWARENESS ===
Before any trade decision, EXPLICITLY determine:

**Market Regime:**
- Trending (directional) - Trade WITH momentum
- Ranging (mean-reverting) - Fade extremes only
- Volatile/Event-driven - REDUCE SIZE or NO TRADE
- Illiquid/Untradeable - NO TRADE

**Timeframe Alignment:**
- Higher timeframe bias (HTF) = 4H/1D trend
- Execution timeframe (LTF) = 5m/15m
- Trades MUST NOT violate HTF structure unless counter-trend logic is explicitly valid

=== SIGNAL VALIDATION FRAMEWORK ===
A trade is VALID ONLY if ALL conditions are met:

**1. STRUCTURE**
- Clear trend, range, or breakout structure
- NO ambiguous chop - if unclear, NO TRADE

**2. CONFLUENCE (MINIMUM 2 required)**
- Technical indicator confirmation (RSI divergence, VWAP deviation, EMA slope)
- Volume confirmation (expansion or absorption)
- Market structure (higher low for longs / lower high for shorts)
- Order flow or liquidity signal

**3. RISK-TO-REWARD**
- MINIMUM R:R >= 1:2 (risk 1 to make 2)
- IDEAL R:R >= 1:3
- REJECT trades with poor payoff even if probability seems high

=== EXECUTION RULES ===
- Use limit orders when possible
- NEVER chase price
- Slippage must be accounted for in expected value
- NO trades during extreme spread widening or low liquidity

=== BEHAVIORAL CONSTRAINTS (FORBIDDEN) ===
🚫 Revenge trading
🚫 Over-optimization / signal stacking without independence
🚫 Increasing size after losses
🚫 Trading outside defined liquidity windows
🚫 Fading strong breakouts

=== FAILURE MODE HANDLING ===
- If uncertainty is HIGH → Reduce size or NO TRADE
- If data quality is degraded → NO TRADE
- If regime is UNCLEAR → NO TRADE

=== CONFIDENCE CALIBRATION (0-100 scale) ===
- 80-100: Perfect A+ setup - HTF aligned, confluence 4+, clear structure, R:R > 1:3
- 65-79: Good B setup - HTF aligned, confluence 2-3, decent structure, R:R > 1:2
- 50-64: Marginal C setup - Some conflict, borderline R:R - REDUCE SIZE
- Below 50: NO TRADE - Regime unclear, poor R:R, or confluence missing

=== OUTPUT FORMAT (MANDATORY) ===
Output ONLY valid JSON:
{"action": "long/short/hold", "confidence": 0.0-1.0, "reasoning": "REGIME: X | BIAS: Y | STRUCTURE: Z | CONFLUENCE: N/4 | R:R: X:Y | DECISION: reason", "entry_price": price_number}

=== FINAL PRIME DIRECTIVE ===
"The goal is NOT to be right.
The goal is to extract ASYMMETRIC RETURNS while AVOIDING RUIN."

If in doubt: HOLD. Cash is a position. Live to trade another day."""

    def _build_quant_analysis_prompt(self, market_data: Dict[str, Any]) -> str:
        """Build quantitative analysis prompt with structured data for DeepSeek.

        Uses ALL timeframes: 1m, 5m, 15m, 30m, 1h, 4h, 1d for comprehensive analysis.
        Now includes: funding rates, historical accuracy, and learning context.
        """
        symbol = market_data.get('symbol', 'BTC')
        price = market_data.get('price', 0)

        # === FUNDING RATE (Important for position bias) ===
        funding_rate_8h = market_data.get('funding_rate_8h', 0)
        funding_pct = funding_rate_8h * 100 if funding_rate_8h else 0
        if funding_pct > 0.03:
            funding_signal = "🔴 HIGH POSITIVE (longs paying shorts) → Bearish bias"
        elif funding_pct > 0.01:
            funding_signal = "⚠️ Positive (longs paying) → Slight bearish"
        elif funding_pct < -0.03:
            funding_signal = "🟢 HIGH NEGATIVE (shorts paying longs) → Bullish bias"
        elif funding_pct < -0.01:
            funding_signal = "⚠️ Negative (shorts paying) → Slight bullish"
        else:
            funding_signal = "Neutral"

        # === HISTORICAL LEARNING CONTEXT FROM DATABASE ===
        learning_context = ""
        symbol_win_rates = ""
        try:
            if DB_AVAILABLE:
                db = get_db()
                # Get symbol-specific accuracy
                symbol_stats = db.get_symbol_accuracy(symbol)

                # Get winning patterns
                patterns = db.get_winning_patterns(symbol=symbol, min_samples=2)
                best_combos = patterns.get('best_symbol_direction_combos', [])

                # Get DeepSeek's own accuracy
                ds_stats = db.get_deepseek_accuracy(symbol=symbol, days=14)

                # Build learning context
                if ds_stats['total_predictions'] >= 3:
                    acc = ds_stats['accuracy_pct']
                    learning_context = f"""
**📚 YOUR HISTORICAL ACCURACY FOR {symbol}**
- DeepSeek Accuracy: {acc:.0f}% ({ds_stats['correct']}/{ds_stats['correct']+ds_stats['incorrect']})
- {"⚠️ BELOW 50% - Be more conservative!" if acc < 50 else "✅ Good accuracy" if acc > 60 else "Marginal accuracy"}
"""
                    # Add recent misses to avoid
                    if ds_stats.get('recent_misses'):
                        miss_summary = []
                        for m in ds_stats['recent_misses'][:3]:
                            miss_summary.append(f"  - Called {m.get('deepseek_bias', '?')}, moved {m.get('outcome_pct_4h', 0):+.1f}%")
                        if miss_summary:
                            learning_context += "Recent misses (learn from these):\n" + "\n".join(miss_summary) + "\n"

                # Build symbol win rate context
                if symbol_stats:
                    trades = symbol_stats.get('trades', {})
                    chart = symbol_stats.get('chart_signals', {})
                    if trades.get('total', 0) >= 3 or chart.get('total', 0) >= 3:
                        symbol_win_rates = f"""
**📊 {symbol} HISTORICAL WIN RATES**
- Trade signals: {trades.get('win_rate', 0)*100:.0f}% ({trades.get('wins', 0)}/{trades.get('total', 0)})
- Chart signals: {chart.get('win_rate', 0)*100:.0f}% ({chart.get('wins', 0)}/{chart.get('total', 0)})
"""
                # Best performing combos
                if best_combos:
                    combo_lines = []
                    for c in best_combos[:3]:
                        wr = (c['correct'] / c['total'] * 100) if c['total'] > 0 else 0
                        combo_lines.append(f"  - {c['symbol']} {c['direction']}: {wr:.0f}% win rate")
                    if combo_lines:
                        symbol_win_rates += "Best setups historically:\n" + "\n".join(combo_lines) + "\n"

        except Exception as e:
            logger.debug(f"Could not get learning context: {e}")

        # === MULTI-TIMEFRAME TREND SIGNALS (1m to 1d) ===
        trend_1m = market_data.get('ema_1m_signal', 'neutral')
        trend_5m = market_data.get('ema_fast_signal', 'neutral')
        trend_15m = market_data.get('ema_mid_signal', 'neutral')
        trend_30m = market_data.get('ema_30m_signal', 'neutral')
        trend_1h = market_data.get('ema_macro_signal', 'neutral')
        trend_4h = market_data.get('ema_4h_signal', 'neutral')
        trend_1d = market_data.get('ema_1d_signal', 'neutral')

        # === MULTI-TIMEFRAME RSI ===
        rsi_1m = market_data.get('rsi_1m')
        rsi_5m = market_data.get('rsi', 50)  # Default RSI is 5m
        rsi_30m = market_data.get('rsi_30m')
        rsi_1h = market_data.get('rsi_1h')
        rsi_4h = market_data.get('rsi_4h')
        rsi_1d = market_data.get('rsi_1d')

        # Daily S/R levels (institutional levels)
        sr_1d_supports = market_data.get('sr_1d_supports', [])
        sr_1d_resistances = market_data.get('sr_1d_resistances', [])

        # Momentum
        rsi = market_data.get('rsi', 50)
        rsi_direction = "rising" if rsi > 50 else "falling" if rsi < 50 else "neutral"
        macd_signal = market_data.get('macd_signal', 'neutral')
        macd_hist = market_data.get('macd_histogram', 0)

        # Structure
        support = market_data.get('nearest_support', price * 0.98)
        resistance = market_data.get('nearest_resistance', price * 1.02)
        sr_signal = market_data.get('sr_signal', 'mid_range')
        dist_to_support = ((price - support) / price) * 100 if support > 0 else 0
        dist_to_resistance = ((resistance - price) / price) * 100 if resistance > 0 else 0

        # CRITICAL: Trendline/Breakout detection
        trendline_signal = market_data.get('trendline_signal', 'neutral')
        breakout_confidence = market_data.get('breakout_confidence', 0)
        is_breaking_support = trendline_signal == 'breaking_support'
        is_breaking_resistance = trendline_signal == 'breaking_resistance'
        is_testing_support = trendline_signal == 'testing_support'
        is_testing_resistance = trendline_signal == 'testing_resistance'
        is_at_support = trendline_signal == 'at_ascending_support'
        is_at_resistance = trendline_signal == 'at_descending_resistance'

        # Level status for clarity
        support_status = "HOLDING"
        if is_breaking_support:
            support_status = "⛔ BREAKING"
        elif is_testing_support:
            support_status = "⚠️ TESTING"

        resistance_status = "HOLDING"
        if is_breaking_resistance:
            resistance_status = "⛔ BREAKING"
        elif is_testing_resistance:
            resistance_status = "⚠️ TESTING"

        # Order flow
        ob_bias = market_data.get('ob_bias', 'neutral')
        ob_imbalance = market_data.get('ob_imbalance', 0)
        cvd_signal = market_data.get('cvd_signal', 'neutral')

        # Volatility
        atr = market_data.get('atr', price * 0.01)
        atr_pct = (atr / price) * 100 if price > 0 else 1.0
        bb_position = market_data.get('bb_position', 0.5)

        # Consolidation zone detection (horizontal S/R building)
        is_building_support = market_data.get('is_building_support', False)
        is_building_resistance = market_data.get('is_building_resistance', False)
        consolidation_zone = market_data.get('consolidation_zone', {})
        consol_level = consolidation_zone.get('level', 0) if consolidation_zone else 0
        consol_touches = consolidation_zone.get('touches', 0) if consolidation_zone else 0
        consol_range_pct = consolidation_zone.get('range_pct', 0) if consolidation_zone else 0

        # Quant score (pre-calculated)
        quant = market_data.get('quant_score', {})
        quant_score = quant.get('score', 50)
        quant_direction = quant.get('direction', 'neutral')

        # Build confluence count across ALL timeframes
        bullish_signals = 0
        bearish_signals = 0

        # Count trend signals across all timeframes (weighted by importance)
        # 1D trend (weight 3 - major)
        if trend_1d == 'bullish': bullish_signals += 3
        elif trend_1d == 'bearish': bearish_signals += 3

        # 4H trend (weight 2 - primary)
        if trend_4h == 'bullish': bullish_signals += 2
        elif trend_4h == 'bearish': bearish_signals += 2

        # 1H trend (weight 2 - swing)
        if trend_1h == 'bullish': bullish_signals += 2
        elif trend_1h == 'bearish': bearish_signals += 2

        # 30M trend (weight 1)
        if trend_30m == 'bullish': bullish_signals += 1
        elif trend_30m == 'bearish': bearish_signals += 1

        # 15M trend (weight 1)
        if trend_15m == 'bullish': bullish_signals += 1
        elif trend_15m == 'bearish': bearish_signals += 1

        # 5M trend (weight 1)
        if trend_5m == 'bullish': bullish_signals += 1
        elif trend_5m == 'bearish': bearish_signals += 1

        # 1M trend (weight 0.5 - micro)
        if trend_1m == 'bullish': bullish_signals += 0.5
        elif trend_1m == 'bearish': bearish_signals += 0.5

        # RSI signals
        if rsi_5m and rsi_5m > 50: bullish_signals += 0.5
        elif rsi_5m and rsi_5m < 50: bearish_signals += 0.5

        if macd_signal == 'bullish': bullish_signals += 1
        elif macd_signal == 'bearish': bearish_signals += 1

        if sr_signal == 'at_support': bullish_signals += 1
        elif sr_signal == 'at_resistance': bearish_signals += 1

        if ob_bias == 'bullish': bullish_signals += 1
        elif ob_bias == 'bearish': bearish_signals += 1

        # Breakout signals override S/R (confirmed breaks are strong signals)
        if is_breaking_support: bearish_signals += 3  # Strong bearish - don't fade
        if is_breaking_resistance: bullish_signals += 3  # Strong bullish - don't fade
        # Testing signals are weaker warnings
        if is_testing_support: bearish_signals += 1  # Caution on longs
        if is_testing_resistance: bullish_signals += 1  # Caution on shorts

        confluence_score = bullish_signals - bearish_signals

        # Calculate trend alignment percentage
        trend_signals = [trend_1d, trend_4h, trend_1h, trend_30m, trend_15m, trend_5m, trend_1m]
        bullish_tfs = sum(1 for t in trend_signals if t == 'bullish')
        bearish_tfs = sum(1 for t in trend_signals if t == 'bearish')
        total_directional = bullish_tfs + bearish_tfs
        alignment_pct = (max(bullish_tfs, bearish_tfs) / max(total_directional, 1)) * 100 if total_directional > 0 else 0

        # === MACRO TREND BIAS - THE #1 RULE ===
        # Determined by 4H + 1H trend alignment (higher timeframes override lower)
        macro_bullish = trend_4h == 'bullish' or (trend_1h == 'bullish' and trend_4h != 'bearish')
        macro_bearish = trend_4h == 'bearish' or (trend_1h == 'bearish' and trend_4h != 'bullish')

        if macro_bullish and not macro_bearish:
            macro_trend_bias = "🟢 BULLISH - LONGS ONLY (NO SHORTS!)"
            allowed_actions = "LONG or HOLD only"
        elif macro_bearish and not macro_bullish:
            macro_trend_bias = "🔴 BEARISH - SHORTS ONLY (NO LONGS!)"
            allowed_actions = "SHORT or HOLD only"
        else:
            macro_trend_bias = "⚪ NEUTRAL - Both directions OK"
            allowed_actions = "Any direction OK"

        # Build breakout warning string
        breakout_warning = ""
        if is_breaking_support:
            breakout_warning = """
⚠️ BREAKOUT ALERT: SUPPORT IS BREAKING ⚠️
- DO NOT place long limit orders at support - it's FAILING
- Price is breaking DOWN through support level
- WAIT for retest or trade the breakdown SHORT
- Limit longs at broken support = CATCHING A FALLING KNIFE"""
        elif is_breaking_resistance:
            breakout_warning = """
⚠️ BREAKOUT ALERT: RESISTANCE IS BREAKING ⚠️
- DO NOT place short limit orders at resistance - it's FAILING
- Price is breaking UP through resistance level
- WAIT for retest or trade the breakout LONG
- Limit shorts at broken resistance = SHORTING INTO STRENGTH"""

        # Get multi-timeframe candle structure
        mtf_candle_analysis = analyze_mtf_structure(market_data)

        # Format daily S/R levels
        daily_sr_str = ""
        if sr_1d_supports or sr_1d_resistances:
            daily_sr_str = f"""
**DAILY S/R LEVELS (Institutional)**
- Daily Supports: {', '.join(f'${s:,.0f}' for s in sr_1d_supports[:3]) if sr_1d_supports else 'N/A'}
- Daily Resistances: {', '.join(f'${r:,.0f}' for r in sr_1d_resistances[:3]) if sr_1d_resistances else 'N/A'}
"""

        # Format RSI across timeframes
        rsi_summary = f"""
**MULTI-TIMEFRAME RSI**
- 1D RSI: {rsi_1d:.0f if rsi_1d else 'N/A'} {"⚠️OB" if rsi_1d and rsi_1d > 70 else "⚠️OS" if rsi_1d and rsi_1d < 30 else ""}
- 4H RSI: {rsi_4h:.0f if rsi_4h else 'N/A'} {"⚠️OB" if rsi_4h and rsi_4h > 70 else "⚠️OS" if rsi_4h and rsi_4h < 30 else ""}
- 1H RSI: {rsi_1h:.0f if rsi_1h else 'N/A'} {"⚠️OB" if rsi_1h and rsi_1h > 70 else "⚠️OS" if rsi_1h and rsi_1h < 30 else ""}
- 30M RSI: {rsi_30m:.0f if rsi_30m else 'N/A'}
- 5M RSI: {rsi_5m:.0f if rsi_5m else 'N/A'}
- 1M RSI: {rsi_1m:.0f if rsi_1m else 'N/A'}
"""

        return f"""=== {symbol} QUANTITATIVE ANALYSIS @ ${price:,.2f} ===

🚨🚨🚨 MACRO TREND BIAS: {macro_trend_bias} 🚨🚨🚨
⚠️ ALLOWED ACTIONS: {allowed_actions}
(Violating this rule = INSTANT LOSS. Do NOT output forbidden actions!)
{breakout_warning}
{learning_context}
{symbol_win_rates}
**💰 FUNDING RATE**
- 8h Rate: {funding_pct:+.4f}% → {funding_signal}
{"⚠️ HIGH FUNDING - Consider fading crowded trade!" if abs(funding_pct) > 0.03 else ""}

**MULTI-TIMEFRAME CANDLE STRUCTURE** (ANALYZE ALL TIMEFRAMES)
{mtf_candle_analysis}

**TREND ALIGNMENT ACROSS ALL TIMEFRAMES (1m → 1D)**
| TF  | Trend    | Weight |
|-----|----------|--------|
| 1D  | {trend_1d.upper():8} | ★★★ (Major) |
| 4H  | {trend_4h.upper():8} | ★★ (Primary) |
| 1H  | {trend_1h.upper():8} | ★★ (Swing) |
| 30M | {trend_30m.upper():8} | ★ |
| 15M | {trend_15m.upper():8} | ★ |
| 5M  | {trend_5m.upper():8} | ★ (Entry) |
| 1M  | {trend_1m.upper():8} | ½ (Micro) |

📊 ALIGNMENT: {alignment_pct:.0f}% ({bullish_tfs}/7 bullish, {bearish_tfs}/7 bearish)
{"✅ STRONG ALIGNMENT - High conviction trade!" if alignment_pct >= 70 else "⚠️ MIXED SIGNALS - Be selective" if alignment_pct >= 50 else "❌ CONFLICTING - Reduce size or wait"}
{rsi_summary}
{daily_sr_str}
**MOMENTUM DATA**
- 5M RSI: {rsi_5m:.1f} ({"OVERBOUGHT" if rsi_5m > 70 else "OVERSOLD" if rsi_5m < 30 else "neutral"})
- MACD: {macd_signal.upper()} (hist: {macd_hist:+.4f})

**STRUCTURE DATA**
- Support: ${support:,.2f} ({dist_to_support:.2f}% below) → Status: {support_status}
- Resistance: ${resistance:,.2f} ({dist_to_resistance:.2f}% above) → Status: {resistance_status}
- S/R Position: {sr_signal.upper()}
- Trendline Signal: {trendline_signal.upper()}
- Breakout Confidence: {breakout_confidence:.0%}
- BB Position: {bb_position:.0%}
{"" if not is_building_support and not is_building_resistance else f'''
**🔨 CONSOLIDATION ZONE DETECTED** (Horizontal S/R Building!)
- Type: {"SUPPORT BUILDING → AVOID SHORTS!" if is_building_support else "RESISTANCE BUILDING → AVOID LONGS!"}
- Level: ${consol_level:,.2f}
- Touches: {consol_touches}
- Range: {consol_range_pct:.2f}%
⚠️ Price is consolidating - a breakout is setting up. Don't fade the consolidation!
'''}
**ORDER FLOW** (IGNORE if contradicts macro trend!)
- Order Book Bias: {ob_bias.upper()} (imbalance: {ob_imbalance:+.1f}%)
- CVD Signal: {cvd_signal.upper()}
- ⚠️ NOTE: Short-term orderbook noise should NOT override 4H/1H trend

**VOLATILITY**
- ATR: ${atr:.2f} ({atr_pct:.2f}% of price)

**PRE-CALCULATED CONFLUENCE (Weighted)**
- Bullish Score: {bullish_signals:.1f}
- Bearish Score: {bearish_signals:.1f}
- Net Confluence: {confluence_score:+.1f}
- Quant Score: {quant_score}/100 ({quant_direction})

=== ENTRY CALCULATION RULES ===
1. LONG entries: Place at/near SUPPORT levels (not mid-range)
2. SHORT entries: Place at/near RESISTANCE levels (not mid-range)
3. Use daily S/R for major levels, 1H/4H for precision
4. Good entry = at S/R + trend aligned + RSI not extreme in wrong direction

=== HOW TO READ THE TRENDS ===
1. 1D + 4H = MAJOR TREND direction (don't fight this)
2. 1H + 30M = SWING direction (trade with this)
3. 5M + 1M = ENTRY TIMING (fine-tune entry)
4. If 5+ timeframes aligned = HIGH CONVICTION
5. If mixed = REDUCE SIZE or WAIT

=== CRITICAL S/R + TREND RULES ===
🚫 Support Status = "BREAKING" → NEVER place long limit at support
🚫 Resistance Status = "BREAKING" → NEVER place short limit at resistance
🚫 RSI > 75 on 4H = NEVER LONG (overbought)
🚫 RSI < 25 on 4H = NEVER SHORT (oversold)
⚠️ "TESTING" status → Proceed with caution, reduce confidence
✅ "HOLDING" status → OK to trade at level

=== YOUR TASK ===
1. FIRST: Check 1D/4H/1H trend alignment - what's the DOMINANT direction?
2. SECOND: Check RSI across timeframes - any extreme readings blocking trade?
3. THIRD: Identify key S/R levels for entry (daily levels are strongest)
4. FOURTH: Calculate optimal entry price (at S/R, not mid-range)
5. DECIDE: Trade direction MUST match majority of timeframes

Output JSON:
{{"action": "long/short/hold", "confidence": 0.0-1.0, "reasoning": "TF_ALIGNMENT: X/7 bullish | RSI: 4H=Y, 1H=Z | S/R: at support/resistance | ENTRY: reason", "entry_price": price_at_SR_level}}"""

    def _get_scalper_system_prompt(self) -> str:
        """AGGRESSIVE scalper system prompt - hunt for quick momentum plays."""
        return """You are an AGGRESSIVE SCALP TRADER. Your job is to FIND TRADES, not avoid them.

CRITICAL RULE: BE BIASED TOWARD TRADING, NOT HOLDING.
- If you see bullish candles → Say LONG with 60%+ confidence
- If you see bearish candles → Say SHORT with 60%+ confidence
- Only say HOLD if there's literally NO signal at all

YOUR MINDSET:
- TAKE TRADES - that's your job
- Quick small profits compound into big gains
- The stop loss protects you, so BE AGGRESSIVE
- You'd rather take 10 small trades than wait for 1 perfect trade

SCALP STRATEGY:
- Target: +1.5% profit
- Stop: -1% loss
- Hold: 5-30 minutes max

WHEN TO LONG (60%+ confidence):
- ANY bullish candle pattern (marubozu, engulfing, hammer, etc)
- RSI below 50 and price rising
- Green candles forming
- Price near support

WHEN TO SHORT (60%+ confidence):
- ANY bearish candle pattern (marubozu, engulfing, shooting star)
- RSI above 50 and price falling
- Red candles forming
- Price near resistance

CONFIDENCE SCORING - BE GENEROUS:
- Bullish/bearish candle pattern = 0.60 minimum
- Pattern + momentum aligned = 0.70
- Pattern + momentum + at level = 0.80
- NEVER give below 0.50 if there's any pattern

ONLY HOLD (below 0.50) IF:
- Literally no candle pattern
- Price stuck in tight range with no direction
- Completely mixed signals

OUTPUT FORMAT (JSON only):
{
    "action": "long" or "short" or "hold",
    "confidence": 0.50 to 1.0 (BE GENEROUS - if there's a pattern, give 0.60+),
    "reasoning": "SCALP: [Pattern] spotted. [Direction] bias.",
    "thesis_summary": "[SCALP LONG/SHORT] - [Pattern]",
    "entry_price": current_price,
    "stop_loss": entry * 0.99 for longs / entry * 1.01 for shorts,
    "take_profit": entry * 1.015 for longs / entry * 0.985 for shorts
}"""

    def _build_scalper_prompt(self, market_data: Dict[str, Any]) -> str:
        """Build prompt for 5-minute scalp analysis."""
        price = market_data.get("price", 0)
        symbol = market_data.get("symbol", "BTC")

        # 5m candle data
        candle_5m = market_data.get("candle_patterns", {}).get("5m", {})
        candle_15m = market_data.get("candle_patterns", {}).get("15m", {})

        # Momentum from sniper
        momentum_5m = market_data.get("momentum_5m_signal", "neutral")
        trend_5m = market_data.get("trend_5m", {})

        # RSI and MACD
        rsi = market_data.get("rsi", 50)
        macd_data = market_data.get("macd_data", {})
        macd_signal = market_data.get("macd_signal", "neutral")

        # Visual analysis
        visual_trend = market_data.get("visual_trend", "neutral")
        visual_pattern = market_data.get("visual_pattern", "none")
        visual_momentum = market_data.get("visual_momentum", "neutral")

        # Support/Resistance
        sr_data = market_data.get("sr_data", {})
        support = sr_data.get("nearest_support", price * 0.99) if sr_data else price * 0.99
        resistance = sr_data.get("nearest_resistance", price * 1.01) if sr_data else price * 1.01

        return f"""SCALP ANALYSIS: {symbol} @ ${price:.2f}

=== 5-MINUTE SIGNALS ===
- 5m Candle Pattern: {candle_5m.get('pattern', 'none')} ({candle_5m.get('bias', 'neutral')})
- 15m Candle Pattern: {candle_15m.get('pattern', 'none')} ({candle_15m.get('bias', 'neutral')})
- 5m Momentum: {momentum_5m}
- 5m Trend Score: {trend_5m.get('score', 0)}/100
- 5m Scalp Signal: {trend_5m.get('scalp_signal', 'None')}

=== MOMENTUM INDICATORS ===
- RSI (14): {rsi:.1f} {'(OVERSOLD)' if rsi < 35 else '(OVERBOUGHT)' if rsi > 65 else '(neutral)'}
- MACD: {macd_signal}

=== VISUAL CHART ===
- Chart Trend: {visual_trend}
- Chart Pattern: {visual_pattern}
- Momentum Signal: {visual_momentum}

=== KEY LEVELS ===
- Nearest Support: ${support:.2f} ({((price - support) / price * 100):.2f}% away)
- Nearest Resistance: ${resistance:.2f} ({((resistance - price) / price * 100):.2f}% away)

=== SCALP PARAMETERS ===
- Entry: ${price:.2f}
- Long Stop: ${price * 0.99:.2f} (-1%)
- Long Target: ${price * 1.02:.2f} (+2%)
- Short Stop: ${price * 1.01:.2f} (-1%)
- Short Target: ${price * 0.98:.2f} (+2%)

DECISION: Is there a clear 5-minute scalp setup RIGHT NOW?
Look for: Candle pattern + momentum + price at level.

Respond with JSON only."""

    def analyze_scalp(self, market_data: Dict[str, Any]) -> TradeSignal:
        """Analyze market for 5-minute scalp opportunity using DeepSeek (cost-effective)."""
        try:
            prompt = self._build_scalper_prompt(market_data)

            # Use DeepSeek instead of Haiku to save $$$ (was 360 Haiku calls/hour!)
            response = self.deepseek_client.chat.completions.create(
                model=self.DEEPSEEK_MODEL,
                max_tokens=500,
                messages=[
                    {"role": "system", "content": self._get_scalper_system_prompt()},
                    {"role": "user", "content": prompt}
                ]
            )

            self.usage_stats["deepseek_calls"] += 1
            if hasattr(response, 'usage'):
                self.usage_stats["deepseek_tokens"] += response.usage.total_tokens

            result = response.choices[0].message.content
            signal = self._parse_signal(result)
            signal.model_used = "deepseek_scalper"

            logger.info(f"⚡ Scalper (DeepSeek): {signal.action} @ {signal.confidence:.0%}")
            return signal

        except Exception as e:
            logger.error(f"Scalp analysis failed: {e}")
            return TradeSignal(action="hold", confidence=0, reasoning=f"Error: {e}", model_used="error")

    # ==================== STRATEGIC DEEPSEEK FUNCTIONS ====================

    def validate_entry_thesis(self, market_data: Dict[str, Any], proposed_action: str) -> Dict[str, Any]:
        """DeepSeek validates a proposed trade with quick sanity check.

        Returns: {valid: bool, confidence_adjustment: float, reason: str}
        Cost: ~$0.0005 per call (very cheap)
        """
        try:
            price = market_data.get("price", 0)
            rsi = market_data.get("rsi", 50)
            ema_1h = market_data.get("ema_macro_signal", "neutral")
            sr_signal = market_data.get("sr_signal", "mid_range")
            quant = market_data.get("quant_score", {})

            prompt = f"""QUICK VALIDATION: Proposed {proposed_action.upper()} @ ${price:,.0f}

KEY DATA:
- RSI: {rsi:.0f}
- 1H Trend: {ema_1h}
- S/R Position: {sr_signal}
- Quant Score: {quant.get('score', 50)}/100 {quant.get('direction', 'neutral')}

VALIDATE: Is this a good entry? Consider:
1. Is RSI at extreme that supports entry? (Long: RSI<40, Short: RSI>60)
2. Is trend aligned or are we counter-trading with edge?
3. Is price at good S/R level?

RESPOND JSON ONLY:
{{"valid": true/false, "confidence_adj": -0.15 to +0.15, "reason": "one line"}}"""

            response = self.deepseek_client.chat.completions.create(
                model=self.DEEPSEEK_MODEL,
                messages=[
                    {"role": "system", "content": "Validate trade entries. Be decisive. JSON only."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=150
            )

            self.usage_stats["deepseek_calls"] += 1
            result = response.choices[0].message.content

            # Parse JSON response
            import json
            import re
            json_match = re.search(r'\{[^}]+\}', result)
            if json_match:
                return json.loads(json_match.group())
            return {"valid": True, "confidence_adj": 0, "reason": "parse_error"}

        except Exception as e:
            logger.error(f"Entry validation failed: {e}")
            return {"valid": True, "confidence_adj": 0, "reason": f"error: {e}"}

    def analyze_market_regime(self, market_data: Dict[str, Any]) -> Dict[str, Any]:
        """DeepSeek analyzes current market regime (run once per 15-30 min).

        Returns: {regime: str, bias: str, volatility: str, recommendation: str}
        Cost: ~$0.001 per call
        """
        try:
            symbol = market_data.get("symbol", "BTC")
            price = market_data.get("price", 0)
            rsi = market_data.get("rsi", 50)
            adx = market_data.get("adx", 20)
            bb_position = market_data.get("bb_position", 0.5)
            ema_1h = market_data.get("ema_macro_signal", "neutral")
            ema_15m = market_data.get("ema_mid_signal", "neutral")
            atr_pct = market_data.get("atr_pct", 1.0)

            prompt = f"""MARKET REGIME ANALYSIS: {symbol} @ ${price:,.0f}

INDICATORS:
- RSI: {rsi:.0f}
- ADX: {adx:.0f} (>25 = trending, <20 = ranging)
- BB Position: {bb_position:.0%}
- 1H EMA: {ema_1h}
- 15M EMA: {ema_15m}
- ATR%: {atr_pct:.2f}%

DETERMINE:
1. REGIME: "trending_up", "trending_down", "ranging", "volatile", "consolidating"
2. BIAS: "bullish", "bearish", "neutral"
3. VOLATILITY: "low", "normal", "high"
4. STRATEGY: Best approach for this regime

RESPOND JSON ONLY:
{{"regime": "...", "bias": "...", "volatility": "...", "recommendation": "one line strategy"}}"""

            response = self.deepseek_client.chat.completions.create(
                model=self.DEEPSEEK_MODEL,
                messages=[
                    {"role": "system", "content": "Analyze market regimes precisely. JSON only."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=200
            )

            self.usage_stats["deepseek_calls"] += 1
            result = response.choices[0].message.content

            import json
            import re
            json_match = re.search(r'\{[^}]+\}', result)
            if json_match:
                return json.loads(json_match.group())
            return {"regime": "unknown", "bias": "neutral", "volatility": "normal", "recommendation": "parse_error"}

        except Exception as e:
            logger.error(f"Regime analysis failed: {e}")
            return {"regime": "unknown", "bias": "neutral", "volatility": "normal", "recommendation": str(e)}

    def analyze_confluence(self, market_data: Dict[str, Any]) -> Dict[str, Any]:
        """DeepSeek scores confluence of multiple signals.

        Returns: {score: 0-100, direction: str, key_factors: list, trade_quality: str}
        """
        try:
            prompt = f"""CONFLUENCE ANALYSIS

SIGNALS:
- 1H Trend: {market_data.get('ema_macro_signal', 'neutral')}
- 15M Trend: {market_data.get('ema_mid_signal', 'neutral')}
- 5M Trend: {market_data.get('ema_fast_signal', 'neutral')}
- RSI: {market_data.get('rsi', 50):.0f}
- MACD: {market_data.get('macd_signal', 'neutral')}
- S/R Signal: {market_data.get('sr_signal', 'mid_range')}
- Order Book: {market_data.get('ob_bias', 'neutral')}
- CVD: {market_data.get('cvd_signal', 'neutral')}
- Quant Score: {market_data.get('quant_score', {}).get('score', 50)}/100

SCORE the confluence (0-100) and determine:
1. How many signals agree?
2. Are higher timeframes aligned?
3. Is there a clear directional edge?

RESPOND JSON ONLY:
{{"score": 0-100, "direction": "long/short/neutral", "key_factors": ["factor1", "factor2"], "trade_quality": "A/B/C/D"}}"""

            response = self.deepseek_client.chat.completions.create(
                model=self.DEEPSEEK_MODEL,
                messages=[
                    {"role": "system", "content": "Score signal confluence. Be quantitative. JSON only."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=200
            )

            self.usage_stats["deepseek_calls"] += 1
            result = response.choices[0].message.content

            import json
            import re
            json_match = re.search(r'\{[^}]+\}', result)
            if json_match:
                return json.loads(json_match.group())
            return {"score": 50, "direction": "neutral", "key_factors": [], "trade_quality": "C"}

        except Exception as e:
            logger.error(f"Confluence analysis failed: {e}")
            return {"score": 50, "direction": "neutral", "key_factors": [], "trade_quality": "C"}

    def validate_scalp_setup(self, market_data: Dict[str, Any], direction: str) -> Dict[str, Any]:
        """DeepSeek validates scalp setup quality (fast, cheap).

        Returns: {valid: bool, quality: str, confidence: float, reason: str}
        Cost: ~$0.0003 per call (very minimal prompt)
        """
        try:
            prompt = f"""SCALP VALIDATION: {direction.upper()} @ ${market_data.get('price', 0):,.0f}

5M: RSI {market_data.get('rsi', 50):.0f} | MACD {market_data.get('macd_signal', 'neutral')} | EMA {market_data.get('ema_fast_signal', 'neutral')}
15M: EMA {market_data.get('ema_mid_signal', 'neutral')} | S/R {market_data.get('sr_signal', 'mid_range')}
OB: {market_data.get('ob_bias', 'neutral')} | CVD: {market_data.get('cvd_signal', 'neutral')}

Is this a GOOD scalp entry? Consider momentum alignment and order flow.
JSON: {{"valid": true/false, "quality": "A/B/C", "confidence": 0.5-0.9, "reason": "10 words max"}}"""

            response = self.deepseek_client.chat.completions.create(
                model=self.DEEPSEEK_MODEL,
                messages=[
                    {"role": "system", "content": "Validate scalp setups. Be fast and decisive. JSON only."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=100
            )

            self.usage_stats["deepseek_calls"] += 1
            result = response.choices[0].message.content

            import json
            import re
            json_match = re.search(r'\{[^}]+\}', result)
            if json_match:
                return json.loads(json_match.group())
            return {"valid": True, "quality": "B", "confidence": 0.6, "reason": "parse_error"}

        except Exception as e:
            logger.error(f"Scalp validation failed: {e}")
            return {"valid": True, "quality": "B", "confidence": 0.6, "reason": str(e)[:20]}

    def validate_mean_reversion(self, market_data: Dict[str, Any], direction: str) -> Dict[str, Any]:
        """DeepSeek validates mean reversion quality (is exhaustion real?).

        Returns: {valid: bool, exhaustion_quality: str, bounce_probability: float, reason: str}
        Cost: ~$0.0003 per call
        """
        try:
            rsi = market_data.get('rsi', 50)
            bb_pos = market_data.get('bb_position', 0.5)
            cvd = market_data.get('cvd_signal', 'neutral')
            vol_exhaustion = market_data.get('volume_exhaustion', 'none')
            rsi_div = market_data.get('rsi_divergence', 'none')

            prompt = f"""MEAN REVERSION CHECK: {direction.upper()} @ ${market_data.get('price', 0):,.0f}

RSI: {rsi:.0f} | BB: {bb_pos:.0%} | CVD: {cvd}
Volume Exhaustion: {vol_exhaustion} | RSI Divergence: {rsi_div}

Is this TRUE exhaustion or a trend continuation? Signs of reversal?
JSON: {{"valid": true/false, "exhaustion_quality": "strong/weak/fake", "bounce_probability": 0.3-0.8, "reason": "10 words max"}}"""

            response = self.deepseek_client.chat.completions.create(
                model=self.DEEPSEEK_MODEL,
                messages=[
                    {"role": "system", "content": "Validate mean reversion setups. Detect fake exhaustion. JSON only."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=100
            )

            self.usage_stats["deepseek_calls"] += 1
            result = response.choices[0].message.content

            import json
            import re
            json_match = re.search(r'\{[^}]+\}', result)
            if json_match:
                return json.loads(json_match.group())
            return {"valid": True, "exhaustion_quality": "weak", "bounce_probability": 0.5, "reason": "parse_error"}

        except Exception as e:
            logger.error(f"MR validation failed: {e}")
            return {"valid": True, "exhaustion_quality": "unknown", "bounce_probability": 0.5, "reason": str(e)[:20]}

    def score_sr_level(self, market_data: Dict[str, Any], level_type: str, level_price: float) -> Dict[str, Any]:
        """DeepSeek scores S/R level strength (can be cached).

        Returns: {strength: 0-100, hold_probability: float, action: str, reason: str}
        Cost: ~$0.0003 per call
        """
        try:
            price = market_data.get('price', 0)
            distance_pct = abs(price - level_price) / price * 100 if price > 0 else 0
            ob_bias = market_data.get('ob_bias', 'neutral')
            ob_walls = market_data.get('ob_walls', {})

            prompt = f"""S/R LEVEL SCORING: {level_type.upper()} @ ${level_price:,.0f}

Current: ${price:,.0f} ({distance_pct:.2f}% away)
Order Book: {ob_bias} | Walls near level: {len(ob_walls.get('bid_walls', [])) + len(ob_walls.get('ask_walls', []))}
Recent touches: likely multiple (S/R level)

How strong is this level? Will it hold?
JSON: {{"strength": 0-100, "hold_probability": 0.3-0.9, "action": "fade/breakout/wait", "reason": "10 words max"}}"""

            response = self.deepseek_client.chat.completions.create(
                model=self.DEEPSEEK_MODEL,
                messages=[
                    {"role": "system", "content": "Score S/R level strength. Consider order flow. JSON only."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=100
            )

            self.usage_stats["deepseek_calls"] += 1
            result = response.choices[0].message.content

            import json
            import re
            json_match = re.search(r'\{[^}]+\}', result)
            if json_match:
                return json.loads(json_match.group())
            return {"strength": 50, "hold_probability": 0.5, "action": "wait", "reason": "parse_error"}

        except Exception as e:
            logger.error(f"S/R scoring failed: {e}")
            return {"strength": 50, "hold_probability": 0.5, "action": "wait", "reason": str(e)[:20]}

    # ==================== MACRO TREND & LIMIT ORDER PLANNING ====================

    def analyze_macro_trend(self, market_data: Dict[str, Any]) -> Dict[str, Any]:
        """DeepSeek analyzes macro trend across 1D/4H/1H timeframes.

        Returns: {
            macro_bias: "bullish/bearish/neutral",
            trend_strength: 0-100,
            recommended_direction: "long/short/wait",
            key_levels: {long_entry, short_entry, invalidation},
            reasoning: str
        }
        Cost: ~$0.001 per call
        """
        try:
            symbol = market_data.get("symbol", "BTC")
            price = market_data.get("price", 0)

            # Multi-timeframe data
            trend_1d = market_data.get("trend_1d_signal", market_data.get("ema_macro_signal", "neutral"))
            trend_4h = market_data.get("trend_4h_signal", market_data.get("ema_macro_signal", "neutral"))
            trend_1h = market_data.get("ema_mid_signal", "neutral")
            trend_15m = market_data.get("ema_fast_signal", "neutral")

            rsi_1h = market_data.get("rsi_1h", market_data.get("rsi", 50))
            rsi_4h = market_data.get("rsi_4h", rsi_1h)

            support = market_data.get("nearest_support", 0)
            resistance = market_data.get("nearest_resistance", 0)

            # Get candle structure for LLM to see actual price action
            mtf_candles = analyze_mtf_structure(market_data)

            prompt = f"""MACRO TREND ANALYSIS: {symbol} @ ${price:,.0f}

=== CANDLE STRUCTURE (LOOK AT THIS FIRST) ===
{mtf_candles}

=== DERIVED TREND SIGNALS ===
- Daily: {trend_1d}
- 4H: {trend_4h}
- 1H: {trend_1h}
- 15M: {trend_15m}

RSI: 1H={rsi_1h:.0f}, 4H={rsi_4h:.0f}
Key S/R: Support=${support:,.0f}, Resistance=${resistance:,.0f}

TASK: Look at the CANDLES first to determine real trend, then confirm with signals.

HOW TO READ CANDLES:
- Series of 🟢 BULL candles with higher highs = UPTREND
- Series of 🔴 BEAR candles with lower lows = DOWNTREND
- Mixed/small candles = RANGING
- Long wicks = rejection/reversal potential

RULES:
1. Candle trend + ALL timeframes bullish = strong LONG bias
2. Candle trend + ALL timeframes bearish = strong SHORT bias
3. Candles conflicting with signals = REDUCE confidence
4. RSI >75 on 4H = avoid new longs, RSI <25 on 4H = avoid new shorts

JSON RESPONSE:
{{"macro_bias": "bullish/bearish/neutral", "trend_strength": 0-100, "recommended_direction": "long/short/wait", "long_entry_zone": "at_support/below_support/wait", "short_entry_zone": "at_resistance/above_resistance/wait", "reasoning": "CANDLES: [trend seen] | SIGNALS: [confirm/conflict]"}}"""

            response = self.deepseek_client.chat.completions.create(
                model=self.DEEPSEEK_MODEL,
                messages=[
                    {"role": "system", "content": "Analyze macro trends precisely. Consider all timeframes. JSON only."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=250
            )

            self.usage_stats["deepseek_calls"] += 1
            result = response.choices[0].message.content

            json_match = re.search(r'\{[^}]+\}', result)
            if json_match:
                return json.loads(json_match.group())
            return {"macro_bias": "neutral", "trend_strength": 50, "recommended_direction": "wait", "reasoning": "parse_error"}

        except Exception as e:
            logger.error(f"Macro trend analysis failed: {e}")
            return {"macro_bias": "neutral", "trend_strength": 50, "recommended_direction": "wait", "reasoning": str(e)}

    def plan_limit_orders(self, market_data: Dict[str, Any], macro_trend: Dict[str, Any]) -> Dict[str, Any]:
        """DeepSeek plans optimal limit order placement based on trend and S/R.

        CRITICAL: Respects breakout signals - won't place limits at breaking levels.

        Returns: {
            long_order: {price, sl, tp, valid: bool, reason},
            short_order: {price, sl, tp, valid: bool, reason}
        }
        Cost: ~$0.001 per call
        """
        try:
            symbol = market_data.get("symbol", "BTC")
            price = market_data.get("price", 0)
            atr = market_data.get("atr", price * 0.01)
            leverage = market_data.get("leverage", 40)

            support = market_data.get("nearest_support", 0)
            resistance = market_data.get("nearest_resistance", 0)

            # CRITICAL: Get breakout status
            trendline_signal = market_data.get("trendline_signal", "neutral")
            is_breaking_support = trendline_signal == "breaking_support"
            is_breaking_resistance = trendline_signal == "breaking_resistance"
            is_testing_support = trendline_signal == "testing_support"
            is_testing_resistance = trendline_signal == "testing_resistance"

            macro_bias = macro_trend.get("macro_bias", "neutral")
            trend_strength = macro_trend.get("trend_strength", 50)

            # Calculate max SL distance for 3% margin loss
            max_sl_pct = 3.0 / leverage  # e.g., 3% / 40 = 0.075%
            max_sl_distance = price * (max_sl_pct / 100)

            # Build support/resistance status
            support_status = "✅ HOLDING"
            if is_breaking_support:
                support_status = "⛔ BREAKING (confirmed)"
            elif is_testing_support:
                support_status = "⚠️ TESTING (caution)"

            resistance_status = "✅ HOLDING"
            if is_breaking_resistance:
                resistance_status = "⛔ BREAKING (confirmed)"
            elif is_testing_resistance:
                resistance_status = "⚠️ TESTING (caution)"

            prompt = f"""LIMIT ORDER PLANNING: {symbol} @ ${price:,.0f}

LEVEL STATUS (CRITICAL - CHECK FIRST):
- Support: {support_status}
- Resistance: {resistance_status}
- Trendline Signal: {trendline_signal}

MACRO BIAS: {macro_bias} (strength: {trend_strength}/100)
ATR: ${atr:.2f} ({atr/price*100:.2f}%)
Leverage: {leverage}x
Max SL distance for 3% margin loss: ${max_sl_distance:.2f} ({max_sl_pct:.3f}%)

S/R LEVELS:
- Support: ${support:,.0f} ({(price-support)/price*100:.2f}% below) - {support_status}
- Resistance: ${resistance:,.0f} ({(resistance-price)/price*100:.2f}% above) - {resistance_status}

CRITICAL BREAKOUT RULES:
⛔ If support is BREAKING: Set long_order valid=false (don't catch falling knife)
⛔ If resistance is BREAKING: Set short_order valid=false (don't short into strength)
⚠️ If level is TESTING: Can still place order but with tighter stops
✅ Only place limits at levels that are HOLDING or TESTING (with caution)

PLANNING RULES:
1. BULLISH bias + support HOLDING: Place LONG at/near support
2. BEARISH bias + resistance HOLDING: Place SHORT at/near resistance
3. Level BREAKING: Set that order as valid=false with reason="level_breaking"
4. Level TESTING: Set tighter stops, valid=true but add reason="level_testing"
5. SL must be <= ${max_sl_distance:.2f} from entry (3% margin risk max)
6. TP should be 2-3x SL distance minimum

JSON RESPONSE (prices as numbers):
{{"long_order": {{"price": float, "sl": float, "tp": float, "valid": true/false, "reason": "string"}}, "short_order": {{"price": float, "sl": float, "tp": float, "valid": true/false, "reason": "string"}}}}"""

            response = self.deepseek_client.chat.completions.create(
                model=self.DEEPSEEK_MODEL,
                messages=[
                    {"role": "system", "content": "Plan limit orders with BREAKOUT AWARENESS. Never place limits at breaking levels. JSON only."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=400
            )

            self.usage_stats["deepseek_calls"] += 1
            result = response.choices[0].message.content

            # Parse nested JSON
            json_match = re.search(r'\{.*\}', result, re.DOTALL)
            if json_match:
                parsed = json.loads(json_match.group())

                # HARD OVERRIDE: If level is breaking, invalidate the order regardless of LLM response
                if is_breaking_support and parsed.get("long_order", {}).get("valid"):
                    logger.warning("🚫 Overriding LLM: Support is breaking, invalidating long limit order")
                    parsed["long_order"]["valid"] = False
                    parsed["long_order"]["reason"] = "support_breaking_override"

                if is_breaking_resistance and parsed.get("short_order", {}).get("valid"):
                    logger.warning("🚫 Overriding LLM: Resistance is breaking, invalidating short limit order")
                    parsed["short_order"]["valid"] = False
                    parsed["short_order"]["reason"] = "resistance_breaking_override"

                return parsed
            return {
                "long_order": {"price": support, "sl": support * 0.995, "tp": resistance, "valid": False, "reason": "parse_error"},
                "short_order": {"price": resistance, "sl": resistance * 1.005, "tp": support, "valid": False, "reason": "parse_error"}
            }

        except Exception as e:
            logger.error(f"Limit order planning failed: {e}")
            return {
                "long_order": {"valid": False, "reason": str(e)},
                "short_order": {"valid": False, "reason": str(e)}
            }

    def validate_micro_entry(self, market_data: Dict[str, Any], direction: str) -> Dict[str, Any]:
        """DeepSeek validates micro entry with tight SL/TP planning.

        Returns: {
            valid: bool,
            sl_price: float,
            tp_price: float,
            confidence: 0-1,
            reasoning: str
        }
        Cost: ~$0.0005 per call
        """
        try:
            symbol = market_data.get("symbol", "BTC")
            price = market_data.get("price", 0)
            leverage = market_data.get("leverage", 40)
            atr = market_data.get("atr", price * 0.01)
            rsi = market_data.get("rsi", 50)

            support = market_data.get("nearest_support", 0)
            resistance = market_data.get("nearest_resistance", 0)

            ema_5m = market_data.get("ema_fast_signal", "neutral")
            ema_15m = market_data.get("ema_mid_signal", "neutral")
            ema_1h = market_data.get("ema_macro_signal", "neutral")

            # Max SL for 3% margin loss
            max_sl_pct = 3.0 / leverage
            max_sl_dist = price * (max_sl_pct / 100)

            prompt = f"""MICRO ENTRY VALIDATION: {direction.upper()} {symbol} @ ${price:,.0f}

TECHNICAL:
- RSI: {rsi:.0f} (>75=overbought, <25=oversold)
- EMA 5m/15m/1H: {ema_5m}/{ema_15m}/{ema_1h}
- Support: ${support:,.0f} | Resistance: ${resistance:,.0f}
- ATR: ${atr:.2f}

RISK LIMITS:
- Leverage: {leverage}x
- Max SL distance: ${max_sl_dist:.2f} (3% margin loss)

VALIDATION RULES:
1. NO LONGS if RSI > 75 (overbought)
2. NO SHORTS if RSI < 25 (oversold)
3. LONG should have 1H trend bullish or neutral (not bearish)
4. SHORT should have 1H trend bearish or neutral (not bullish)
5. SL just beyond S/R level but within max distance
6. TP at next S/R with room to run (2:1+ R:R)

JSON: {{"valid": true/false, "sl_price": float, "tp_price": float, "confidence": 0.5-0.9, "reasoning": "15 words max"}}"""

            response = self.deepseek_client.chat.completions.create(
                model=self.DEEPSEEK_MODEL,
                messages=[
                    {"role": "system", "content": "Validate micro entries with strict risk rules. Be conservative. JSON only."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=200
            )

            self.usage_stats["deepseek_calls"] += 1
            result = response.choices[0].message.content

            json_match = re.search(r'\{[^}]+\}', result)
            if json_match:
                return json.loads(json_match.group())
            return {"valid": False, "confidence": 0, "reasoning": "parse_error"}

        except Exception as e:
            logger.error(f"Micro validation failed: {e}")
            return {"valid": False, "confidence": 0, "reasoning": str(e)[:30]}

    # ==================== SMART ROUTING ====================

    def analyze_smart(self, market_data: Dict[str, Any], task_type: str = "trade_decision") -> TradeSignal:
        """Smart routing to appropriate AI tier based on task type.

        COST-OPTIMIZED: Use DeepSeek for most tasks, Claude only for critical decisions.

        Task Types:
        - "trade_decision": Critical entry/exit → DeepSeek screens, Sonnet confirms
        - "scalp_decision": Quick scalp trade → DeepSeek (fast + cheap)
        - "position_check": Routine position monitoring → DeepSeek (Tier 1)
        - "market_summary": General data digestion → DeepSeek (Tier 1)
        - "quick_analysis": Fast technical check → DeepSeek (Tier 1)
        """
        if task_type == "trade_decision":
            # Critical decisions: DeepSeek screens, only escalate to Sonnet if needed
            # This is handled in trading_bot.py's two-tier system
            return self.analyze_with_sonnet(market_data)
        elif task_type == "scalp_decision":
            # Fast scalp decisions → DeepSeek (was Haiku)
            return self.analyze_scalp(market_data)
        elif task_type == "position_check":
            # Routine checks → DeepSeek (was Haiku)
            return self.analyze_with_deepseek(market_data)
        elif task_type == "market_summary":
            # Bulk data processing → DeepSeek
            return self.analyze_with_deepseek(market_data)
        elif task_type == "quick_analysis":
            # Fast technical confirmation → DeepSeek (was Haiku)
            return self.analyze_with_deepseek(market_data)
        else:
            # Default to DeepSeek for cost savings
            return self.analyze_with_deepseek(market_data)

    def digest_data(self, data: str, instruction: str = "Summarize this data") -> str:
        """TIER 1: Use DeepSeek for bulk data digestion (cheapest)."""
        try:
            response = self.deepseek_client.chat.completions.create(
                model=self.DEEPSEEK_MODEL,
                messages=[
                    {"role": "system", "content": "You are a data analyst. Be concise and precise."},
                    {"role": "user", "content": f"{instruction}\n\nData:\n{data}"}
                ],
                max_tokens=500
            )
            self.usage_stats["deepseek_calls"] += 1
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"DeepSeek digest failed: {e}")
            return f"Error: {e}"

    def generate_market_summary(self, market_data: Dict[str, Any]) -> str:
        """Generate a short, conversational market summary for Discord.

        Uses DeepSeek to create 1-2 sentence market pulse.
        Cost: ~$0.0001 per summary.
        """
        try:
            price = market_data.get("price", 0)
            trend_4h = market_data.get("ema_macro_signal", "neutral")
            trend_1h = market_data.get("ema_mid_signal", "neutral")
            rsi = market_data.get("rsi", 50)
            sr_signal = market_data.get("sr_signal", "mid_range")
            support = market_data.get("nearest_support", 0)
            resistance = market_data.get("nearest_resistance", 0)
            funding = market_data.get("funding_rate", 0)

            prompt = f"""BTC is at ${price:,.0f}. 4H trend: {trend_4h}. 1H trend: {trend_1h}. RSI: {rsi:.0f}.
Position: {sr_signal}. Support: ${support:,.0f}. Resistance: ${resistance:,.0f}. Funding: {funding:.4%}.

Write 1-2 SHORT sentences describing what's happening in the market RIGHT NOW.
Be conversational like a trader chat. Use emojis sparingly. No price targets or trading advice.
Example: "BTC grinding higher in a solid uptrend 📈 RSI cooling off from overbought, could see a small pullback before continuation."
"""

            response = self.deepseek_client.chat.completions.create(
                model=self.DEEPSEEK_MODEL,
                messages=[
                    {"role": "system", "content": "You're a crypto trader giving quick market updates. Be casual, concise, insightful."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=100
            )
            self.usage_stats["deepseek_calls"] += 1
            return response.choices[0].message.content.strip()
        except Exception as e:
            logger.error(f"Market summary failed: {e}")
            return ""

    def quick_qa(self, question: str, context: str = "") -> str:
        """TIER 2: Use Haiku for quick Q&A (fast + affordable)."""
        try:
            prompt = question if not context else f"Context:\n{context}\n\nQuestion: {question}"
            response = self.anthropic_client.messages.create(
                model=self.HAIKU_MODEL,
                max_tokens=500,
                messages=[{"role": "user", "content": prompt}]
            )
            self.usage_stats["haiku_calls"] += 1
            return response.content[0].text
        except Exception as e:
            logger.error(f"Haiku Q&A failed: {e}")
            return f"Error: {e}"

    def deep_analysis(self, question: str, context: str = "") -> str:
        """TIER 3: Use Sonnet for deep analysis (best quality)."""
        try:
            prompt = question if not context else f"Context:\n{context}\n\nQuestion: {question}"
            response = self.anthropic_client.messages.create(
                model=self.SONNET_MODEL,
                max_tokens=1024,
                messages=[{"role": "user", "content": prompt}],
                system="You are an expert trading analyst. Provide thorough, well-reasoned analysis."
            )
            self.usage_stats["sonnet_calls"] += 1
            return response.content[0].text
        except Exception as e:
            logger.error(f"Sonnet analysis failed: {e}")
            return f"Error: {e}"

    def get_usage_stats(self) -> Dict[str, Any]:
        """Get API usage statistics for cost monitoring."""
        # Rough cost estimates (per 1M tokens)
        costs = {
            "deepseek": 0.14,  # $0.14/1M input, $0.28/1M output (using avg)
            "haiku": 1.00,     # $1/1M input, $5/1M output (using avg)
            "sonnet": 3.00    # $3/1M input, $15/1M output (using avg)
        }

        estimated_cost = (
            (self.usage_stats["deepseek_tokens"] / 1_000_000) * costs["deepseek"] +
            (self.usage_stats["haiku_tokens"] / 1_000_000) * costs["haiku"] +
            (self.usage_stats["sonnet_tokens"] / 1_000_000) * costs["sonnet"]
        )

        return {
            **self.usage_stats,
            "estimated_cost_usd": estimated_cost,
            "total_calls": (
                self.usage_stats["deepseek_calls"] +
                self.usage_stats["haiku_calls"] +
                self.usage_stats["sonnet_calls"]
            )
        }

    def _build_analysis_prompt(self, market_data: Dict[str, Any]) -> str:
        """Build the analysis prompt for MID-TO-LONG TERM position trading."""
        rsi = market_data.get('rsi')
        rsi_str = f"{rsi:.1f}" if rsi is not None else "N/A"

        # Macro EMA (4h 21/50)
        ema_macro_fast = market_data.get('ema_macro_fast')
        ema_macro_slow = market_data.get('ema_macro_slow')
        ema_macro_str = f"{ema_macro_fast:.2f}/{ema_macro_slow:.2f}" if ema_macro_fast and ema_macro_slow else "N/A"

        # Mid EMA (1h 9/21)
        ema_mid_fast = market_data.get('ema_mid_fast')
        ema_mid_slow = market_data.get('ema_mid_slow')
        ema_mid_str = f"{ema_mid_fast:.2f}/{ema_mid_slow:.2f}" if ema_mid_fast and ema_mid_slow else "N/A"

        funding = market_data.get('funding_rate_8h', 0)
        price = market_data.get('price', 0)

        # MACD
        macd_line = market_data.get('macd_line')
        macd_signal = market_data.get('macd_signal_line')
        macd_hist = market_data.get('macd_histogram')
        macd_str = f"MACD: {macd_line:.2f}, Signal: {macd_signal:.2f}, Hist: {macd_hist:.2f}" if macd_line else "N/A"

        # Bollinger Bands
        bb_upper = market_data.get('bb_upper')
        bb_lower = market_data.get('bb_lower')
        bb_pos = market_data.get('bb_position')
        bb_str = f"Upper: ${bb_upper:.2f}, Lower: ${bb_lower:.2f}, Position: {bb_pos:.1%}" if bb_upper else "N/A"

        # Support/Resistance
        resistance = market_data.get('nearest_resistance')
        support = market_data.get('nearest_support')
        sr_str = f"Resistance: ${resistance:.2f}, Support: ${support:.2f}" if resistance else "N/A"

        # Open Interest
        oi_usd = market_data.get('open_interest_usd', 0)
        oi_str = f"${oi_usd/1e6:.1f}M" if oi_usd else "N/A"

        # Liquidation levels
        liq_long_25x = market_data.get('liq_long_25x')
        liq_short_25x = market_data.get('liq_short_25x')
        liq_str = f"Long liq (25x): ${liq_long_25x:.2f}, Short liq (25x): ${liq_short_25x:.2f}" if liq_long_25x else "N/A"

        # ATR/Volatility
        atr_pct = market_data.get('atr_pct', 0)

        return f"""Analyze this crypto for a SWING TRADE. Think like a trader looking for opportunities.
Target: +8% | Stop: -2.5% | R:R = 3.2x | Trailing activates at +3%

MARKET DATA:
- Symbol: {market_data.get('symbol', 'ETH')}
- Current Price: ${price:.2f}
- Account Equity: ${market_data.get('equity', 0):.2f}
- Current Position: {market_data.get('position', 'none')}

=== TREND ANALYSIS ===
4H MACRO TREND:
- EMA 21/50: {ema_macro_str} ({market_data.get('ema_macro_signal', 'neutral')})
- Spread: {market_data.get('ema_macro_spread_pct', 0):.3f}%

1H MOMENTUM:
- EMA 9/21: {ema_mid_str} ({market_data.get('ema_mid_signal', 'neutral')})
- Spread: {market_data.get('ema_mid_spread_pct', 0):.3f}%

=== MOMENTUM INDICATORS ===
- RSI (14): {rsi_str} ({market_data.get('rsi_signal', 'neutral')})
- MACD: {macd_str} ({market_data.get('macd_signal', 'neutral')})
- ATR Volatility: {atr_pct:.2f}%

=== PRICE LEVELS ===
- Bollinger Bands: {bb_str} ({market_data.get('bb_signal', 'neutral')})
- Support/Resistance: {sr_str} ({market_data.get('sr_signal', 'neutral')})

=== MARKET CONTEXT ===
- Funding Rate (8h): {funding:.4f}% ({market_data.get('funding_signal', 'neutral')})
- Open Interest: {oi_str}
- 24h Volume: ${market_data.get('day_volume_usd', 0)/1e6:.1f}M

=== ALPHA SIGNALS ===
- Fear & Greed: {market_data.get('fear_greed_value', 'N/A')} ({market_data.get('fear_greed_signal', 'neutral')})
- Order Book: {market_data.get('orderbook_signal', 'neutral')} ({market_data.get('orderbook_strength', 0):.0%})
- Volume: {'SPIKE' if market_data.get('volume_spike') else 'Normal'} ({market_data.get('volume_ratio', 1):.1f}x)
- AGGREGATE: {market_data.get('alpha_aggregate_signal', 'neutral').upper()} ({market_data.get('alpha_net_score', 0):+.0%})

=== VISUAL CHART ANALYSIS (AI Vision) ===
- Trend Direction: {market_data.get('visual_trend', 'N/A')} (strength: {market_data.get('visual_trend_strength', 'N/A')}/10)
- Chart Pattern: {market_data.get('visual_pattern', 'none')} ({market_data.get('visual_pattern_stage', 'N/A')})
- Key Support: ${market_data.get('visual_support', 'N/A')}
- Key Resistance: ${market_data.get('visual_resistance', 'N/A')}
- Momentum Signal: {market_data.get('visual_momentum', 'N/A')}
- Divergence Detected: {market_data.get('visual_divergence', 'none')}
- Volume Confirms Trend: {market_data.get('visual_volume_confirms', 'N/A')}
- Vision Confidence: {market_data.get('visual_confidence', 0):.0%}
- Claude's Chart Reasoning: {market_data.get('visual_reasoning', 'N/A')}
- Suggested Trade Setup: {market_data.get('visual_trade_idea', 'N/A')}

=== 🎯 OPPORTUNITY SCORE (IMPORTANT!) ===
- Score: {market_data.get('opportunity_score', 0)}/100
- Bias: {market_data.get('opportunity_bias', 'neutral').upper()}
- Summary: {market_data.get('opportunity_summary', 'N/A')}
- Setups Found: {', '.join(market_data.get('opportunity_setups', [])) or 'None'}

=== SNIPER ANALYSIS ===
- 5m Momentum: {market_data.get('momentum_5m_signal', 'N/A')}
- 5m Trend: {market_data.get('trend_5m', {}).get('trend', 'N/A')} (Score: {market_data.get('trend_5m', {}).get('score', 0)}/100)
- Trendline Signal: {market_data.get('trendline_signal', 'N/A')}
- Confluence Score: {market_data.get('confluence_score', 0)}/100
- Confluence Direction: {market_data.get('confluence_direction', 'N/A')}

CRITICAL TRENDLINE RULES:
⚠️ If trendline_signal = "at_ascending_support" → ONLY LONG (DO NOT SHORT!)
⚠️ If trendline_signal = "at_descending_resistance" → ONLY SHORT (DO NOT LONG!)
⚠️ If trendline_signal = "breaking_support" → Bearish breakdown, short or wait
⚠️ If trendline_signal = "breaking_resistance" → Bullish breakout, long or wait

=== 📗 ORDER BOOK (L2 REAL-TIME) ===
- Imbalance: {market_data.get('ob_imbalance_pct', 0):+.0f}% ({'buying' if market_data.get('ob_imbalance', 0) > 0 else 'selling'} pressure)
- OB Bias: {market_data.get('ob_bias', 'neutral').upper()} ({market_data.get('ob_confidence', 0):.0f}% confidence)
- Bid Depth: ${market_data.get('ob_bid_depth', 0):,.0f} | Ask Depth: ${market_data.get('ob_ask_depth', 0):,.0f}
- Spread: {market_data.get('ob_spread_pct', 0):.4f}%
- Absorption: {market_data.get('ob_absorption', {}).get('interpretation', 'None detected') if market_data.get('ob_absorption') else 'None detected'}
- OB Summary: {market_data.get('ob_summary', 'N/A')}

=== 🔄 REVERSAL SIGNALS (KEY FOR TIMING) ===
- RSI Divergence: {market_data.get('rsi_divergence', 'none')} ({market_data.get('rsi_divergence_strength', 0):.0%})
- Volume Exhaustion: {market_data.get('volume_exhaustion', 'none')} ({market_data.get('volume_exhaustion_strength', 0):.0%})
- Reversal Setup: {market_data.get('reversal_setup', 'none')} ({market_data.get('reversal_confidence', 0):.0f}% confidence)

=== 📊 STRATEGY EDGE METRICS (Historical Performance) ===
- Edge Quality: {market_data.get('edge_quality', 'UNKNOWN')}
- Expected Value: {market_data.get('expected_value', 0):+.2f}% per trade
- Profit Factor: {market_data.get('profit_factor', 0):.2f} (>1.5 good, >2.0 excellent)
- Win Rate: {market_data.get('win_rate', 0):.0f}%
- Recent Streak: {market_data.get('current_streak', 0):+d} trades
- Total Trades: {market_data.get('total_trades', 0)}

=== MULTI-TIMEFRAME CANDLE PATTERNS ===
- 5m Pattern: {market_data.get('candle_patterns', {}).get('5m', {}).get('pattern', 'N/A')} ({market_data.get('candle_patterns', {}).get('5m', {}).get('bias', 'N/A')})
- 15m Pattern: {market_data.get('candle_patterns', {}).get('15m', {}).get('pattern', 'N/A')} ({market_data.get('candle_patterns', {}).get('15m', {}).get('bias', 'N/A')})
- 30m Pattern: {market_data.get('candle_patterns', {}).get('30m', {}).get('pattern', 'N/A')} ({market_data.get('candle_patterns', {}).get('30m', {}).get('bias', 'N/A')})
- Candle Confluence: {market_data.get('candle_confluence', 'N/A')}
- Candle Recommendation: {market_data.get('candle_recommendation', 'WAIT')}
- Patterns Summary: {market_data.get('candle_patterns_summary', 'N/A')}

KEY CANDLE PATTERNS TO WATCH:
✅ BULLISH: hammer, bullish_engulfing, morning_star, three_white_soldiers, dragonfly_doji
❌ BEARISH: shooting_star, bearish_engulfing, evening_star, three_black_crows, gravestone_doji
⚠️ REVERSAL: doji, long_legged_doji (indecision, potential reversal)

HOW TO DECIDE (Think like a trader):
1. Look at OPPORTUNITY SCORE first - if >= 60, there's likely a setup
2. Check if bias matches the signals (trend, momentum, alpha)
3. Identify your EDGE - what makes this a good entry?
4. Define your THESIS - clear reason with entry, target, stop

GOOD SETUPS (need 2-3 of these):
✓ Trend aligned (1h EMA direction matches trade)
✓ Price at good level (support/resistance/EMA pullback)
✓ Momentum confirming (RSI direction, MACD)
✓ Visual chart supports the trade
✓ Alpha signals aligned

SKIP IF:
✗ Price in no-man's land (middle of range)
✗ Choppy action with no clear direction
✗ Fighting the 4h trend

RISK IS MANAGED AUTOMATICALLY:
- Stop Loss: -2.5%
- Partial Profit: 33% at +4%
- Trailing Stop: Activates +3%, trails 2.5%
- Full Target: +8%
- Pyramid: Add 50% at +2% if trend confirms

CONFIDENCE = YOUR PROBABILITY ESTIMATE:
- 0.85+ = A+ Setup - Multiple confirmations, high conviction → ENTER
- 0.70-0.84 = B Setup - Good probability, tradeable → ENTER
- 0.55-0.69 = C Setup - Possible but weak → WAIT
- Below 0.55 = No edge → PASS

BE DECISIVE: If opportunity score >= 60 and bias is clear, TAKE THE TRADE.
Good traders act on good setups. Don't wait for perfection.

Respond with JSON ONLY:
{{
    "action": "long" or "short" or "hold",
    "confidence": 0.0 to 1.0,
    "reasoning": "THESIS: [Why this trade]. EDGE: [What gives us an advantage]. SETUP: [Key signals]. RISK: Stop -2.5%, target +8%.",
    "thesis_summary": "[LONG/SHORT] {market_data.get('symbol', 'ETH')} @ $[your_entry_price] | Target: +8% | Stop: -2.5% | [Key reason]",
    "entry_price": YOUR_DESIRED_ENTRY_PRICE (bid at support for longs, offer at resistance for shorts, or current price if urgent),
    "stop_loss": your_entry_price * 0.975 (for long) or * 1.025 (for short),
    "take_profit": your_entry_price * 1.08 (for long) or * 0.92 (for short)
}}

IMPORTANT: entry_price is where you WANT to get filled. The bot will place a LIMIT ORDER at this price.
- If entry_price < current_price for LONG: Bid below market (patient entry at support)
- If entry_price >= current_price for LONG: Will use market order (immediate fill)
- If entry_price > current_price for SHORT: Offer above market (patient entry at resistance)
- If entry_price <= current_price for SHORT: Will use market order (immediate fill)

Current price: ${price:.2f}
Support: ${market_data.get('nearest_support', price * 0.99):.2f}
Resistance: ${market_data.get('nearest_resistance', price * 1.01):.2f}"""

    def _parse_signal(self, response: str) -> TradeSignal:
        """Parse LLM response into TradeSignal."""
        try:
            # Clean up response - extract JSON
            response = response.strip()
            if response.startswith("```"):
                response = response.split("```")[1]
                if response.startswith("json"):
                    response = response[4:]
            response = response.strip()
            
            data = json.loads(response)
            
            return TradeSignal(
                action=data.get("action", "hold").lower(),
                confidence=float(data.get("confidence", 0.0)),
                reasoning=data.get("reasoning", ""),
                thesis_summary=data.get("thesis_summary", ""),
                entry_price=data.get("entry_price"),
                stop_loss=data.get("stop_loss"),
                take_profit=data.get("take_profit")
            )
        except Exception as e:
            logger.error(f"Failed to parse LLM response: {e}")
            return TradeSignal(action="hold", confidence=0.0, reasoning=f"Parse error: {e}")

