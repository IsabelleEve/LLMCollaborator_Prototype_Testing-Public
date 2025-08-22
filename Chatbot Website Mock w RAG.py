# app.py
# MOST Collaborator (Pilot) – MULTI-AGENT (ChatGPT), styled UI
# streamlit run "C:\\Users\\isscott\\OneDrive - ORYGEN\\Documents\\Grant Planning\\Welcome Trust Generative AI Grant\\Protype Mocks\\Chatbot Website Mock w RAG.py"

import json
import re
import streamlit as st
from openai import OpenAI
from pathlib import Path
BASE_DIR = Path(__file__).parent

# ==================== Necessary for MOST logo integration ====================
import base64
BASE_DIR = Path(__file__).parent

def svg_data_uri(filename: str) -> str | None:
    p = (BASE_DIR / filename)
    if not p.is_file():
        return None
    b64 = base64.b64encode(p.read_bytes()).decode("utf-8")
    return f"data:image/svg+xml;base64,{b64}"

# add agent image
AGENT_AVATAR = str(BASE_DIR / "MOST_label.png")   # your AI agent image
USER_AVATAR  = str(BASE_DIR / "yp_pic.png")       # your YP/user image

# ==================== CONFIG: key loaded from file ====================
MODEL_NAME = "gpt-4o-mini"  # fast/cheap; change if you like
client = OpenAI(api_key=(Path(__file__).parent / "openai_key.txt").read_text().strip())
# ======================================================================

# ---------- Page & "brand" ----------
st.set_page_config(page_title="MOST • Collaborator", page_icon="💬", layout="wide", initial_sidebar_state="expanded")

# --- Simple password gate ---
def _require_password():
    if st.session_state.get("auth_ok"):
        return
    with st.sidebar:
        st.subheader("Locked")
        pw = st.text_input("Password", type="password", placeholder="Enter password")
        if pw == "XXXXX":
            st.session_state["auth_ok"] = True
        elif pw:  # wrong non-empty input
            st.error("Incorrect password")
    if not st.session_state.get("auth_ok"):
        st.stop()  # don't run the rest of the app until unlocked

_require_password()

# ---- Brand tokens (tuned to MOST-like look) ----
PRIMARY       = "#4F46E5"
PRIMARY_DARK  = "#4338CA"
ACCENT        = "#06B6D4"
ACCENT_2      = "#22C55E"
INK           = "#111827"
MUTED         = "#6B7280"
BG            = "#F9FAFB"
CARD          = "#FFFFFF"
RING          = "#E5E7EB"

# ---------- Light CSS polish ----------
st.markdown(
    f"""
    <style>
      @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@400;600;700&display=swap');

      html, body, [class*="stApp"] {{
        background: {BG};
        color: {INK};
        font-family: "Poppins", system-ui, -apple-system, Segoe UI, Roboto, Arial, sans-serif;
      }}

      #MainMenu {{visibility: hidden;}}
      footer {{visibility: hidden;}}
      header {{visibility: hidden;}}

      .brand {{
        font-weight: 700; letter-spacing: .02em; font-size: .95rem; color: {PRIMARY};
        text-transform: uppercase; margin-bottom: 6px;
      }}

      .hero {{
        background: linear-gradient(180deg, rgba(79,70,229,0.08), rgba(6,182,212,0.08));
        border: 1px solid {RING};
        border-radius: 20px;
        padding: 18px 20px;
        margin-bottom: 12px;
        box-shadow: 0 8px 20px rgba(15, 23, 42, 0.05);
      }}
      .hero h1 {{ margin: 0 0 4px 0; font-size: 1.28rem; font-weight: 700; color: {INK}; }}
      .hero p  {{ margin: 0; color: {MUTED}; }}
      .hero .logo {{ height: 28px; border-radius: 6px; vertical-align: middle; }}

      section[data-testid="stSidebar"] > div {{ background: {BG}; }}
      .sidecard {{
        background: {CARD};
        border: 1px solid {RING};
        border-radius: 16px;
        padding: 14px;
        margin-bottom: 10px;
        box-shadow: 0 4px 12px rgba(15, 23, 42, 0.04);
      }}
      .chip {{
        display:inline-block; padding:4px 10px; border-radius:999px;
        background: rgba(79,70,229,0.08);
        color:{PRIMARY};
        font-size:12px; margin-right:6px;
        border:1px solid {RING};
      }}
      .small {{ color:{MUTED}; font-size: 12px; }}

      .stChatMessage .stMarkdown p {{ margin-bottom: 0; }}
      .stChatMessage[data-testid="stChatMessage"] {{
        background: {CARD};
        border: 1px solid {RING};
        border-radius: 16px;
        padding: 10px 12px;
        box-shadow: 0 4px 12px rgba(15, 23, 42, 0.04);
      }}

      .stButton>button {{
        border-radius: 999px;
        padding: 10px 16px;
        border: 1px solid {RING};
        background: white;
        color: {INK};
        transition: all .15s ease;
      }}
      .stButton>button:hover {{ background: #F1F5F9; transform: translateY(-1px); }}

      .cta .stButton>button {{
        background: linear-gradient(90deg, {PRIMARY}, {ACCENT});
        color: white; border-color: {PRIMARY_DARK};
        box-shadow: 0 6px 14px rgba(79,70,229,.18);
      }}
      .cta .stButton>button:hover {{
        background: linear-gradient(90deg, {PRIMARY_DARK}, {ACCENT});
      }}

      .success-badge {{
        display:inline-block; padding:4px 10px; border-radius:999px;
        background: rgba(34,197,94,0.12);
        color:#065F46; border:1px solid #D1FAE5; font-size:12px;
      }}

      /* --- trace/status chip --- */
      .trace {{
        display:inline-block; padding:4px 8px; border-radius:8px;
        background:#EEF2FF; color:#3730A3; border:1px solid #E5E7EB; font-size:12px;
      }}

      a, a:visited {{ color: {PRIMARY}; text-decoration: none; }}
      a:hover {{ text-decoration: underline; }}
    </style>
    """,
    unsafe_allow_html=True,
)

# ---------- Demo data ----------
ASSIGNED = {
    "name": "Fundamentals",
    "why": "A gentle first step if you haven’t done therapy before; builds core skills.",
    "format": "Journey",
    "image": "test_img.png"  # file in same folder
}
CATALOGUE = [
    {"name":"Starter Skills",    "elements":["psychoeducation","BA-starter"], "format":"modular", "burden":"~10m/day"},
    {"name":"Daily Micro-steps", "elements":["psychoeducation","BA-starter"], "format":"micro",   "burden":"~5m/day"},
    {"name":"Fundamentals-Lite", "elements":["psychoeducation","BA-starter"], "format":"course",  "burden":"~7m/day"},
]

# --- Onboarding: 3 journeys + simple rules ---
JOURNEYS = {
    "fundamentals": {
        "name": "Fundamentals",
        "why": "A gentle first step if you haven’t done therapy before; builds core skills.",
        "format": "Journey",
        "burden": "~15m/day",
        "required_elements": ["psychoeducation", "BA-starter"],
        "image": "test_img.png",
    },
    "starter_skills": {
        "name": "Starter Skills",
        "why": "Pick-and-mix modules; easier to dip in/out if you want flexibility.",
        "format": "Modular",
        "burden": "~10m/day",
        "required_elements": ["psychoeducation", "BA-starter"],
        "image": "test_img.png",
    },
    "micro_steps": {
        "name": "Daily Micro-steps",
        "why": "Tiny daily actions for low time/energy days; same core skills at a lighter pace.",
        "format": "Micro",
        "burden": "~5m/day",
        "required_elements": ["psychoeducation", "BA-starter"],
        "image": "test_img.png",
    },
}

def assign_journey(therapy_hist: str, capacity: str, style: str) -> dict:
    if capacity == "Low" or style == "Tiny daily steps":
        return JOURNEYS["micro_steps"]
    if therapy_hist == "No" and style == "Step-by-step course":
        return JOURNEYS["fundamentals"]
    return JOURNEYS["starter_skills"]

# ---------- Prompts (3 lightweight agents) ----------
DIV_SYS = """
You are the Divergence Checker and Router for MOST.
Return STRICT JSON with EXACTLY these keys:
{"diverged":true|false,"understands_why":true|false,"next":"accept|explain|resolve"}

Interpret user_text and route using this priority order:

1) If the user explicitly asks for an explanation (e.g., "please explain", "why this", "what is it", "I don't understand"),
   then: understands_why=false; diverged = mention of not starting now? (true if they say later/not now; else false); next="explain".

2) If the user indicates capacity/context or preference barriers (e.g., "not in the mood", "too tired", "no time", "later", "busy",
   "overwhelmed", "can't today", "prefer something lighter/different", "too long/hard", "micro steps instead"),
   then: diverged=true; understands_why=true; next="resolve".

3) If the user clearly agrees to start now (e.g., "ok let's start", "ready to begin", "start now"),
   then: diverged=false; understands_why=true; next="accept".

4) If the user seems unsure about the rationale but does not refuse to start,
   then: diverged=false; understands_why=false; next="explain".

5) Otherwise, default to: diverged=false; understands_why=true; next="accept".

Notes:
- "diverged" means not starting now (postpone/navigate away/talk instead).
- Treat capacity/mood/time/schedule/energy/tech-access issues as context barriers.
- Output JSON only with those three keys and booleans for the first two.
"""

EXP_SYS = """
You are the Explainer for MOST. The user doesn't yet understand why the journey was recommended.
Return STRICT JSON: {"message": str}
Use the field user_text to briefly reflect back the user's reason in a warm, validating way (one short clause), then give a 1–3 sentence rationale and ONE short question.
Youth-friendly, warm, brief.
Context: 
The Fundamentals Journey on MOST will teach you the essentials of good mental health. It will help you explore how your thoughts, emotions, and behaviours are connected to your mood. 
It will also provide you with practical strategies to feel better. You will learn how to handle real-life situations and develop your ability to stay present and manage stress.
You’ll be able to create your own personalised toolkit of these strategies within MOST so you can access them at the tap of a button.
The Fundamentals Journey is made up of five tracks, each filled with fun, interactive activities that you can explore at your own pace.
These short activities are designed to be easy to understand and apply to real life.
They combine skills and strategies from evidence-based frameworks like Cognitive Behavioural Therapy (CBT), the Unified Protocol (UP), and Acceptance and Commitment Therapy (ACT).
These frameworks help guide therapists in supporting people to manage their mental health, and now you get to learn and use them too.
As you move through the journey, you’ll get to see our MOST comic characters work through their own challenges.
You’ll see how they put the strategies you’re learning into action to overcome obstacles and feel better.
"""

RES_SYS = """
You are the Resolver for MOST. The user understands why but prefers not to start now.
Return STRICT JSON:
{"message": str, "options":[{"name":str,"why_fit":str,"format":str,"burden":str}]}
Use user_text to tailor tone and options (e.g., if "tired/busy/overwhelmed", prefer lighter/shorter options). Offer up to 3 alternatives that KEEP all required_elements but adjust format/burden/tone.
Brief, 1–2 sentences total in "message".
"""



# --- NEW: RAG helpers (local YAML) ---
# Change GUIDE_PATH to a list of paths for your YAML files
GUIDE_PATHS = [
    Path(BASE_DIR / "dicucom.yaml"),
    Path(BASE_DIR / "dicucom.yaml") #DCP_Guidelines.yaml")
]

def _load_guideline_chunks(paths: list):
    """Parse a simple YAML 'chunks:' list without requiring PyYAML."""
    all_chunks = []
    # Loop through each path in the provided list
    for path in paths:
        if not path.is_file():
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        # Grab each '- id: ...' block
        rx = re.compile(r'(?m)^\s*-\s+id:\s*(?P<id>[^\n]+)\n(?P<body>.*?)(?=^\s*-\s+id:|\Z)', re.S)
        chunks = []
        for m in rx.finditer(text):
            cid = m.group("id").strip()
            body = m.group("body")
            # Try to extract a short summary if present
            sm = re.search(r'summary:\s*(?:>\s*)?(?P<sum>.*?)(?:\n\s*[a-z_]+:|\Z)', body, re.S | re.I)
            summary = sm.group("sum").strip() if sm else ""
            kp = re.findall(r'^\s*-\s*(.+)$', body, re.M)
            chunk_text = f"ID: {cid}\n{summary}\n" + ("\n".join(kp) if kp else "")
            chunks.append({"id": cid, "text": chunk_text.lower(), "raw": chunk_text})
        all_chunks.extend(chunks)  # Add chunks from the current file to the main list
    return all_chunks

_GUIDE_CHUNKS = _load_guideline_chunks(GUIDE_PATHS)

def _retrieve_guideline_snippets(query_text: str, k: int = 3) -> str:
    """Naive keyword match over local YAML chunks; returns up to k chunks' raw text."""
    if not _GUIDE_CHUNKS:
        return ""
    q = (query_text or "").lower()
    # Basic tokenisation; ignore very short tokens
    terms = [t for t in re.findall(r"[a-z]{4,}", q)]
    def score(c):
        return sum(c["text"].count(t) for t in terms) + (1 if not terms else 0)
    ranked = sorted(_GUIDE_CHUNKS, key=score, reverse=True)[:max(1, k)]
    return "\n---\n".join(c["raw"] for c in ranked)

# NEW: Clinician summariser (updated to accept guideline_snippets)
CLIN_SYS = """
You are the Clinician Summariser for MOST.
Return STRICT JSON: {"summary": str}
Summarise for a clinician using:
- onboarding (therapy_hist, capacity, style)
- assigned journey (name, why, format, burden, required_elements)
- recent chat excerpt (last turns)
- guideline_snippets (RAG-selected from BPS DCP formulation guidance)

Write ≤120 words, bullet-ish lines under headings:
Context; Current stance; Suggested next steps.
Anchor “Suggested next steps” in the guideline_snippets (e.g., collaborative, meaning-focused, iterative formulation). If helpful, include bracketed refs like [ID: …].
Paraphrase; no sensitive verbatim quotes. Youth-friendly tone, but clinician-facing.
Then provide information relative to what we know about 
Presenting problem(s): Initial signs, symptoms or other difficulties that are clinically important for the young person. (e.g. low mood)
Predisposing factors: Aspects of the young person’s background that make him/her susceptible to presenting with the given problems (e.g. history of mental illness in family)
Precipitating factors: Immediate issues or events that have caused the young person to present with or experience these problems or symptoms at this time (e.g. recent life experiences/stressors, bullying etc.)
Perpetuating factors: Factors that cause the young person’s symptoms/problems to continue or to progressively get worse (e.g. conflict in home, low social support, poor coping strategies, bullying)
Protective factors: Factors that help to improve the young person’s situation or symptoms (e.g. supportive relationships, friendships and strengths)
"""

def _json_call(system_prompt: str, user_payload: dict) -> dict:
    resp = client.chat.completions.create(
        model=MODEL_NAME,
        temperature=0,
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": json.dumps(user_payload)}
        ],
    )
    return json.loads(resp.choices[0].message.content)

def call_divergence_checker(user_text: str, assigned: dict) -> dict:
    return _json_call(DIV_SYS, {"user_text": user_text, "assigned": assigned})

def call_explainer(assigned: dict, user_text: str) -> dict:
    return _json_call(EXP_SYS, {"assigned": assigned, "user_text": user_text})

def call_resolver(assigned: dict, catalogue: list, user_text: str) -> dict:
    return _json_call(RES_SYS, {"assigned": assigned, "catalogue": catalogue[:6], "user_text": user_text})

def call_clinician_summariser(assigned: dict, onboarding: dict, chat_excerpt: str, guideline_snippets: str) -> dict:
    return _json_call(CLIN_SYS, {
        "assigned": assigned,
        "onboarding": onboarding,
        "chat_excerpt": chat_excerpt,
        "guideline_snippets": guideline_snippets
    })

# ---------- tiny helpers ----------
def push_trace(label: str, **info):
    detail = " ".join(f"{k}={v}" for k, v in info.items() if v is not None)
    html = f"<span class='trace'>state: {label}{(' — ' + detail) if detail else ''}</span>"
    st.session_state.chat.append(("assistant", html))
    with st.chat_message("assistant", avatar=AGENT_AVATAR):
        st.markdown(html, unsafe_allow_html=True)

def strip_tags(s: str) -> str:
    return re.sub(r"<[^>]+>", "", s or "")

# ---------- Header ----------
logo_uri = svg_data_uri("MOST_img.svg")  # optional SVG; falls back to text if missing
st.markdown(
    f"""
    <div class="hero">
      <div style="display:flex;align-items:center;gap:10px;margin-bottom:6px">
        {f'<img class="logo" src="{logo_uri}" alt="MOST Collaborator logo"/>' if logo_uri else '<div class="brand">MOST</div>'}
      </div>
      <h1>MOST Collaborator</h1>
      <p>Just got a journey? I can explain why it fits, adjust the plan, or suggest a lighter alternative.</p>
    </div>
    """,
    unsafe_allow_html=True,
)

# ---------- Right panel placeholder (clinician summary) ----------
col_main, col_right = st.columns([2, 1])
with col_right:
    if st.session_state.get("clinician_summary"):
        st.subheader("Clinician summary")
        st.markdown(st.session_state["clinician_summary"])

# ---------- Onboarding (3 questions) ----------
with col_main:
    if "assigned" not in st.session_state:
        with st.container():
            st.subheader("Quick start")
            st.caption("Answer 3 quick questions so I can suggest the best starting journey.")

            with st.form("onboarding"):
                q1 = st.radio(
                    "Have you done therapy before?",
                    ["No", "Some/previous", "Currently in therapy"],
                    index=0,
                )
                q2 = st.radio(
                    "How much time/energy do you have right now?",
                    ["Low", "Medium", "High"],
                    index=1,
                )
                q3 = st.radio(
                    "What style suits you today?",
                    ["Step-by-step course", "Pick-and-mix modules", "Tiny daily steps"],
                    index=0,
                )
                submitted = st.form_submit_button("See my recommendation")

            if submitted:
                st.session_state.assigned = assign_journey(q1, q2, q3)
                st.session_state.onboard_data = {"therapy_hist": q1, "capacity": q2, "style": q3}  # NEW store onboarding
                st.markdown(
                    f"""<div class="sidecard"><div style="font-weight:700;color:{INK}">{st.session_state.assigned['name']}</div>
                    <div class="small" style="color:{MUTED}">{st.session_state.assigned['why']}</div>
                    <div style="margin-top:6px">
                    <span class="chip">{'</span> <span class="chip">'.join(st.session_state.assigned.get('required_elements', []))}</span></div></div>""",
                    unsafe_allow_html=True
                )
                st.button(f"Start {st.session_state.assigned['name']} →", use_container_width=True)
                st.success(f"Recommended: {st.session_state.assigned['name']}")

# If onboarding ran, override ASSIGNED used by the rest of the app
if "assigned" in st.session_state:
    ASSIGNED = st.session_state.assigned

# ---------- Sidebar ----------
with st.sidebar:
    st.markdown('<div class="sidecard">', unsafe_allow_html=True)

    # journey image
    img_name = ASSIGNED.get("image", "")
    img_path = (BASE_DIR / img_name) if img_name else None
    if img_path and img_path.is_file():
        st.image(str(img_path), use_container_width=True)
    else:
        st.caption(f"Image not found at: {img_path}")

    st.subheader("Recommended therapy journey")
    st.markdown(f"**{ASSIGNED['name']}**")

    # "Required" chips area (simple string list)
    req = ASSIGNED.get("required_elements", [])
    chips_html = " ".join(f"<span class='chip'>{e}</span>" for e in req)
    st.markdown(f"<span class='chip'>Required</span> {chips_html}", unsafe_allow_html=True)

    st.markdown(f"<div style='margin-top:8px;color:{MUTED};'>{ASSIGNED['why']}</div>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

    if st.button("Change my recommendation"):
        if "assigned" in st.session_state:
            del st.session_state.assigned
        if "onboard_data" in st.session_state:
            del st.session_state.onboard_data
        st.experimental_rerun()

    # --- NEW: Finish -> Clinician summary (with RAG)
    if st.button("Finish • Generate clinician summary", type="primary", use_container_width=True):
        # Build a short chat excerpt (last 20 turns)
        turns = st.session_state.get("chat", [])[-20:]
        chat_excerpt = "\n".join(f"{r}: {strip_tags(m)}" for r, m in turns)

        onboarding = st.session_state.get("onboard_data", {})
        # RAG: retrieve top guideline snippets based on all available context
        query_text = " ".join([
            json.dumps(onboarding, ensure_ascii=False),
            json.dumps(ASSIGNED, ensure_ascii=False),
            chat_excerpt or ""
        ])
        guideline_snippets = _retrieve_guideline_snippets(query_text, k=3)

        try:
            out = call_clinician_summariser(ASSIGNED, onboarding, chat_excerpt, guideline_snippets)
            st.session_state.clinician_summary = out.get("summary", "—")
            push_trace("clinician_summary_ready", model=MODEL_NAME)
        except Exception as e:
            st.session_state.clinician_summary = f"_Could not generate summary: {e}_"

# ---------- Chat state ----------
if "chat" not in st.session_state:
    st.session_state.chat = []
if "picked" not in st.session_state:
    st.session_state.picked = None

# ---------- Render history ----------
with col_main:
    for role, msg in st.session_state.chat:
        av = AGENT_AVATAR if role == "assistant" else USER_AVATAR
        with st.chat_message(role, avatar=av):
            st.markdown(msg)

# ---------- Input ----------
with col_main:
    user_msg = st.chat_input("Ask about the journey, or say if you'd like to try something else…")

# ---------- Orchestration (multi-agent) ----------
if user_msg:
    st.session_state.chat.append(("user", user_msg))
    with col_main:
        with st.chat_message("user", avatar=USER_AVATAR):
            st.markdown(user_msg)

    try:
        gate = call_divergence_checker(user_msg, ASSIGNED)
    except Exception:
        bot_text = f"```json\n{json.dumps({'error':'divergence_checker_failed'}, indent=2)}\n```"
        st.session_state.chat.append(("assistant", bot_text))
        with col_main:
            with st.chat_message("assistant", avatar=AGENT_AVATAR): st.markdown(bot_text)
        gate = {"next":"accept"}

    action = gate.get("next", "accept")

    # --- trace: divergence decision ---
    push_trace("divergence_check", model=MODEL_NAME, next=action)

    if action == "accept":
        push_trace("accept", model=MODEL_NAME)
        bot_text = "Great — want to start now? I can keep the pace flexible if you like."
        st.session_state.chat.append(("assistant", bot_text))
        with col_main:
            with st.chat_message("assistant", avatar=AGENT_AVATAR):
                st.markdown(bot_text)
                with st.container():
                    st.markdown('<div class="cta">', unsafe_allow_html=True)
                    st.button("Start Fundamentals →", use_container_width=True)
                    st.markdown("</div>", unsafe_allow_html=True)

    elif action == "explain":
        push_trace("explain", model=MODEL_NAME)
        try:
            out = call_explainer(ASSIGNED, user_msg)
            bot_text = out.get(
                "message",
                "This was suggested to build core skills. What makes it feel not right — time, structure, or something else?"
            )
        except Exception:
            bot_text = ("This was suggested to build core skills. "
                        "What makes it feel not right — time, structure, or something else?")
        st.session_state.chat.append(("assistant", bot_text))
        with col_main:
            with st.chat_message("assistant", avatar=AGENT_AVATAR):
                st.markdown(bot_text)

    elif action == "resolve":
        push_trace("resolver", model=MODEL_NAME)
        try:
            out = call_resolver(ASSIGNED, CATALOGUE, user_msg)
            bot_text = out.get("message", "Would any of these fit better right now?")
            options = out.get("options", [])
        except Exception:
            bot_text = "Would any of these fit better right now?"
            options = []
        st.session_state.chat.append(("assistant", bot_text))
        with col_main:
            with st.chat_message("assistant", avatar=AGENT_AVATAR):
                st.markdown(bot_text)
                cols = st.columns(len(options)) if len(options) > 1 else [st]
                for i, (col, o) in enumerate(zip(cols, options)):
                    with col:
                        name=o.get("name",""); fmt=o.get("format",""); brd=o.get("burden",""); why=o.get("why_fit","")
                        st.markdown(f"**{name}**  \n_{fmt} · {brd}_")
                        st.caption(why)
                        if st.button(f"Try {name}", key=f"opt_{i}"):
                            st.session_state.picked = name

    if st.session_state.get("picked"):
        picked_msg = f"<span class='success-badge'>Selected: {st.session_state.picked}</span>"
        st.session_state.chat.append(("assistant", f"✅ Selected **{st.session_state.picked}**"))
        with col_main:
            with st.chat_message("assistant", avatar=AGENT_AVATAR):
                st.markdown(picked_msg, unsafe_allow_html=True)
        st.session_state.picked = None

# ---------- Re-render right panel if summary exists ----------
with col_right:
    if st.session_state.get("clinician_summary"):
        st.subheader("Clinician summary")
        st.markdown(st.session_state["clinician_summary"])

