import os
import time
import json
import re
import streamlit as st
from groq import Groq
from datetime import datetime
from dotenv import load_dotenv
from pathlib import Path

# ── Load .env file ───────────────────────────────────────────────────────────
env_path = Path(__file__).parent / ".env"
load_dotenv(dotenv_path=env_path)

# ── Try to get API key from .env first ───────────────────────────────────────
api_key = os.getenv("GROQ_API_KEY")

# ── If not found, ask user to input manually ─────────────────────────────────
if not api_key:
    st.warning("GROQ_API_KEY not found in .env file.")
    api_key = st.text_input("Enter your Groq API Key", type="password")

# ── Stop app if still not provided ───────────────────────────────────────────
if not api_key:
    st.stop()

# ── Create Groq client ───────────────────────────────────────────────────────
client = Groq(api_key=api_key)

MODEL = "llama-3.3-70b-versatile"

HISTORY_FILE = "chat_history.json"

SYSTEM_PROMPT = """You are TravelAgent, an expert AI travel planner.

You have access to the user's structured travel profile:
- Destination, budget level, trip duration, number of travelers, travel style, and interests

Your role:
- Use the structured profile data as the foundation for all recommendations
- Ask ONE follow-up question at a time if any detail is missing
- Generate detailed, personalized travel plans based on the profile
- Suggest destinations, hotels, attractions, local food, and transportation
- Give practical tips (visa, weather, currency, safety, best time to visit)

When generating a full travel plan, always structure it as:
🗺 Trip Overview — destination summary and why it suits them
📅 Day-by-Day Itinerary — detailed daily plan
🏨 Where to Stay — hotel recommendations matching their budget
🍽 Must-Try Food — local dishes and restaurant tips
💡 Travel Tips — visa, currency, weather, safety
💰 Estimated Budget Breakdown — realistic cost estimates

IMPORTANT: When showing prices or costs, always write LKR amounts like this: LKR 2000 - LKR 15000
Never use currency symbols for amounts. Always write "LKR" before the number.

Budget guide:
- Low Budget 🔵: free stays, volunteer programs, ultra-cheap transport (under LKR 3000/day)
- Budget 🟢: hostels, street food, public transport (LKR 3000 - LKR 8000/day)
- Mid-range 🟡: 3-star hotels, local restaurants, mix of transport (LKR 8000 - LKR 25000/day)
- Luxury 💎: 5-star hotels, fine dining, private transfers (LKR 25000+/day)

Always tailor everything to their exact profile. Be enthusiastic and inspiring.
You have memory of the full conversation — reference earlier preferences always.
"""

# ── History Helpers ───────────────────────────────────────────────────────────
def load_history():
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, "r") as f:
            return json.load(f)
    return []

def save_history(sessions):
    with open(HISTORY_FILE, "w") as f:
        json.dump(sessions, f, indent=2)

def save_current_session():
    if not st.session_state.messages:
        return
    if not st.session_state.current_session_id:
        st.session_state.current_session_id = datetime.now().strftime("%Y%m%d_%H%M%S")

    session_id  = st.session_state.current_session_id
    destination = st.session_state.profile.get("destination", "Trip")

    session = {
        "id":       session_id,
        "title":    destination,
        "date":     datetime.now().strftime("%d %b %Y, %H:%M"),
        "messages": st.session_state.messages,
        "profile":  st.session_state.profile,
    }

    all_sessions = [s for s in load_history() if s.get("id") != session_id]
    all_sessions.append(session)
    save_history(all_sessions)

def delete_session(session_id):
    all_sessions = [s for s in load_history() if s.get("id") != session_id]
    save_history(all_sessions)

# ── LLM Response ─────────────────────────────────────────────────────────────
def get_response(chat_history: list, profile: dict) -> str:
    try:
        profile_summary = f"""
Current Travel Profile:
- Destination: {profile.get('destination', 'Not specified')}
- Budget: {profile.get('budget', 'Not specified')}
- Duration: {profile.get('duration', 'Not specified')} days
- Travelers: {profile.get('travelers', 'Not specified')}
- Travel Style: {profile.get('style', 'Not specified')}
- Interests: {profile.get('interests', 'Not specified')}
"""
        full_system = SYSTEM_PROMPT + profile_summary
        messages    = [{"role": "system", "content": full_system}] + chat_history
        response    = client.chat.completions.create(
            model=MODEL,
            messages=messages,
            temperature=0.7,
            max_tokens=1500,
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"⚠️ Error: {str(e)}"

# ── Page Config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="TravelAgent – AI Travel Planner",
    page_icon="✈️",
    layout="centered",
    initial_sidebar_state="collapsed",
)

# ── Custom CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@600&family=Inter:wght@300;400;500;600&display=swap');

html, body, [class*="css"] { font-family: 'Inter', sans-serif; }

.block-container {
    max-width: 390px !important;
    padding: 1rem 0.8rem 6rem 0.8rem !important;
    margin: 0 auto !important;
}

.stApp {
    background: linear-gradient(160deg, #0a1628 0%, #1a2a4a 60%, #0d1f3d 100%);
    min-height: 100vh;
}

[data-testid="collapsedControl"] { display: none !important; }
header[data-testid="stHeader"]   { display: none !important; }

/* ── App Header ── */
.app-header {
    background: rgba(255,180,50,0.08);
    border: 1px solid rgba(255,180,50,0.2);
    border-radius: 16px;
    padding: 14px 16px 10px 16px;
    margin-bottom: 14px;
    text-align: center;
}
.main-title {
    font-family: 'Playfair Display', serif;
    font-size: 1.7rem;
    color: #fff8e7;
    margin: 0;
    line-height: 1.2;
}
.sub-title {
    color: #ffb432;
    font-size: 0.72rem;
    font-weight: 600;
    letter-spacing: 2px;
    text-transform: uppercase;
    margin-top: 4px;
}

/* ── Profile Card ── */
.profile-card {
    background: rgba(255,180,50,0.07);
    border: 1px solid rgba(255,180,50,0.25);
    border-radius: 12px;
    padding: 10px 12px;
    color: #d4c9a8;
    font-size: 0.78rem;
    line-height: 1.7;
    margin-bottom: 8px;
}
.profile-card b { color: #ffb432; }

/* ── Chat Bubbles ── */
.user-bubble {
    background: linear-gradient(135deg, #ffb432, #ff8c00);
    color: #fff;
    padding: 10px 14px;
    border-radius: 16px 16px 4px 16px;
    margin: 6px 0 6px auto;
    max-width: 88%;
    font-size: 0.88rem;
    line-height: 1.5;
    box-shadow: 0 3px 12px rgba(255,180,50,0.25);
    word-wrap: break-word;
}
.agent-bubble {
    background: rgba(255,255,255,0.05);
    border: 1px solid rgba(255,180,50,0.2);
    color: #e8dfc8;
    padding: 10px 14px;
    border-radius: 16px 16px 16px 4px;
    margin: 6px 0;
    max-width: 92%;
    font-size: 0.85rem;
    line-height: 1.65;
    backdrop-filter: blur(10px);
    word-wrap: break-word;
}
.agent-bubble strong { color: #ffb432; }

/* ── History Panel ── */
.history-header {
    color: #ffb432;
    font-size: 0.82rem;
    font-weight: 600;
    letter-spacing: 1px;
    text-transform: uppercase;
    margin-bottom: 8px;
    padding-bottom: 6px;
    border-bottom: 1px solid rgba(255,180,50,0.2);
}
.history-card {
    background: rgba(255,255,255,0.04);
    border: 1px solid rgba(255,180,50,0.18);
    border-radius: 12px;
    padding: 10px 12px;
    margin-bottom: 8px;
    cursor: pointer;
    transition: all 0.2s ease;
}
.history-card:hover {
    background: rgba(255,180,50,0.08);
    border-color: rgba(255,180,50,0.4);
}
.history-card-title {
    color: #fff8e7;
    font-size: 0.88rem;
    font-weight: 600;
    margin-bottom: 2px;
}
.history-card-meta {
    color: #8898b8;
    font-size: 0.72rem;
}
.history-card-preview {
    color: #b8a98a;
    font-size: 0.75rem;
    margin-top: 4px;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
    max-width: 280px;
}
.history-empty {
    color: #8898b8;
    font-size: 0.8rem;
    text-align: center;
    padding: 16px 0;
    font-style: italic;
}
.loaded-badge {
    display: inline-block;
    background: rgba(255,180,50,0.15);
    border: 1px solid rgba(255,180,50,0.4);
    color: #ffb432;
    font-size: 0.65rem;
    font-weight: 600;
    padding: 2px 7px;
    border-radius: 20px;
    margin-left: 6px;
    vertical-align: middle;
    letter-spacing: 0.5px;
}

/* ── Form Labels ── */
.stTextInput label, .stNumberInput label,
.stSelectbox label, .stSlider label,
.stMultiSelect label {
    color: #d4c9a8 !important;
    font-size: 0.8rem !important;
}
h1, h2, h3 { color: #fff8e7 !important; }
p, li      { color: #e8dfc8 !important; }
strong     { color: #ffb432 !important; }

/* ── Buttons ── */
.stButton > button {
    background: rgba(255,180,50,0.1);
    color: #ffb432;
    border: 1px solid rgba(255,180,50,0.3);
    border-radius: 10px;
    font-weight: 500;
    font-size: 0.85rem;
    padding: 6px 12px;
    transition: all 0.2s ease;
    width: 100%;
}
.stButton > button:hover {
    background: rgba(255,180,50,0.22);
    border-color: rgba(255,180,50,0.65);
}

/* ── Multiselect ── */
[data-baseweb="tag"] span,
[data-baseweb="tag"] { color: #1a1a1a !important; }
[data-baseweb="menu"] li,
[role="option"] {
    color: #1a1a1a !important;
    background-color: #fff !important;
}
[role="option"]:hover { background-color: #fff3dc !important; }
[data-baseweb="select"] input,
[data-baseweb="select"] input::placeholder { color: #1a1a1a !important; }

/* ── Thinking animation ── */
@keyframes pulse {
  0%, 100% { opacity: 1; }
  50%       { opacity: 0.4; }
}
.thinking {
    animation: pulse 1.2s ease-in-out infinite;
    color: #ffb432;
    font-size: 0.85rem;
    text-align: center;
    padding: 8px 0;
}

#chat-anchor { display: block; height: 0; visibility: hidden; }

/* ── Sticky chat input ── */
[data-testid="stChatInput"] {
    position: fixed !important;
    bottom: 0 !important;
    left: 50% !important;
    transform: translateX(-50%) !important;
    width: 390px !important;
    max-width: 390px !important;
    z-index: 9999 !important;
    background: #0d1f3d !important;
    padding: 10px 12px 14px 12px !important;
    border-top: 1px solid rgba(255,180,50,0.15) !important;
}

/* ── Input text fix ── */
textarea,
textarea:focus, textarea:active, textarea:hover,
.stChatInput textarea,
[data-testid="stChatInput"] textarea,
[data-baseweb="textarea"] textarea,
[data-baseweb="base-input"] textarea,
section[data-testid="stChatInput"] textarea,
div[data-testid="stChatInput"] textarea {
    color: #fff8e7 !important;
    -webkit-text-fill-color: #fff8e7 !important;
    caret-color: #ffb432 !important;
    background: rgba(255,255,255,0.07) !important;
    border: 1px solid rgba(255,180,50,0.3) !important;
    border-radius: 12px !important;
    font-size: 0.88rem !important;
    font-family: 'Inter', sans-serif !important;
    opacity: 1 !important;
}
textarea::placeholder,
[data-testid="stChatInput"] textarea::placeholder {
    color: #8898b8 !important;
    -webkit-text-fill-color: #8898b8 !important;
    opacity: 1 !important;
}
[data-testid="stChatInput"] > div,
[data-baseweb="base-input"],
[data-baseweb="textarea"] {
    background: rgba(255,255,255,0.07) !important;
    border-radius: 12px !important;
}
input,
input[type="text"], input[type="search"],
input[type="number"], input[type="email"], input[type="password"],
input:focus, input:active, input:hover,
.stTextInput input, .stNumberInput input,
[data-baseweb="input"] input,
[data-baseweb="base-input"] input {
    color: #fff8e7 !important;
    -webkit-text-fill-color: #fff8e7 !important;
    caret-color: #ffb432 !important;
    background: rgba(255,255,255,0.07) !important;
    border: 1px solid rgba(255,180,50,0.3) !important;
    border-radius: 10px !important;
    font-family: 'Inter', sans-serif !important;
    opacity: 1 !important;
}
input::placeholder,
.stTextInput input::placeholder,
.stNumberInput input::placeholder {
    color: #8898b8 !important;
    -webkit-text-fill-color: #8898b8 !important;
    opacity: 1 !important;
}
.stTextInput > div, .stNumberInput > div,
[data-baseweb="input"],
[data-testid="stTextInput"] > div > div,
[data-testid="stNumberInput"] > div > div {
    background: rgba(255,255,255,0.07) !important;
    border: 1px solid rgba(255,180,50,0.25) !important;
    border-radius: 10px !important;
}
[data-testid="stChatInput"] button {
    background: rgba(255,180,50,0.2) !important;
    border-radius: 10px !important;
    color: #ffb432 !important;
}

hr { border-color: rgba(255,180,50,0.12) !important; }
details summary {
    color: #ffb432 !important;
    font-size: 0.82rem !important;
    font-weight: 600;
}
</style>
""", unsafe_allow_html=True)

# ── Session State ─────────────────────────────────────────────────────────────
if "messages"           not in st.session_state: st.session_state.messages           = []
if "turn_count"         not in st.session_state: st.session_state.turn_count         = 0
if "profile"            not in st.session_state: st.session_state.profile            = {}
if "triggered_input"    not in st.session_state: st.session_state.triggered_input    = None
if "show_settings"      not in st.session_state: st.session_state.show_settings      = True
if "scroll_to_chat"     not in st.session_state: st.session_state.scroll_to_chat     = False
if "current_session_id" not in st.session_state: st.session_state.current_session_id = None
if "load_session_id"    not in st.session_state: st.session_state.load_session_id    = None
if "delete_session_id"  not in st.session_state: st.session_state.delete_session_id  = None
if "show_history"       not in st.session_state: st.session_state.show_history       = False

# ── Handle load/delete actions BEFORE rendering ───────────────────────────────
if st.session_state.load_session_id:
    target_id = st.session_state.load_session_id
    st.session_state.load_session_id = None
    all_sessions = load_history()
    for s in all_sessions:
        if s.get("id") == target_id:
            # Save current session first if it has messages
            if st.session_state.messages:
                save_current_session()
            st.session_state.messages           = s.get("messages", [])
            st.session_state.profile            = s.get("profile", {})
            st.session_state.current_session_id = s.get("id")
            st.session_state.turn_count         = sum(1 for m in st.session_state.messages if m["role"] == "user")
            st.session_state.show_settings      = False
            st.session_state.show_history       = False
            st.session_state.scroll_to_chat     = True
            break
    st.rerun()

if st.session_state.delete_session_id:
    delete_session(st.session_state.delete_session_id)
    # If deleting the currently active session, clear the chat
    if st.session_state.delete_session_id == st.session_state.current_session_id:
        st.session_state.messages           = []
        st.session_state.turn_count         = 0
        st.session_state.current_session_id = None
        st.session_state.show_settings      = True
    st.session_state.delete_session_id = None
    st.rerun()

# ── App Header ────────────────────────────────────────────────────────────────
st.markdown("""
<div class='app-header'>
  <div class='main-title'>✈️ Travel Agent</div>
  <div class='sub-title'>Your Autonomous AI Travel Planner</div>
</div>
""", unsafe_allow_html=True)

# ── Trip Settings ─────────────────────────────────────────────────────────────
with st.expander("⚙️ Trip Settings", expanded=st.session_state.show_settings):

    destination = st.text_input("📍 Destination", placeholder="e.g. Japan, Bali, Paris...")

    col1, col2 = st.columns(2)
    with col1:
        duration  = st.number_input("📅 Days",      min_value=1, max_value=30)
    with col2:
        travelers = st.number_input("👥 Travelers", min_value=1, max_value=20)

    budget = st.select_slider(
        "💰 Budget Level",
        options=["🔵 Low Budget", "🟢 Budget", "🟡 Mid-range", "💎 Luxury"],
        value="🟡 Mid-range"
    )

    style = st.multiselect(
        "🎯 Travel Style",
        ["🏖 Relaxation", "🏛 Cultural & History", "🌿 Nature & Adventure",
         "🍽 Food & Culinary", "🛍 Shopping & City", "🎒 Backpacking",
         "🧘 Wellness & Spa", "📸 Photography", "🎉 Nightlife",
         "🚴 Active & Sports", "🛳 Cruise & Sailing", "🏕 Camping"],
        default=["🏖 Relaxation"]
    )

    interests = st.multiselect(
        "❤️ Interests",
        ["Beaches", "Museums", "Hiking", "Street Food", "Nightlife",
         "Photography", "Temples", "Wildlife", "Luxury Spas", "Local Markets",
         "Cooking Classes", "Water Sports", "Art Galleries", "Historical Sites",
         "Local Festivals", "Scenic Drives", "Island Hopping"],
        default=["Beaches", "Street Food"]
    )

    st.session_state.profile = {
        "destination": destination if destination else "Not specified",
        "duration":    duration,
        "travelers":   travelers,
        "budget":      budget,
        "style":       ", ".join(style)     if style     else "Not specified",
        "interests":   ", ".join(interests) if interests else "Not specified",
    }

    if destination:
        st.markdown(f"""<div class='profile-card'>
        <b>📍</b> {destination} &nbsp;|&nbsp; <b>📅</b> {duration}d &nbsp;|&nbsp; <b>👥</b> {travelers}<br>
        <b>💰</b> {budget}<br>
        <b>🎯</b> {', '.join(style) if style else 'Not set'}<br>
        <b>❤️</b> {', '.join(interests) if interests else 'None'}
        </div>""", unsafe_allow_html=True)

    col_a, col_b = st.columns(2)
    with col_a:
        if st.button("🗺 Generate Plan", use_container_width=True):
            if destination:
                st.session_state.current_session_id = None
                st.session_state.triggered_input = (
                    f"Please generate a complete {duration}-day travel plan for {destination} "
                    f"for {travelers} traveler(s) with a {budget} budget. "
                    f"My travel style is {', '.join(style) if style else 'general'} and I'm interested in "
                    f"{', '.join(interests) if interests else 'general sightseeing'}. "
                    f"Include day-by-day itinerary, where to stay, must-try food, travel tips, and budget breakdown. "
                    f"Write all prices as LKR amounts (e.g. LKR 5000) not with rupee signs."
                )
                st.session_state.show_settings  = False
                st.session_state.scroll_to_chat = True
                st.rerun()
            else:
                st.warning("Enter a destination first!")
    with col_b:
        if st.button("🔄 New Trip", use_container_width=True):
            if st.session_state.messages:
                save_current_session()
            st.session_state.messages           = []
            st.session_state.turn_count         = 0
            st.session_state.triggered_input    = None
            st.session_state.scroll_to_chat     = False
            st.session_state.show_settings      = True
            st.session_state.current_session_id = None
            st.rerun()

st.markdown("---")

# ── 📚 Chat History Panel ─────────────────────────────────────────────────────
all_history = load_history()

with st.expander(f"Trip History  ({len(all_history)} saved)", expanded=st.session_state.show_history):

    if not all_history:
        st.markdown("<div class='history-empty'>No saved trips yet.<br>Generate a plan to get started!</div>",
                    unsafe_allow_html=True)
    else:
        # Sort newest first
        sorted_history = sorted(all_history, key=lambda s: s.get("id", ""), reverse=True)

        for session in sorted_history:
            sid         = session.get("id", "")
            title       = session.get("title", "Unknown Trip")
            date        = session.get("date", "")
            msgs        = session.get("messages", [])
            msg_count   = sum(1 for m in msgs if m["role"] == "user")
            is_active   = sid == st.session_state.current_session_id

            # Preview: first assistant message snippet
            preview = ""
            for m in msgs:
                if m["role"] == "assistant":
                    raw = re.sub(r'\*\*(.*?)\*\*', r'\1', m["content"])
                    raw = re.sub(r'\*(.*?)\*',     r'\1', raw)
                    raw = raw.replace('\n', ' ').strip()
                    preview = raw[:80] + "…" if len(raw) > 80 else raw
                    break

            active_badge = "<span class='loaded-badge'>ACTIVE</span>" if is_active else ""

            st.markdown(f"""
            <div class='history-card'>
                <div class='history-card-title'>🗺 {title}{active_badge}</div>
                <div class='history-card-meta'>📅 {date} &nbsp;·&nbsp; 💬 {msg_count} exchange{"s" if msg_count != 1 else ""}</div>
                {"<div class='history-card-preview'>" + preview + "</div>" if preview else ""}
            </div>
            """, unsafe_allow_html=True)

            btn_col1, btn_col2 = st.columns([3, 1])
            with btn_col1:
                load_label = "✅ Currently Loaded" if is_active else "📂 Load This Trip"
                if st.button(load_label, key=f"load_{sid}", use_container_width=True, disabled=is_active):
                    st.session_state.load_session_id = sid
                    st.rerun()
            with btn_col2:
                if st.button("🗑", key=f"del_{sid}", use_container_width=True):
                    st.session_state.delete_session_id = sid
                    st.rerun()

        st.markdown("---")
        if st.button("🗑 Clear All History", use_container_width=True):
            save_history([])
            if st.session_state.current_session_id:
                st.session_state.messages           = []
                st.session_state.turn_count         = 0
                st.session_state.current_session_id = None
                st.session_state.show_settings      = True
            st.rerun()

st.markdown("---")

# ── Chat anchor ───────────────────────────────────────────────────────────────
st.markdown('<div id="chat-anchor"></div>', unsafe_allow_html=True)

# ── Auto-scroll ───────────────────────────────────────────────────────────────
if st.session_state.scroll_to_chat:
    st.markdown("""
    <script>
        setTimeout(function() {
            var anchor = window.parent.document.getElementById('chat-anchor');
            if (anchor) {
                anchor.scrollIntoView({ behavior: 'smooth', block: 'start' });
            } else {
                window.parent.document.querySelector('section.main')
                    .scrollTo({ top: 99999, behavior: 'smooth' });
            }
        }, 300);
    </script>
    """, unsafe_allow_html=True)
    st.session_state.scroll_to_chat = False

# ── Chat Messages ─────────────────────────────────────────────────────────────
if not st.session_state.messages:
    st.markdown("""
    <div class='agent-bubble'>
    🌍 Hello! I'm <strong>Travel Agent</strong>, your AI travel planner!<br><br>
    👆 Open <strong>Trip Settings</strong> above to enter your destination and preferences,
    then tap <strong>🗺 Generate Plan</strong> — or just chat with me below!<br><br>
    You can also browse your saved trips in <strong>Trip History</strong>.
    </div>
    """, unsafe_allow_html=True)

for msg in st.session_state.messages:
    if msg["role"] == "user":
        st.markdown(f"<div class='user-bubble'>{msg['content']}</div>", unsafe_allow_html=True)
    else:
        content = msg["content"]
        content = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', content)
        content = re.sub(r'\*(.*?)\*',     r'<em>\1</em>',         content)
        content = content.replace('\n', '<br>')
        st.markdown(f"<div class='agent-bubble'>{content}</div>", unsafe_allow_html=True)

# ── Chat Input & Response ─────────────────────────────────────────────────────
typed_input = st.chat_input("Ask me about your trip...")

user_input = None
if st.session_state.triggered_input:
    user_input = st.session_state.triggered_input
    st.session_state.triggered_input = None
elif typed_input:
    user_input = typed_input

if user_input:
    st.session_state.messages.append({"role": "user", "content": user_input})
    st.markdown(f"<div class='user-bubble'>{user_input}</div>", unsafe_allow_html=True)

    thinking_placeholder = st.empty()
    thinking_placeholder.markdown(
        "<div class='thinking'>🌐 Planning your perfect trip...</div>",
        unsafe_allow_html=True
    )
    time.sleep(0.4)

    response = get_response(st.session_state.messages, st.session_state.profile)
    thinking_placeholder.empty()

    st.session_state.turn_count += 1
    st.session_state.messages.append({"role": "assistant", "content": response})

    save_current_session()

    resp_html = response
    resp_html = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', resp_html)
    resp_html = re.sub(r'\*(.*?)\*',     r'<em>\1</em>',         resp_html)
    resp_html = resp_html.replace('\n', '<br>')
    st.markdown(f"<div class='agent-bubble'>{resp_html}</div>", unsafe_allow_html=True)

    st.markdown("""
    <script>
        setTimeout(function() {
            window.parent.document.querySelector('section.main')
                .scrollTo({ top: 99999, behavior: 'smooth' });
        }, 300);
    </script>
    """, unsafe_allow_html=True)

# ── Footer ────────────────────────────────────────────────────────────────────
if st.session_state.turn_count > 0:
    st.markdown(
        f"<div style='color:#8898b8;font-size:0.72rem;text-align:center;margin-top:8px;'>"
        f"Turns: {st.session_state.turn_count}</div>",
        unsafe_allow_html=True
    )