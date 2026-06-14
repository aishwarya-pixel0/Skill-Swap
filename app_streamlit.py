# ============================================================
# SKILL SWAP PROJECT
# PART 4 : STREAMLIT FRONTEND (app.py)
# Presenter: Team Member 4


import streamlit as st  # type: ignore
import pandas as pd
from backend_db import (
    get_all_users, get_user_by_usn, add_user, update_user, delete_user,
    get_all_skills, add_skill,
    assign_skill_to_user, get_skills_by_user, search_teachers_by_skill,
    add_want_to_learn, get_wants_by_user,
    send_request, update_request_status,
    get_requests_for_user, get_requests_sent_by_user,
    find_swap_matches,
    skill_demand_stats, skill_supply_stats, dept_distribution, request_status_stats,
    get_total_request_count
)

# ── PAGE CONFIG ────────────────────────────────────────────
st.set_page_config(
    page_title="Skill Swap",
    page_icon="🔄",
    layout="wide"
)

# ── CUSTOM CSS (light BIT-blue theme) ─────────────────────
st.markdown("""
<style>
    [data-testid="stAppViewContainer"], .stApp {
        background: linear-gradient(180deg, #f8fbff 0%, #eef5ff 100%);
        color: #0f172a;
    }
    [data-testid="stAppViewContainer"] * {
        color: #0f172a;
    }
    h1, h2, h3, h4, h5, h6,
    .stMarkdown p,
    .stMarkdown li,
    .stMarkdown span,
    label,
    div[data-testid="stMetricLabel"],
    div[data-testid="stMetricValue"],
    div[data-testid="stSelectbox"],
    div[data-testid="stTextInput"],
    div[data-testid="stTextArea"] {
        color: #0f172a !important;
    }
    h1, h2, h3 { color: #1a237e !important; }
    [data-testid="stHeader"], [data-testid="stToolbar"] {
        background: rgba(255, 255, 255, 0.92);
    }
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #22252d 0%, #1a1d24 100%);
    }
    [data-testid="stSidebar"],
    [data-testid="stSidebar"] *,
    [data-testid="stSidebarNav"] * {
        color: #f8fafc !important;
    }
    [data-testid="stSidebar"] .stRadio label,
    [data-testid="stSidebar"] .stMarkdown p,
    [data-testid="stSidebar"] .stCaption,
    [data-testid="stSidebar"] .stTitle {
        color: #f8fafc !important;
    }
    .stButton > button {
        background-color: #1565c0;
        color: white;
        border-radius: 8px;
        border: none;
        font-weight: 600;
    }
    .stButton > button:hover { background-color: #0d47a1; }
    div[data-testid="stForm"] button,
    div[data-testid="stForm"] .stButton > button,
    div[data-testid="stForm"] button[kind="primary"],
    div[data-testid="stForm"] button[kind="secondary"] {
        background: #1565c0 !important;
        color: #ffffff !important;
        border: 1px solid #1565c0 !important;
        border-radius: 8px !important;
        font-weight: 700 !important;
        min-height: 44px !important;
        width: 100% !important;
    }
    div[data-testid="stForm"] button:hover {
        background: #0d47a1 !important;
        border-color: #0d47a1 !important;
    }
    .stTextInput input,
    .stTextArea textarea,
    [data-baseweb="select"] input,
    [data-baseweb="select"] * {
        color: #f8fafc !important;
        -webkit-text-fill-color: #f8fafc !important;
        caret-color: #f8fafc !important;
    }
    .stTextInput input::placeholder,
    .stTextArea textarea::placeholder {
        color: rgba(248, 250, 252, 0.6) !important;
    }
    [data-testid="stForm"] {
        background: rgba(255, 255, 255, 0.65);
        border: 1px solid rgba(15, 23, 42, 0.08);
        border-radius: 16px;
        padding: 1rem;
        box-shadow: 0 10px 30px rgba(15, 23, 42, 0.08);
    }
    .metric-card {
        background: white;
        border-radius: 12px;
        padding: 16px 20px;
        border-left: 5px solid #1565c0;
        margin-bottom: 10px;
        box-shadow: 0 2px 6px rgba(0,0,0,0.08);
    }
    .match-card {
        background: #e3f2fd;
        border-radius: 10px;
        padding: 14px 18px;
        margin-bottom: 8px;
        border-left: 4px solid #42a5f5;
    }
</style>
""", unsafe_allow_html=True)

# ── SIDEBAR NAV ────────────────────────────────────────────
st.sidebar.image(
    r"C:\Users\aishw\OneDrive\Pictures\logoss.png", width=80
)
st.sidebar.title("Skill Swap")
st.sidebar.caption("BIT Bangalore — Peer Learning Platform")

PAGES = [
    "🏠 Dashboard",
    "👤 Register / Profile",
    "🔍 Find a Teacher",
    "📬 My Requests",
    "🤝 Smart Match",
    "⚙️  Admin Panel",
]
page = st.sidebar.radio("Navigate", PAGES)

# ── HELPER ─────────────────────────────────────────────────
PROFICIENCY_OPTIONS = ["Beginner", "Intermediate", "Expert"]
DEPT_OPTIONS = [
    "Computer Science", "Information Science",
    "Electronics and Telecommunication",
    "Electronics and Instrumentation", "Electrical and Electronics",
    "Mechanical", "Civil", "Robotics and AI", "Other"
]

def skill_name_list() -> list[str]:
    return [s["skill_name"] for s in get_all_skills()]


def default_profile_label(labels: list[str]) -> str:
    qp_profile = st.query_params.get("profile")
    if isinstance(qp_profile, list):
        qp_profile = qp_profile[0] if qp_profile else ""

    candidate = qp_profile or st.session_state.get("active_profile", labels[0])
    return candidate if candidate in labels else labels[0]

# ══════════════════════════════════════════════════════════
# PAGE 1 — DASHBOARD
# ══════════════════════════════════════════════════════════
if page == "🏠 Dashboard":
    st.title("Skill Swap — BIT Bangalore")
    st.markdown("**A peer-to-peer skill exchange platform for students**")
    st.divider()

    # KPI row
    users  = get_all_users()
    skills = get_all_skills()
    col1, col2, col3 = st.columns(3)
    col1.metric("👥 Students Registered", len(users))
    col2.metric("🛠️ Skills in Catalog",   len(skills))
    col3.metric("🔁 Exchange Requests",   get_total_request_count())

    st.subheader("📊 Skill Demand vs Supply")
    demand = pd.DataFrame(skill_demand_stats()).rename(columns={"skill_name": "Skill", "demand_count": "Want to Learn"})
    supply = pd.DataFrame(skill_supply_stats()).rename(columns={"skill_name": "Skill", "supply_count": "Can Teach"})

    if not demand.empty and not supply.empty:
        merged = pd.merge(demand, supply, on="Skill", how="outer").fillna(0)
        merged = merged.set_index("Skill")
        st.bar_chart(merged)
    else:
        st.info("No data yet — import survey responses first.")

    st.subheader("🏫 Students by Department")
    dept_data = dept_distribution()
    if dept_data:
        df_dept = pd.DataFrame(dept_data).rename(columns={"dept": "Department", "count": "Count"})
        st.dataframe(df_dept, width="stretch", hide_index=True)

# ══════════════════════════════════════════════════════════
# PAGE 2 — REGISTER / PROFILE
# ══════════════════════════════════════════════════════════
elif page == "👤 Register / Profile":
    st.title("👤 Student Profile")

    tab_reg, tab_view, tab_edit = st.tabs(["➕ Register", "👁 View Profile", "✏️ Edit / Delete"])

    # ── REGISTER ──
    with tab_reg:
        st.subheader("New Student Registration")
        with st.form("reg_form"):
            col1, col2 = st.columns(2)
            name  = col1.text_input("Full Name *")
            usn   = col2.text_input("USN *")
            email = col1.text_input("Email")
            dept  = col2.selectbox("Department", DEPT_OPTIONS)
            year  = st.slider("Year of Study", 1, 4, 1)

            st.markdown("**Skills You Can Teach**")
            teach_skills  = st.multiselect("Select skills", skill_name_list())
            proficiency   = st.selectbox("Your Proficiency Level", PROFICIENCY_OPTIONS)

            st.markdown("**Skills You Want to Learn**")
            learn_skills  = st.multiselect("Select skills", skill_name_list(), key="learn")
            reason        = st.text_area("Why do you want to learn these skills?")

            submitted = st.form_submit_button("Register")
            if submitted:
                if not name or not usn:
                    st.error("Name and USN are required.")
                elif get_user_by_usn(usn):
                    st.warning(f"USN {usn} is already registered.")
                else:
                    uid = add_user(name, usn, email or f"{name.lower().replace(' ','')}@bit.edu.in", dept, year)
                    all_skills = {s["skill_name"]: s["skill_id"] for s in get_all_skills()}
                    for sk in teach_skills:
                        assign_skill_to_user(uid, all_skills[sk], proficiency)
                    for sk in learn_skills:
                        add_want_to_learn(uid, all_skills[sk], reason)
                    st.success(f"✅ {name} registered successfully! (ID: {uid})")

    # ── VIEW PROFILE ──
    with tab_view:
        st.subheader("Look Up a Profile")
        usn_input = st.text_input("Enter USN to search")
        if st.button("Search"):
            user = get_user_by_usn(usn_input.strip())
            if user:
                st.markdown(f"""
                <div class="metric-card">
                    <h3>{user['name']}</h3>
                    <p>USN: <b>{user['usn']}</b> | Dept: <b>{user['dept']}</b> | Year: <b>{user['year']}</b></p>
                    <p>Email: {user['email']}</p>
                </div>
                """, unsafe_allow_html=True)

                col_t, col_l = st.columns(2)
                with col_t:
                    st.markdown("**Skills They Teach**")
                    teaches = get_skills_by_user(user["user_id"])
                    if teaches:
                        for s in teaches:
                            st.write(f"• {s['skill_name']} — *{s['proficiency_level']}*")
                    else:
                        st.write("None listed")

                with col_l:
                    st.markdown("**Skills They Want to Learn**")
                    wants = get_wants_by_user(user["user_id"])
                    if wants:
                        for s in wants:
                            st.write(f"• {s['skill_name']}")
                    else:
                        st.write("None listed")
            else:
                st.error("No student found with that USN.")

    # ── EDIT / DELETE ──
    with tab_edit:
        st.subheader("Edit or Delete Profile")
        usn_edit = st.text_input("Enter USN", key="edit_usn")
        if st.button("Load Profile"):
            user = get_user_by_usn(usn_edit.strip())
            if user:
                st.session_state["edit_user"] = user
            else:
                st.error("User not found.")

        if "edit_user" in st.session_state:
            user = st.session_state["edit_user"]
            with st.form("edit_form"):
                new_name  = st.text_input("Name",  value=user["name"])
                new_email = st.text_input("Email", value=user.get("email",""))
                new_dept  = st.selectbox("Dept", DEPT_OPTIONS,
                                         index=DEPT_OPTIONS.index(user["dept"]) if user["dept"] in DEPT_OPTIONS else 0)
                new_year  = st.slider("Year", 1, 4, int(user["year"]))
                col_s, col_d = st.columns(2)
                save   = col_s.form_submit_button("💾 Save Changes")
                delete = col_d.form_submit_button("🗑️ Delete Account")
                if save:
                    update_user(user["user_id"], new_name, new_email, new_dept, new_year)
                    st.success("Profile updated!")
                    del st.session_state["edit_user"]
                if delete:
                    delete_user(user["user_id"])
                    st.success("Account deleted.")
                    del st.session_state["edit_user"]

# ══════════════════════════════════════════════════════════
# PAGE 3 — FIND A TEACHER
# ══════════════════════════════════════════════════════════
elif page == "🔍 Find a Teacher":
    st.title("🔍 Find a Teacher")
    st.caption("Search for a peer who can teach you any skill")

    # Show any pending success messages
    if st.session_state.get("just_sent_request"):
        req_info = st.session_state.get("request_info", {})
        st.success(f"✅ Request #{req_info.get('id', '?')} sent successfully to {req_info.get('receiver', 'user')}!")
        st.info(f"Go to **My Requests** → **Sent** to see your request")
        st.balloons()
        # Clear the flag after displaying
        st.session_state["just_sent_request"] = False

    query = st.text_input("Enter a skill name (e.g. Python, SQL, Guitar …)")
    if st.button("Search") and query:
        results = search_teachers_by_skill(query)
        if results:
            df = pd.DataFrame(results).rename(columns={
                "name": "Student", "usn": "USN",
                "dept": "Department", "year": "Year",
                "skill_name": "Skill", "proficiency_level": "Level"
            })
            st.success(f"Found {len(results)} result(s)!")
            st.dataframe(df, width="stretch", hide_index=True)

            # Send Request section
            st.divider()
            st.subheader("📩 Send a Skill Exchange Request")
            all_users = get_all_users()
            user_opts = {u["name"] + f" ({u['usn']})": u["user_id"] for u in all_users}

            col1, col2 = st.columns(2)
            with col1:
                sender_label = st.selectbox("You are …", list(user_opts.keys()))
                sender_id = user_opts[sender_label]
                st.session_state["active_profile"] = sender_label
                st.query_params["profile"] = sender_label
                
            with col2:
                skill_opts = {s["skill_name"]: s["skill_id"] for s in get_all_skills()}
                skill_sel = st.selectbox("For skill", list(skill_opts.keys()))

            sender_user = next((u for u in all_users if u["user_id"] == sender_id), None)
            sender_usn = sender_user["usn"] if sender_user else None
            receiver_candidates = [
                r["name"] + f" ({r['usn']})"
                for r in results
                if r["usn"] != sender_usn
            ]
            
            if receiver_candidates:
                receiver_label = st.selectbox("Send request to …", receiver_candidates)
                if st.button("📤 Send Request", key="send_btn", use_container_width=True):
                    receiver_usn = receiver_label.split("(")[-1].rstrip(")")
                    receiver = get_user_by_usn(receiver_usn)
                    if receiver:
                        try:
                            rid = send_request(sender_id, receiver["user_id"], skill_opts[skill_sel])
                            st.session_state["just_sent_request"] = True
                            st.session_state["request_info"] = {
                                "id": rid,
                                "receiver": receiver["name"],
                                "skill": skill_sel
                            }
                            st.rerun()
                        except ValueError as exc:
                            st.error(str(exc))
                    else:
                        st.error("Could not find the selected receiver.")
            else:
                st.info("No other students found in these results. Search for a different skill.")
        else:
            st.warning("No teachers found for that skill.")

    st.divider()
    st.subheader("📋 All Registered Skills")
    all_skills = get_all_skills()
    cols = st.columns(3)
    for i, s in enumerate(all_skills):
        cols[i % 3].write(f"• {s['skill_name']}")

# ══════════════════════════════════════════════════════════
# PAGE 4 — MY REQUESTS
# ══════════════════════════════════════════════════════════
elif page == "📬 My Requests":
    st.title("📬 My Requests")

    all_users   = get_all_users()
    user_opts   = {u["name"] + f" ({u['usn']})": u["user_id"] for u in all_users}
    profile_labels = list(user_opts.keys())
    default_label = default_profile_label(profile_labels)
    default_index = profile_labels.index(default_label) if default_label in profile_labels else 0
    me_label    = st.selectbox("Select your profile", profile_labels, index=default_index)
    me_id       = user_opts[me_label]
    st.session_state["active_profile"] = me_label
    st.query_params["profile"] = me_label

    tab_in, tab_out = st.tabs(["📥 Inbox (Received)", "📤 Sent"])

    with tab_in:
        inbox = get_requests_for_user(me_id)
        if inbox:
            st.subheader("Incoming Requests")
            for r in inbox:
                with st.expander(f"#{r['request_id']} — {r['sender_name']} wants to learn **{r['skill_name']}**   [{r['status']}]"):
                    col1, col2 = st.columns([2, 1])
                    with col1:
                        st.write(f"📌 **From:** {r['sender_name']} ({r['sender_usn']})")
                        st.write(f"🛠️ **Skill:** {r['skill_name']}")
                        st.write(f"⏰ **Requested:** {r['created_at']}")
                    with col2:
                        st.write(f"**Status:** `{r['status']}`")
                    st.divider()
                    if r["status"] == "Pending":
                        col1, col2, col3 = st.columns(3)
                        if col1.button("✅ Accept",  key=f"acc_{r['request_id']}", use_container_width=True):
                            update_request_status(r["request_id"], "Accepted")
                            st.success("✅ Accepted!"); st.rerun()
                        if col2.button("⏳ Pending",  key=f"pend_{r['request_id']}", use_container_width=True, disabled=True):
                            pass
                        if col3.button("❌ Reject",  key=f"rej_{r['request_id']}", use_container_width=True):
                            update_request_status(r["request_id"], "Rejected")
                            st.warning("❌ Rejected."); st.rerun()
                    elif r["status"] == "Accepted":
                        col1, col2 = st.columns(2)
                        with col1:
                            st.write("✅ **You accepted this request**")
                        with col2:
                            if st.button("🏁 Mark Completed", key=f"done_{r['request_id']}", use_container_width=True):
                                update_request_status(r["request_id"], "Completed")
                                st.success("✅ Marked as completed!"); st.rerun()
                    elif r["status"] == "Rejected":
                        st.write("❌ **You rejected this request**")
                    elif r["status"] == "Completed":
                        st.write("🎉 **Exchange completed!**")
        else:
            st.info("📭 No incoming requests yet.")

    with tab_out:
        sent = get_requests_sent_by_user(me_id)
        if sent:
            st.subheader("Requests You Sent")
            for s in sent:
                with st.expander(f"#{s['request_id']} → {s['receiver_name']} for **{s['skill_name']}**   [{s['status']}]"):
                    col1, col2 = st.columns([2, 1])
                    with col1:
                        st.write(f"👤 **To:** {s['receiver_name']} ({s['receiver_usn']})")
                        st.write(f"🛠️ **Skill:** {s['skill_name']}")
                        st.write(f"⏰ **Sent:** {s['created_at']}")
                    with col2:
                        status_emoji = {"Pending": "⏳", "Accepted": "✅", "Rejected": "❌", "Completed": "🎉"}.get(s['status'], "❓")
                        st.write(f"**Status:** `{status_emoji} {s['status']}`")
        else:
            st.info("📭 You haven't sent any requests yet.")

# ══════════════════════════════════════════════════════════
# PAGE 5 — SMART MATCH
# ══════════════════════════════════════════════════════════
elif page == "🤝 Smart Match":
    st.title("🤝 Smart Skill Match")
    st.markdown("Find students who **need what you know** and **know what you need**. Perfect mutual swaps!")

    all_users = get_all_users()
    user_opts = {u["name"] + f" ({u['usn']})": u["user_id"] for u in all_users}
    profile_labels = list(user_opts.keys())
    default_label = default_profile_label(profile_labels)
    default_index = profile_labels.index(default_label) if default_label in profile_labels else 0
    me_label  = st.selectbox("Select your profile", profile_labels, index=default_index)
    me_id     = user_opts[me_label]
    st.session_state["active_profile"] = me_label
    st.query_params["profile"] = me_label

    if st.button("🔍 Find My Matches"):
        matches = find_swap_matches(me_id)
        if matches:
            st.success(f"Found **{len(matches)}** potential swap partner(s)!")
            for m in matches:
                st.markdown(f"""
                <div class="match-card">
                    <b>{m['partner_name']}</b> ({m['partner_usn']}) — {m['partner_dept']}<br/>
                    🎓 They can teach you: <b>{m['they_teach']}</b><br/>
                    📚 You can teach them: <b>{m['you_teach']}</b>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.info("No mutual matches found yet. Try adding more skills to your profile!")

# ══════════════════════════════════════════════════════════
# PAGE 6 — ADMIN PANEL
# ══════════════════════════════════════════════════════════
elif page == "⚙️  Admin Panel":
    st.title("⚙️ Admin Panel")

    tab_users, tab_skills, tab_req = st.tabs(["👥 All Users", "🛠️ Skills", "📊 Requests"])

    with tab_users:
        st.subheader("All Registered Students")
        users = get_all_users()
        if users:
            st.dataframe(pd.DataFrame(users), width="stretch", hide_index=True)
        else:
            st.info("No users yet.")

    with tab_skills:
        st.subheader("Skill Catalog")
        skills = get_all_skills()
        df_sk  = pd.DataFrame(skills)
        st.dataframe(df_sk, width="stretch", hide_index=True)

        st.divider()
        st.subheader("Add a New Skill")
        new_skill = st.text_input("Skill name")
        if st.button("Add Skill") and new_skill:
            sid = add_skill(new_skill)
            st.success(f"Skill added (ID: {sid})")

    with tab_req:
        st.subheader("Exchange Requests Overview")
        stats = request_status_stats()
        if stats:
            df_stats = pd.DataFrame(stats).rename(columns={"status": "Status", "count": "Count"})
            col1, col2 = st.columns([1, 2])
            col1.dataframe(df_stats, hide_index=True)
            col2.bar_chart(df_stats.set_index("Status"))
        else:
            st.info("No requests yet.")

# ── FOOTER ─────────────────────────────────────────────────
st.sidebar.divider()
st.sidebar.caption("Skill Swap v1.0 · BIT Bangalore · DBMS Mini Project")
st.sidebar.caption("Team: Ananya · Shri Hari · Aishwarya · Adithi")
