# SupportDesk — Streamlit app (CSV, popup, clear fields without reload) + Staff tab
# Run:
#   pip install streamlit pandas
#   streamlit run app.py

import os
import csv
from datetime import datetime, date
from typing import List, Optional

import streamlit as st
import streamlit.components.v1 as components
import pandas as pd

# --- Config & paths ---
st.set_page_config(page_title="WESO Support Desk", page_icon="💬", layout="centered")
DATA_DIR = "data"
UPLOAD_DIR = "uploads"
CSV_PATH = os.path.join(DATA_DIR, "submissions.csv")

os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(UPLOAD_DIR, exist_ok=True)

CSV_HEADERS = [
    "timestamp", "full_name", "email", "category", "priority",
    "order_ref", "subject", "message", "attachment_file",
    "client_ip", "user_agent",
]

# Create CSV if missing
if not os.path.exists(CSV_PATH):
    with open(CSV_PATH, "w", newline="", encoding="utf-8") as f:
        csv.writer(f).writerow(CSV_HEADERS)

def append_row(row: List[str]) -> None:
    with open(CSV_PATH, "a", newline="", encoding="utf-8") as f:
        csv.writer(f).writerow(row)

def load_df() -> pd.DataFrame:
    if os.path.getsize(CSV_PATH) == 0:
        # Shouldn't happen because we write headers, but guard anyway
        return pd.DataFrame(columns=CSV_HEADERS)
    df = pd.read_csv(CSV_PATH)
    # Normalize category
    if "category" in df.columns:
        df["category"] = df["category"].astype(str).str.strip()
    # Normalize priority
    if "priority" in df.columns:
        df["priority"] = df["priority"].astype(str).str.strip()
    # Normalize timestamp to datetime for filtering/sorting
    if "timestamp" in df.columns:
        with pd.option_context("mode.chained_assignment", None):
            df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce", utc=True)
    # Fill NaNs for display
    return df.fillna("")
    
CATEGORIES = ["Question", "Bug report", "Feature request", "Other"]
PRIORITIES = ["Normal", "High", "Urgent"]

# --- Session init ---
st.session_state.setdefault("form_instance", 0)     # bump to clear all fields
st.session_state.setdefault("show_popup", False)    # show alert on next run
st.session_state.setdefault("staff_authed", False)  # staff login flag

# --- One-time popup (no reload) ---
if st.session_state["show_popup"]:
    components.html("<script>alert('Submitted');</script>", height=0)
    st.session_state["show_popup"] = False  # don't show again

# Helper to make per-instance keys so widgets remount empty after success
def k(name: str) -> str:
    return f"{name}_{st.session_state['form_instance']}"

# --- Header ---
ICON_B64 = "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"

st.markdown(f"""
<style>
.header {{
  display: flex; align-items: center; gap: 16px; margin-bottom: 1rem;
}}
.header-icon img {{
  width: 96px; height: 96px; display: block;
}}
.header-text {{ display: flex; flex-direction: column; justify-content: center; }}
.header-text .title {{ font-weight: 700; font-size: 28px; }}
.header-text .subtitle {{ color: #374151; font-size: 16px; margin-top: 2px; }}
.header-text .note {{ color: #6b7280; font-size: 14px; margin-top: 6px; }}
</style>

<div class="header">
  <div class="header-icon">
    <img src="data:image/png;base64,{ICON_B64}" alt="Support Desk logo">
  </div>
  <div class="header-text">
    <div class="title">Support Desk</div>
    <div class="subtitle">Submit a question or issue.</div>
    <div class="note">We typically reply within 1–2 business days.</div>
  </div>
</div>
""", unsafe_allow_html=True)

# ==============================
# Tabs: Submit | Tickets (staff)
# ==============================
tab_submit, tab_staff = st.tabs(["Submit ticket", "Tickets"])

with tab_submit:
    # --- Form (values persist on errors; clear on success by bumping form_instance) ---
    c1, c2 = st.columns(2)
    with c1:
        full_name = st.text_input("Full name", key=k("full_name"), placeholder="Jane Doe", max_chars=120)
    with c2:
        email = st.text_input("Email", key=k("email"), placeholder="jane@example.com", max_chars=200)

    c3, c4, c5 = st.columns([1, 1, 1])
    with c3:
        category = st.selectbox("Category", CATEGORIES, key=k("category"), index=0)
    with c4:
        priority = st.selectbox("Priority", PRIORITIES, key=k("priority"), index=0)
    with c5:
        order_ref = st.text_input("Order / Ref # (optional)", key=k("order_ref"))

    subject = st.text_input("Subject", key=k("subject"), max_chars=200)
    message = st.text_area("Message", key=k("message"), height=160)
    attachment = st.file_uploader(
        "Attachment (optional)",
        type=["png", "jpg", "jpeg", "gif", "pdf", "txt", "log", "csv", "zip"],
        key=k("uploader"),
    )
    consent = st.checkbox("I agree to receive email updates about this ticket.", key=k("consent"))

    submitted = st.button("Submit ticket", use_container_width=True)

    # --- Handle submit ---
    if submitted:
        errors = []
        if not full_name.strip(): errors.append("Full name is required.")
        if not email.strip() or "@" not in email: errors.append("Valid email is required.")
        if not subject.strip(): errors.append("Subject is required.")
        if not message.strip(): errors.append("Message is required.")
        if not consent: errors.append("Consent is required.")

        if errors:
            st.error("\n".join(errors))  # keep inputs
        else:
            # Save attachment (if any)
            saved_name = ""
            if attachment is not None:
                ts = datetime.utcnow().strftime("%Y%m%d-%H%M%S-%f")
                base = attachment.name.replace(" ", "_")
                saved_name = f"{ts}-{base}"
                with open(os.path.join(UPLOAD_DIR, saved_name), "wb") as out:
                    out.write(attachment.getbuffer())

            # Minimal request info (best effort)
            client_ip = st.session_state.get("client_ip", "")
            user_agent = st.session_state.get("user_agent", "")

            # Append row
            append_row([
                datetime.utcnow().isoformat(timespec="seconds") + "Z",
                full_name.strip(),
                email.strip(),
                category,
                priority,
                (order_ref or "").strip(),
                subject.strip(),
                message.strip(),
                saved_name,
                client_ip,
                user_agent,
            ])

            # Schedule popup and clear fields (no browser reload)
            st.session_state["show_popup"] = True
            st.session_state["form_instance"] += 1  # remount widgets with fresh keys
            st.rerun()

with tab_staff:
    st.subheader("Tickets (staff)")

    # --- Password gate using st.secrets ---
    # Configure one of these in .streamlit/secrets.toml or Streamlit Cloud:
    # STAFF_PASSWORD = "your-strong-password"
    required_password: Optional[str] = st.secrets.get("STAFF_PASSWORD", None)

    if required_password is None:
        st.info(
            "Staff portal is not configured. Add `STAFF_PASSWORD` to your `st.secrets` to enable this tab.\n\n"
            "Example `.streamlit/secrets.toml`:\n\n"
            "STAFF_PASSWORD = \"replace-me\"\n"
        )
    else:
        # Login UI
        if not st.session_state["staff_authed"]:
            pwd = st.text_input("Enter staff password", type="password")
            c_login, c_spacer = st.columns([1, 3])
            with c_login:
                if st.button("Sign in"):
                    if pwd == required_password:
                        st.session_state["staff_authed"] = True
                        st.success("Signed in.")
                        st.rerun()
                    else:
                        st.error("Invalid password.")
        else:
            # Toolbar
            toolbar_cols = st.columns([1,1,2,2,1])
            with toolbar_cols[0]:
                # default: all time; otherwise choose range
                df = load_df()
                if not df.empty and df["timestamp"].notna().any():
                    min_dt = df["timestamp"].min().date()
                    max_dt = df["timestamp"].max().date()
                else:
                    min_dt = date.today()
                    max_dt = date.today()
            with toolbar_cols[1]:
                date_from = st.date_input("From", value=min_dt, min_value=min_dt, max_value=max_dt)
            with toolbar_cols[2]:
                date_to = st.date_input("To", value=max_dt, min_value=min_dt, max_value=max_dt)
            with toolbar_cols[3]:
                col1, col2 = st.columns(2)
            # Build dropdown choices: "All" + known constants + any new values found in CSV
            cat_options = ["All"] + sorted(set(CATEGORIES) | set(df["category"].unique()))
            pri_options = ["All"] + sorted(set(PRIORITIES) | set(df["priority"].unique()))
            with col1:
                cat_choice = st.selectbox("Category", options=cat_options, index=0)
            with col2:
                pri_choice = st.selectbox("Priority", options=pri_options, index=0)
            with toolbar_cols[4]:
                st.write("")  # spacing

            search = st.text_input("Search (name, email, order ref, subject, message)")
            st.caption("Tip: download the raw CSV for full offline analysis.")

            # Load and filter
            df = load_df()
            if df.empty:
                st.info("No submissions yet.")
            else:
                # Date range (inclusive)
                if "timestamp" in df.columns:
                    mask_date = (df["timestamp"].dt.date >= date_from) & (df["timestamp"].dt.date <= date_to)
                    df = df[mask_date]

                # Category/priority filters
                if cat_choice != "All":
                    df = df[df["category"] == cat_choice]
                if pri_choice != "All":
                    df = df[df["priority"] == pri_choice]

                # Text search
                if search.strip():
                    s = search.strip().lower()
                    cols = ["full_name", "email", "order_ref", "subject", "message"]
                    mask = pd.Series(False, index=df.index)
                    for c in cols:
                        if c in df.columns:
                            mask |= df[c].astype(str).str.lower().str.contains(s, na=False)
                    df = df[mask]

                # Sort newest first
                if "timestamp" in df.columns:
                    df = df.sort_values("timestamp", ascending=False)

                # Show a condensed view; expand to see all fields
                show_cols = ["timestamp", "full_name", "email", "category", "priority",
                             "order_ref", "subject", "message", "attachment_file"]
                show_cols = [c for c in show_cols if c in df.columns]

                st.dataframe(
                    df[show_cols],
                    use_container_width=True,
                    hide_index=True
                )

                # Download buttons
                csv_bytes = df.to_csv(index=False).encode("utf-8")
                st.download_button(
                    "Download filtered CSV",
                    data=csv_bytes,
                    file_name="support_submissions_filtered.csv",
                    mime="text/csv",
                    use_container_width=True
                )

                # Attachment fetcher (optional convenience)
                with st.expander("Download an attachment"):
                    if "attachment_file" in df.columns and df["attachment_file"].astype(str).str.len().sum() > 0:
                        files = sorted({f for f in df["attachment_file"].astype(str) if f and f != "nan"})
                        if files:
                            chosen = st.selectbox("Select attachment", files)
                            local_path = os.path.join(UPLOAD_DIR, chosen)
                            if os.path.exists(local_path):
                                with open(local_path, "rb") as fh:
                                    st.download_button(
                                        "Download selected attachment",
                                        data=fh.read(),
                                        file_name=chosen,
                                        use_container_width=True
                                    )
                            else:
                                st.warning("File not found on server.")
                    else:
                        st.write("No attachments in the filtered results.")

                # Sign out
                if st.button("Sign out"):
                    # flip auth off
                    st.session_state["staff_authed"] = False
                    # optional: clear staff tab filters/inputs so they reset next time
                    for k in ["cat_filter", "pri_filter", "category_dropdown", "priority_dropdown"]:
                        st.session_state.pop(k, None)
                    st.rerun()
