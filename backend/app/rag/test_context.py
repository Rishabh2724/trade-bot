"""
Offline test for conversation-aware market context.

Stubs Pinecone / Gemini / dotenv so rag_chain imports without API keys
or network, then simulates the section-23 test plan by driving
build_live_market_context with the conversation history that would exist
at each turn. analyze_market is monkeypatched to capture the resolved
(symbol, timeframe) instead of hitting Binance.
"""

import os
import sys
import types


# ------------------------------------------------------------
# Stub heavy / network dependencies BEFORE importing rag_chain
# ------------------------------------------------------------

os.environ.setdefault("PINECONE_API_KEY", "test")
os.environ.setdefault("PINECONE_INDEX_NAME", "test")
os.environ.setdefault("GEMINI_API_KEY", "test")


def _stub_module(name, attrs):
    module = types.ModuleType(name)
    for key, value in attrs.items():
        setattr(module, key, value)
    sys.modules[name] = module


class _Dummy:
    def __init__(self, *args, **kwargs):
        pass

    def __call__(self, *args, **kwargs):
        return self

    def Index(self, *args, **kwargs):
        return self


_stub_module("dotenv", {"load_dotenv": lambda *a, **k: None})
_stub_module(
    "langchain_google_genai",
    {
        "GoogleGenerativeAIEmbeddings": _Dummy,
        "ChatGoogleGenerativeAI": _Dummy,
    },
)
_stub_module("pinecone", {"Pinecone": _Dummy})

# langchain_core.prompts.ChatPromptTemplate.from_template(...)
_prompts = types.ModuleType("langchain_core.prompts")


class _PromptStub:
    @classmethod
    def from_template(cls, *a, **k):
        return cls()


_prompts.ChatPromptTemplate = _PromptStub
sys.modules["langchain_core"] = types.ModuleType("langchain_core")
sys.modules["langchain_core.prompts"] = _prompts

# Ensure `import app...` resolves from the backend/ root.
sys.path.insert(
    0,
    os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")),
)

# Stub the analysis service so importing rag_chain does not pull in the
# binance -> requests dependency chain (not installed in this env).
_analysis_service = types.ModuleType("app.services.analysis_service")
_analysis_service.analyze_market = lambda *a, **k: {}
sys.modules["app.services.analysis_service"] = _analysis_service

from app.rag import rag_chain  # noqa: E402


# ------------------------------------------------------------
# Capture what symbol/timeframe the pipeline resolves to
# ------------------------------------------------------------

captured = {}


def fake_analyze_market(symbol, timeframe, limit=500):
    captured["symbol"] = symbol
    captured["timeframe"] = timeframe
    # Minimal shape so build_live_market_context does not crash.
    return {
        "market": {"symbol": symbol, "timeframe": timeframe},
        "trend": "n/a",
    }


rag_chain.analyze_market = fake_analyze_market


def resolve(question, history):
    captured.clear()
    result = rag_chain.build_live_market_context(question, history)
    return captured.get("symbol"), captured.get("timeframe"), result


def build_history(turns):
    """turns: list of (role, content) -> history string as the chain builds it."""
    if not turns:
        return "No previous conversation."
    return "\n\n".join(f"{r.upper()}: {c}" for r, c in turns)


# ------------------------------------------------------------
# Section 23 test plan
# ------------------------------------------------------------

ANSWER = "[assistant analysis text]"

turns = []  # accumulated (role, content) BEFORE current question
failures = 0


def check(label, question, expect_symbol, expect_tf):
    global failures
    history = build_history(turns)
    sym, tf, ctx = resolve(question, history)
    ok = sym == expect_symbol and tf == expect_tf
    status = "PASS" if ok else "FAIL"
    if not ok:
        failures += 1
    print(f"[{status}] {label}: got symbol={sym} tf={tf} (want {expect_symbol} {expect_tf})")
    # Simulate storage of this turn for subsequent history.
    turns.append(("user", question))
    turns.append(("assistant", f"{ANSWER} {sym} {tf}"))


check("T1 Analyze BTCUSDT 15m", "Analyze BTCUSDT on the 15m timeframe.", "BTCUSDT", "15m")
check("T2 What about the FVG?", "What about the FVG?", "BTCUSDT", "15m")
check("T3 Where is liquidity?", "Where is liquidity?", "BTCUSDT", "15m")
check("T4 Is there a long setup?", "Is there a long setup?", "BTCUSDT", "15m")
check("T5 Now analyze ETH 1h", "Now analyze ETH on the 1h timeframe.", "ETHUSDT", "1h")
check("T6 What about its FVG?", "What about its FVG?", "ETHUSDT", "1h")


# ------------------------------------------------------------
# Symbol resolution from a single question (no history)
# ------------------------------------------------------------

SYMBOL_CASES = [
    # Tickers
    ("btc price", "BTCUSDT"),
    ("What is the price of BTC?", "BTCUSDT"),
    ("BTCUSDT price", "BTCUSDT"),
    ("btc price in usd", "BTCUSDT"),
    ("current price of ETH", "ETHUSDT"),
    # Full coin names must work the same as tickers.
    ("bitcoin price", "BTCUSDT"),
    ("What's the current Bitcoin price?", "BTCUSDT"),
    ("price of ethereum", "ETHUSDT"),
    ("solana price", "SOLUSDT"),
    ("dogecoin trend", "DOGEUSDT"),
    # Longest alias wins.
    ("ethereum classic price", "ETCUSDT"),
    # Tickers that are English words only count when uppercase.
    ("Explain FVG, BOS, CHoCH etc. in trading", None),
    ("ETC price", "ETCUSDT"),
    ("is price near support?", None),
    ("NEAR price", "NEARUSDT"),
    # Nothing to resolve.
    ("what is the price?", None),
]

print()

for question, expected in SYMBOL_CASES:
    got = rag_chain.extract_symbol(question)
    ok = got == expected
    if not ok:
        failures += 1
    print(
        f"[{'PASS' if ok else 'FAIL'}] extract_symbol({question!r}) "
        f"-> {got} (want {expected})"
    )


# ------------------------------------------------------------
# Non-market query should not trigger analysis
# ------------------------------------------------------------

_, _, ctx = resolve("Explain what a CHoCH is.", build_history(turns))
# "choch" is a market keyword, so this DOES trigger — check a truly generic one.
sym_g, tf_g, ctx_g = resolve("Hello, who are you?", "No previous conversation.")
if sym_g is None and ctx_g == "No live market analysis requested.":
    print("[PASS] Generic greeting: no analysis triggered")
else:
    print(f"[FAIL] Generic greeting triggered analysis: {sym_g} {tf_g}")
    failures += 1

print()
print("RESULT:", "ALL PASS" if failures == 0 else f"{failures} FAILURE(S)")
sys.exit(1 if failures else 0)
