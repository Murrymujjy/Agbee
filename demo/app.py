"""
Local test-run UI for Àgbẹ̀ — NOT part of the ADTC submission.

The evaluator only runs metadata.json + download_model.sh + llama.cpp via
adtc-profiler. This app exists purely so the team can see the pipeline
working end-to-end (Router -> Retriever/KB -> Engine) while individual
tracks are still stubs, and keep using it as each stub gets swapped for
the real thing.

Run:
    pip install -r requirements.txt
    streamlit run demo/app.py
"""
import sys
from pathlib import Path

import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.router.interfaces import RouterStub
from src.retrieval.interfaces import StubRetriever
from src.kb.interfaces import StubKB
from src.engine.interfaces import StubEngine

st.set_page_config(page_title="Àgbẹ̀ — local test", page_icon="🌾", layout="centered")

# ---------------------------------------------------------------------------
# Component wiring — swap Stub* for the real class as each track finishes.
# Nothing else in this file needs to change when that happens, because
# everything is built against the frozen interfaces.
# ---------------------------------------------------------------------------
COMPONENTS = {
    "router": RouterStub(),       # Track C — swap for real intent classifier
    "retriever": StubRetriever(), # Track A — swap for BM25 + embedding fusion
    "kb": StubKB(),                # Track A — swap for real SQLite-backed KB
    "engine": StubEngine(),        # Track B — swap for real llama.cpp server client
}
IS_STUB = {k: v.__class__.__name__.startswith("Stub") for k, v in COMPONENTS.items()}

TIER_LABEL = {
    "A": "Tier A — exact fact (DB lookup)",
    "B": "Tier B — explanation/diagnosis (retrieval)",
    "C": "Tier C — multi-step + calculation",
    "D": "Tier D — refused / out of scope",
}

st.title("🌾 Àgbẹ̀ — local pipeline test")
st.caption(
    "Team testing tool only — not the graded artifact. The ADTC evaluator runs "
    "your model through `llama.cpp` + `adtc-profiler`, not this app."
)

with st.sidebar:
    st.subheader("Component status")
    for name, is_stub in IS_STUB.items():
        icon = "🟡 stub" if is_stub else "🟢 real"
        st.write(f"**{name}**: {icon}")
    if any(IS_STUB.values()):
        st.info(
            "Answers below are canned stub output until a track swaps its "
            "component in `demo/app.py`'s COMPONENTS dict for the real class."
        )
    st.divider()
    show_internals = st.checkbox("Show routing internals", value=True)

if "history" not in st.session_state:
    st.session_state.history = []

question = st.chat_input("Ask a farming question (English, Pidgin, Yoruba, Hausa)...")

for turn in st.session_state.history:
    with st.chat_message("user"):
        st.write(turn["question"])
    with st.chat_message("assistant"):
        st.write(turn["answer_text"])
        st.caption(f"Source: {turn['source']}")

if question:
    with st.chat_message("user"):
        st.write(question)

    route = COMPONENTS["router"].classify(question)

    if route.tier == "D":
        answer_text = "I don't have reliable information on this — please contact your local extension officer."
        source = "N/A — refused"
        internals = {"route": route.__dict__}

    elif route.tier == "A":
        rows = COMPONENTS["kb"].query(route.intent, route.slots)
        facts = "; ".join(str(r.data) for r in rows)
        gen = COMPONENTS["engine"].generate(
            prompt=f"Phrase this fact for a farmer, do not add anything not stated: {facts}",
            grammar=None,
        )
        answer_text = gen["text"]
        source = rows[0].source_id if rows else "N/A"
        internals = {"route": route.__dict__, "kb_rows": [r.__dict__ for r in rows], "engine_timings": gen["timings"]}

    else:  # Tier B or C — retrieval path (Tier C calculator step omitted from this demo skeleton)
        passages = COMPONENTS["retriever"].search(question, k=3)
        context = "\n".join(p.text for p in passages)
        gen = COMPONENTS["engine"].generate(
            prompt=f"Answer using only this context, cite the source: {context}\n\nQuestion: {question}",
            grammar=None,
        )
        answer_text = gen["text"]
        source = passages[0].source_id if passages else "N/A"
        internals = {"route": route.__dict__, "passages": [p.__dict__ for p in passages], "engine_timings": gen["timings"]}

    with st.chat_message("assistant"):
        st.markdown(f"**{TIER_LABEL[route.tier]}**")
        st.write(answer_text)
        st.caption(f"Source: {source}")
        if show_internals:
            with st.expander("Routing internals"):
                st.json(internals)

    st.session_state.history.append({"question": question, "answer_text": answer_text, "source": source})
