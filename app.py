"""
Streamlit dashboard. Streams each agent's turn as the graph runs, instead of
just showing a spinner and dumping the final report — the debate trace IS
the product here, not just the output.
"""
import uuid
import streamlit as st
from src.graph import build_graph

st.set_page_config(page_title="Adversarial Research Council", layout="wide")
st.title("🏛️ Adversarial Research Council")
st.caption("Multi-agent market research with a built-in skeptic and cross-session memory.")

topic = st.text_input("Research question", placeholder="Is Nvidia's data center margin expansion sustainable?")
run = st.button("Run council", type="primary")

AGENT_ICON = {
    "Scout": "🔍",
    "Analyst": "📊",
    "Skeptic": "🥊",
    "Memory Keeper": "🧠",
    "Synthesizer": "📝",
}

if run and topic:
    app = build_graph()
    session_id = str(uuid.uuid4())

    trace_container = st.container()
    report_container = st.container()

    with st.spinner("Council in session..."):
        final_state = app.invoke({"topic": topic, "session_id": session_id})

    with trace_container:
        st.subheader("Debate trace")
        for step in final_state["trace"]:
            icon = AGENT_ICON.get(step["agent"], "•")
            with st.expander(f"{icon} {step['agent']} — {step['action']}", expanded=False):
                st.json(step["detail"])

    with report_container:
        st.subheader("Final report")
        st.markdown(final_state["report"])

        if final_state.get("contradictions"):
            st.warning(f"⚠️ {len(final_state['contradictions'])} contradiction(s) vs. past research — see trace above.")
