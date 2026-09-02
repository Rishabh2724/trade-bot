#!/usr/bin/env python3
"""
Stdlib-only stand-in for the FastAPI backend, for frontend verification.

This exists because the real backend needs fastapi, pandas, numpy and a
Binance/CoinGecko/Gemini reachable network, none of which are available in
every dev environment. It serves the same routes with the same response
shapes so the browser exercises the real fetch path, the real TypeScript
types and real CORS.

It is a dev tool. Nothing here is imported by the app, and no fixture value
reaches production code.

    python3 tools/mock-api.py                # port 8000
    NEXT_PUBLIC_API_BASE_URL=http://localhost:8000 npm run dev

Symbols are given deliberately different shapes so every render path can be
seen without editing the file:

    BTCUSDT   full confluence, LONG setup, FVGs, liquidity clusters
    ETHUSDT   neutral swing structure, NO_SETUP, no FVGs   <- the empty states
    anything  mid-strength bearish

Pass --flaky to make /api/market fail intermittently, which is what a
CoinGecko rate limit looks like from the frontend.
"""

from __future__ import annotations

import argparse
import json
import random
import re
import sys
import time
from datetime import datetime, timedelta, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

BASE_PRICES = {
    "BTC": 68_420.55,
    "ETH": 3_512.80,
    "SOL": 172.34,
    "BNB": 604.12,
    "XRP": 0.5412,
    "ADA": 0.4433,
    "DOGE": 0.1288,
    "AVAX": 27.91,
    "LINK": 14.62,
    "DOT": 6.08,
}

TIMEFRAME_SECONDS = {
    "1m": 60,
    "3m": 180,
    "5m": 300,
    "15m": 900,
    "30m": 1800,
    "1h": 3600,
    "2h": 7200,
    "4h": 14400,
    "1d": 86400,
    "1w": 604800,
}


def ts(minutes_ago: float) -> str:
    """The backend stringifies pandas Timestamps, so mimic that exact format."""
    moment = datetime.now(timezone.utc) - timedelta(minutes=minutes_ago)
    return str(moment.replace(microsecond=0)).replace("+00:00", "+00:00")


def structure_event(kind, direction, level, minutes_ago):
    return {
        "event": kind,
        "direction": direction,
        "level": round(level, 2),
        "pivot_index": 380,
        "break_index": 420,
        "pivot_timestamp": ts(minutes_ago + 40),
        "break_timestamp": ts(minutes_ago),
    }


def fvg(kind, lower, upper, minutes_ago, index):
    size = upper - lower
    return {
        "type": kind,
        "timestamp": ts(minutes_ago),
        "lower": round(lower, 2),
        "upper": round(upper, 2),
        "size": round(size, 2),
        "size_percent": round(size / upper * 100, 4),
        "formation_index": index,
        "mitigated": False,
        # Always null from the real pipeline: get_relevant_fvgs() is never
        # called, so the frontend derives distance itself.
        "position": None,
        "distance": None,
        "distance_percent": None,
    }


def analysis_payload(symbol: str, timeframe: str) -> dict:
    ticker = symbol[:-4] if symbol.endswith("USDT") else symbol
    price = BASE_PRICES.get(ticker, 100.0)

    # Empty-state fixture: no swing break, no FVGs, no setup.
    if symbol == "ETHUSDT":
        return {
            "market": {
                "symbol": symbol,
                "timeframe": timeframe,
                "current_price": round(price, 2),
            },
            "trend": "mixed",
            "indicators": {
                "sma_20": round(price * 1.001, 2),
                "sma_50": round(price * 0.998, 2),
                "ema_20": round(price * 1.0005, 2),
                "ema_50": round(price * 0.9975, 2),
                "ema_200": round(price * 0.981, 2),
                "rsi_14": 50.0,
            },
            "rsi_condition": "neutral",
            "structure": {
                # The bug-1 case: "neutral" is a real fourth state.
                "swing": {
                    "trend": "neutral",
                    "latest_event": None,
                    "events": [],
                    "pivots": [],
                },
                "internal": {
                    "trend": "neutral",
                    "latest_event": None,
                    "events": [],
                    "pivots": [],
                },
            },
            "fvg": {"active_count": 0, "zones": []},
            "liquidity": {
                "equal_highs": [],
                "equal_lows": [],
                "buy_side_liquidity": [],
                "sell_side_liquidity": [],
            },
            "confluence": {
                "bias": "mixed",
                "strength": "weak",
                "score": 0,
                "bullish_score": 1,
                "bearish_score": 1,
                "bullish_factors": ["Price above EMA 20"],
                "bearish_factors": ["Price below EMA 200"],
                "conflicting_factors": [
                    "Swing structure neutral while internal is neutral"
                ],
                "latest_swing_event": None,
                "latest_internal_event": None,
                "selected_fvg": None,
                "nearby_fvgs": [],
                "nearest_buy_side_liquidity": None,
                "nearest_sell_side_liquidity": None,
                "reasons": ["No confirmed structure break in this window"],
            },
            "setup": {
                "setup": "NO_SETUP",
                "direction": None,
                "confidence": "low",
                "score": 0,
                "entry_zone": None,
                "entry_source": None,
                "stop_loss": None,
                "stop_source": None,
                "targets": [],
                "target_source": None,
                "risk": None,
                "reward": None,
                "risk_reward": None,
                "reasons": [
                    "Confluence score 0/5 is below the threshold for a setup"
                ],
                "conflicts": [],
                "invalidated_if": None,
            },
        }

    bullish = symbol == "BTCUSDT"
    direction = "bullish" if bullish else "bearish"

    swing = structure_event("BOS", direction, price * 0.988, 74)
    internal = structure_event(
        "CHoCH", "bearish" if bullish else "bullish", price * 1.004, 12
    )

    zones = [
        fvg("bullish", price * 0.972, price * 0.979, 300, 402),
        fvg("bullish", price * 0.994, price * 0.998, 96, 448),
        fvg("bearish", price * 1.021, price * 1.027, 42, 470),
        fvg("bullish", price * 0.9995, price * 1.0008, 6, 488),
    ]

    entry_low = price * 0.994
    entry_high = price * 0.998
    stop = price * 0.9695
    target = price * 1.045
    risk = (entry_high + entry_low) / 2 - stop
    reward = target - (entry_high + entry_low) / 2

    return {
        "market": {
            "symbol": symbol,
            "timeframe": timeframe,
            "current_price": round(price, 2),
        },
        "trend": direction,
        "indicators": {
            "sma_20": round(price * 0.996, 2),
            "sma_50": round(price * 0.988, 2),
            "ema_20": round(price * 0.998, 2),
            "ema_50": round(price * 0.991, 2),
            "ema_200": round(price * 0.964, 2),
            "rsi_14": 71.4 if bullish else 28.6,
        },
        "rsi_condition": "overbought" if bullish else "oversold",
        "structure": {
            "swing": {
                "trend": direction,
                "latest_event": swing,
                "events": [
                    structure_event("BOS", direction, price * 0.961, 640),
                    structure_event("CHoCH", direction, price * 0.974, 310),
                    swing,
                ],
                "pivots": [
                    {
                        "index": 380,
                        "timestamp": ts(114),
                        "price": round(price * 0.988, 2),
                        "type": "high",
                        "label": "HH",
                    },
                    {
                        "index": 402,
                        "timestamp": ts(92),
                        "price": round(price * 0.975, 2),
                        "type": "low",
                        "label": "HL",
                    },
                ],
            },
            "internal": {
                "trend": "mixed",
                "latest_event": internal,
                "events": [
                    structure_event("BOS", direction, price * 0.997, 58),
                    internal,
                ],
                "pivots": [],
            },
        },
        # active_count is the true total; zones are the most recent slice.
        "fvg": {"active_count": 27, "zones": zones},
        "liquidity": {
            "equal_highs": [
                {
                    "price": round(price * 1.032, 2),
                    "touches": 3,
                    "points": [
                        {
                            "index": 431,
                            "timestamp": ts(180),
                            "price": round(price * 1.032, 2),
                        },
                        {
                            "index": 462,
                            "timestamp": ts(88),
                            "price": round(price * 1.0319, 2),
                        },
                        {
                            "index": 481,
                            "timestamp": ts(31),
                            "price": round(price * 1.0321, 2),
                        },
                    ],
                }
            ],
            "equal_lows": [
                {
                    "price": round(price * 0.9705, 2),
                    "touches": 2,
                    "points": [
                        {
                            "index": 409,
                            "timestamp": ts(240),
                            "price": round(price * 0.9705, 2),
                        },
                        {
                            "index": 455,
                            "timestamp": ts(102),
                            "price": round(price * 0.9704, 2),
                        },
                    ],
                }
            ],
            "buy_side_liquidity": [
                {
                    "type": "buy_side",
                    "price": round(price * 1.032, 2),
                    "source": "equal_highs",
                    "touches": 3,
                }
            ],
            "sell_side_liquidity": [
                {
                    "type": "sell_side",
                    "price": round(price * 0.9705, 2),
                    "source": "equal_lows",
                    "touches": 2,
                }
            ],
        },
        "confluence": {
            "bias": direction,
            "strength": "strong" if bullish else "moderate",
            "score": 4,
            "bullish_score": 4 if bullish else 1,
            "bearish_score": 1 if bullish else 4,
            "bullish_factors": [
                "Swing BOS bullish",
                "Price above EMA 50 and EMA 200",
                "Unmitigated demand FVG below price",
                "Sell-side liquidity swept",
            ]
            if bullish
            else ["Price reclaimed EMA 20"],
            "bearish_factors": ["RSI overbought at 71.4"]
            if bullish
            else [
                "Swing BOS bearish",
                "Price below EMA 50 and EMA 200",
                "Unmitigated supply FVG above price",
                "Buy-side liquidity swept",
            ],
            "conflicting_factors": [
                "Internal structure CHoCH opposes the swing trend"
            ],
            "latest_swing_event": swing,
            "latest_internal_event": internal,
            "selected_fvg": zones[1],
            "nearby_fvgs": zones,
            "nearest_buy_side_liquidity": {
                "type": "buy_side",
                "price": round(price * 1.032, 2),
                "source": "equal_highs",
                "touches": 3,
            },
            "nearest_sell_side_liquidity": {
                "type": "sell_side",
                "price": round(price * 0.9705, 2),
                "source": "equal_lows",
                "touches": 2,
            },
            "reasons": [
                f"Swing {direction} BOS at {price * 0.988:.2f}",
                "Confluence score 4/5",
            ],
        },
        "setup": {
            "setup": "LONG" if bullish else "SHORT",
            "direction": direction,
            "confidence": "high" if bullish else "moderate",
            "score": 4,
            "entry_zone": [round(entry_low, 2), round(entry_high, 2)],
            "entry_source": "unmitigated_fvg",
            "stop_loss": round(stop, 2),
            "stop_source": "below_swing_low",
            "targets": [round(price * 1.021, 2), round(target, 2)],
            "target_source": "buy_side_liquidity",
            "risk": round(risk, 2),
            "reward": round(reward, 2),
            "risk_reward": round(reward / risk, 2) if risk else None,
            "reasons": [f"Swing {direction} BOS confirmed"],
            "conflicts": ["Internal CHoCH opposes the swing trend"],
            "invalidated_if": f"price closes below {stop:.2f}",
        },
    }


def price_payload(ticker: str) -> dict:
    base = BASE_PRICES[ticker]
    # A little drift so a poll visibly refreshes.
    drift = random.uniform(-0.004, 0.004)

    return {
        "symbol": ticker,
        "currency": "usd",
        "price": round(base * (1 + drift), 6),
        "change_24h": round(random.uniform(-6.5, 6.5), 2),
        "volume_24h": round(base * random.uniform(1e5, 9e5), 2),
        "market_cap": round(base * random.uniform(1e7, 9e7), 2),
    }


ANALYSIS_RE = re.compile(r"^/api/analysis/([A-Za-z0-9]+)$")
PRICE_RE = re.compile(r"^/api/market/([A-Za-z0-9]+)/price$")
HISTORY_RE = re.compile(r"^/api/chat/([^/]+)/history$")

CONVERSATIONS: dict[str, list[dict]] = {}


class Handler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"
    flaky = False

    def log_message(self, fmt, *args):
        sys.stderr.write(f"  {self.command} {self.path} -> {args[1]}\n")

    def _cors(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")

    def _send(self, status: int, body: dict):
        # allow_nan=False on purpose: a NaN here would be the exact invalid-JSON
        # bug the real indicators.py fix guards against, and it must not slip
        # through the mock unnoticed.
        raw = json.dumps(body, allow_nan=False).encode()

        self.send_response(status)
        self._cors()
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)

    def do_OPTIONS(self):
        self.send_response(204)
        self._cors()
        self.send_header("Content-Length", "0")
        self.end_headers()

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path

        match = ANALYSIS_RE.match(path)
        if match:
            symbol = match.group(1).upper()
            query = parse_qs(parsed.query)
            timeframe = (query.get("timeframe") or ["1h"])[0]

            if timeframe not in TIMEFRAME_SECONDS:
                return self._send(
                    400, {"detail": f"Unsupported timeframe: {timeframe}"}
                )

            # A real analysis run is not instant.
            time.sleep(0.25)
            return self._send(200, analysis_payload(symbol, timeframe))

        match = PRICE_RE.match(path)
        if match:
            ticker = match.group(1).upper()

            if ticker not in BASE_PRICES:
                return self._send(400, {"detail": f"Unknown symbol: {ticker}"})

            if Handler.flaky and random.random() < 0.35:
                return self._send(
                    502, {"detail": "CoinGecko request failed (rate limited)"}
                )

            time.sleep(0.1)
            return self._send(200, price_payload(ticker))

        match = HISTORY_RE.match(path)
        if match:
            conversation_id = match.group(1)
            messages = CONVERSATIONS.get(conversation_id)

            if messages is None:
                return self._send(
                    404, {"detail": f"Conversation not found: {conversation_id}"}
                )

            return self._send(
                200,
                {
                    "conversation_id": conversation_id,
                    "message_count": len(messages),
                    "messages": messages,
                },
            )

        if path == "/health":
            return self._send(200, {"status": "ok"})

        self._send(404, {"detail": f"Not found: {path}"})

    def do_POST(self):
        if urlparse(self.path).path != "/api/chat":
            return self._send(404, {"detail": "Not found"})

        length = int(self.headers.get("Content-Length") or 0)
        try:
            body = json.loads(self.rfile.read(length) or b"{}")
        except json.JSONDecodeError:
            return self._send(400, {"detail": "Invalid JSON body"})

        question = (body.get("message") or "").strip()
        if not question:
            return self._send(400, {"detail": "message must not be empty"})

        conversation_id = body.get("conversation_id") or f"mock-{int(time.time())}"
        history = CONVERSATIONS.setdefault(conversation_id, [])

        now = str(datetime.now(timezone.utc).replace(microsecond=0))
        answer = (
            "Mock response. The real answer comes from the RAG chain over "
            f"Gemini, which this stub does not run.\n\nYou asked: {question}"
        )

        history.append({"role": "user", "content": question, "created_at": now})
        history.append({"role": "assistant", "content": answer, "created_at": now})

        time.sleep(0.5)
        self._send(
            200,
            {
                "conversation_id": conversation_id,
                "answer": answer,
                "sources": [
                    {
                        "text": "A fair value gap is an imbalance left by a "
                        "three-candle sequence where the middle candle's range "
                        "does not overlap its neighbours.",
                        "source": "smc-primer.pdf",
                        "page": 42,
                        "score": 0.8123,
                    }
                ],
            },
        )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument(
        "--flaky",
        action="store_true",
        help="fail ~35%% of price requests, imitating a CoinGecko rate limit",
    )
    args = parser.parse_args()

    Handler.flaky = args.flaky
    random.seed()

    server = ThreadingHTTPServer(("127.0.0.1", args.port), Handler)
    print(f"mock backend on http://127.0.0.1:{args.port} (flaky={args.flaky})")

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nstopping")
    finally:
        server.server_close()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
