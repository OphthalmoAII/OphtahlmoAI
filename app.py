import streamlit as st
import psycopg2
import pandas as pd
import hashlib
import uuid
import urllib.parse
from datetime import datetime
import plotly.express as px

# ================== CONFIG ================== #

st.set_page_config(page_title="OphthalmoAI SaaS", layout="wide")

# ================== DATABASE ================== #

DB_URL = st.secrets["DB_URL"]

try:
    conn = psycopg2.connect(
        DB_URL,
        sslmode="require",
        connect_timeout=10
    )
    cur = conn.cursor()
except Exception as e:
    st.error("Database connection failed ❌")
    st.write(e)
    st.stop()


# ================== STYLING ================== #

st.markdown("""
<style>
body {background-color:#f4f6f9;}

[data-testid="stSidebar"] {
    background: linear-gradient(180deg,#0f766e,#115e59);
}
[data-testid="stSidebar"] * {
    color: white;
}

.page-title {
    font-size:28px;
    font-weight:700;
}

.metric-card {
    background:white;
    padding:20px;
    border-radius:14px;
    box-shadow:0px 4px 20px rgba(0,0,0,0.05);
}
</style>
""", unsafe_allow_html=True)

# ================== PASSWORD HASH ================== #

def hash_pwd(p):
    return hashlib.sha256(p.encode()).hexdigest()

# ================== SESSION INIT ================== #

if "login" not in st.session_state:
    st.session_state.login = False

# ================== LOGIN ================== #

if not st.session_state.login:

    st.title("OphthalmoAI Enterprise Login")

    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    if st.button("Login"):

        cur.execute(
            "SELECT id, role, hospital_id FROM users WHERE username=%s AND password=%s",
            (username, password)
        )
        user = cur.fetchone()

        if user:
            st.session_state.login = True
            st.session_state.user_id = user[0]
            st.session_state.role = user[1]
            st.session_state.hospital_id = user[2]
            st.session_state.username = username
            st.rerun()
        else:
            st.error("Invalid Credentials")

    st.stop()



# ================== LOAD DATA ================== #

cur.execute(
    "SELECT * FROM patients WHERE hospital_id=%s",
    (st.session_state.hospital_id,)
)
rows = cur.fetchall()

columns = [
    "id","patient_id","name","phone","city","age","gender",
    "vision_od","vision_os","procedure","iol",
    "doctor","counsellor","cost","status","created_on","hospital_id"
]

df = pd.DataFrame(rows, columns=columns) if rows else pd.DataFrame(columns=columns)

# ==========================================================
# ===================== SIDEBAR =============================
# ==========================================================

from datetime import date, timedelta, datetime, time
import calendar

# ---------------- REMOVE ALL WHITE / SHADOW ---------------- #

st.markdown("""
<style>

/* Sidebar background */
section[data-testid="stSidebar"] {
    background-color: #eef2f7 !important;
}

/* Remove all white backgrounds */
section[data-testid="stSidebar"] .stDateInput,
section[data-testid="stSidebar"] .stButton,
section[data-testid="stSidebar"] .stRadio,
section[data-testid="stSidebar"] .stSelectbox,
section[data-testid="stSidebar"] .stTextInput {
    background: transparent !important;
    box-shadow: none !important;
    border: none !important;
}

/* Remove internal white containers */
section[data-testid="stSidebar"] div[data-testid="stVerticalBlock"] > div {
    background: transparent !important;
    box-shadow: none !important;
    border: none !important;
}

/* Remove input white box */
section[data-testid="stSidebar"] input {
    background-color: #e5e7eb !important;
    color: #111827 !important;
    border-radius: 6px !important;
    border: none !important;
}

/* Buttons clean style */
section[data-testid="stSidebar"] button {
    background-color: #dbeafe !important;
    color: #1e3a8a !important;
    border-radius: 6px !important;
    border: none !important;
    box-shadow: none !important;
}

/* Remove hover white flash */
section[data-testid="stSidebar"] button:hover {
    background-color: #bfdbfe !important;
}

/* Labels */
section[data-testid="stSidebar"] label {
    color: #111827 !important;
    font-weight: 500 !important;
}

</style>
""", unsafe_allow_html=True)


# ---------------- TITLE ---------------- #

st.sidebar.markdown("## 🏥 OphthalmoAI")
st.sidebar.markdown("---")


# ==========================================================
# ================= ROLE BASED MENU ========================
# ==========================================================

def menu_item(label, icon):
    return f"{icon}  {label}"

if st.session_state.role == "master":
    menu = {
        menu_item("Dashboard", "📊"): "Dashboard",
        menu_item("Master Control", "🛠️"): "Master Control",
    }

elif st.session_state.role == "hospital_admin":
    menu = {
        menu_item("Dashboard", "📊"): "Dashboard",
        menu_item("Patients", "👥"): "Patients",
        menu_item("Daily Reminders", "🔔"): "Daily Reminders",
        menu_item("Conversion", "📈"): "Conversion",
        menu_item("Pending", "⏳"): "Pending",
        menu_item("Revenue", "💰"): "Revenue",
        menu_item("Doctors", "🩺"): "Doctors",
        menu_item("Demographics", "📊"): "Demographics",
    }

else:
    menu = {
        menu_item("Dashboard", "📊"): "Dashboard",
        menu_item("Patients", "👥"): "Patients",
        menu_item("Daily Reminders", "🔔"): "Daily Reminders",
        menu_item("Pending", "⏳"): "Pending",
        menu_item("Doctors", "🩺"): "Doctors",
    }

choice_display = st.sidebar.radio("", list(menu.keys()))
choice = menu[choice_display]

st.sidebar.markdown("---")


# ==========================================================
# ================= DATE FILTER ============================
# ==========================================================

st.sidebar.markdown("### 📅 Date Range")

if "start_date" not in st.session_state:
    st.session_state.start_date = date.today() - timedelta(days=30)

if "end_date" not in st.session_state:
    st.session_state.end_date = date.today()

col1, col2 = st.sidebar.columns(2)

if col1.button("Today", use_container_width=True):
    st.session_state.start_date = date.today()
    st.session_state.end_date = date.today()
    st.rerun()

if col2.button("7 Days", use_container_width=True):
    st.session_state.start_date = date.today() - timedelta(days=7)
    st.session_state.end_date = date.today()
    st.rerun()

col3, col4 = st.sidebar.columns(2)

if col3.button("30 Days", use_container_width=True):
    st.session_state.start_date = date.today() - timedelta(days=30)
    st.session_state.end_date = date.today()
    st.rerun()

if col4.button("This Month", use_container_width=True):
    today = date.today()
    first_day = date(today.year, today.month, 1)
    last_day = date(today.year, today.month,
                    calendar.monthrange(today.year, today.month)[1])
    st.session_state.start_date = first_day
    st.session_state.end_date = last_day
    st.rerun()

start_date = st.sidebar.date_input("From", st.session_state.start_date)
end_date = st.sidebar.date_input("To", st.session_state.end_date)

if st.sidebar.button("Apply", use_container_width=True):
    st.session_state.start_date = start_date
    st.session_state.end_date = end_date
    st.rerun()

st.sidebar.markdown("---")


# ==========================================================
# ================= LOGOUT =====================
# ==========================================================

if st.sidebar.button("🚪 Logout", use_container_width=True):
    st.session_state.clear()
    st.rerun()


# ==========================================================
# ================= GLOBAL FILTERED DATA ===================
# ==========================================================

start_datetime = datetime.combine(
    st.session_state.start_date,
    time.min
)

end_datetime = datetime.combine(
    st.session_state.end_date,
    time.max
)

cur.execute("""
    SELECT *
    FROM patients
    WHERE hospital_id=%s
    AND created_on BETWEEN %s AND %s
    ORDER BY created_on DESC
""", (
    st.session_state.hospital_id,
    start_datetime,
    end_datetime
))

rows = cur.fetchall()

columns = [
    "id","patient_id","name","phone","city","age","gender",
    "vision_od","vision_os","procedure","iol",
    "doctor","counsellor","cost","status","created_on","hospital_id"
]

df = pd.DataFrame(rows, columns=columns) if rows else pd.DataFrame(columns=columns)


# ================= DASHBOARD ================= #

if choice == "Dashboard":

    st.markdown("""
    <style>
    .card {
        background:white;
        padding:20px;
        border-radius:14px;
        box-shadow:0 6px 20px rgba(0,0,0,0.08);
        text-align:left;
    }
    .card-title {
        font-size:13px;
        color:#6b7280;
        margin-bottom:8px;
    }
    .card-value {
        font-size:24px;
        font-weight:700;
    }
    </style>
    """, unsafe_allow_html=True)

    st.markdown("<div class='page-title'>Master Dashboard</div>", unsafe_allow_html=True)
    st.markdown("<div class='page-sub'>Real-time hospital performance intelligence</div>", unsafe_allow_html=True)

    cur.execute("""
        SELECT procedure, status, cost
        FROM patients
        WHERE hospital_id=%s
    """, (st.session_state.hospital_id,))
    rows = cur.fetchall()

    df_dash = pd.DataFrame(rows, columns=["procedure","status","cost"])

    total = len(df_dash)
    converted = len(df_dash[df_dash["status"]=="Converted"])
    pending = len(df_dash[df_dash["status"]=="Pending"])

    revenue_done = df_dash[df_dash["status"]=="Converted"]["cost"].sum() if total>0 else 0
    revenue_pending = df_dash[df_dash["status"]=="Pending"]["cost"].sum() if total>0 else 0

    conversion_rate = (converted/total*100) if total>0 else 0

    # ---------- TOP ROW ---------- #

    c1, c2, c3, c4 = st.columns(4)

    with c1:
        st.markdown(f"""
        <div class='card'>
            <div class='card-title'>TOTAL ADVISED</div>
            <div class='card-value'>{total}</div>
        </div>
        """, unsafe_allow_html=True)

    with c2:
        st.markdown(f"""
        <div class='card'>
            <div class='card-title'>CONVERSION RATE</div>
            <div class='card-value'>{conversion_rate:.1f}%</div>
        </div>
        """, unsafe_allow_html=True)

    with c3:
        st.markdown(f"""
        <div class='card'>
            <div class='card-title'>REVENUE DONE</div>
            <div class='card-value'>₹{revenue_done:,.0f}</div>
        </div>
        """, unsafe_allow_html=True)

    with c4:
        st.markdown(f"""
        <div class='card'>
            <div class='card-title'>REVENUE PENDING</div>
            <div class='card-value'>₹{revenue_pending:,.0f}</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ---------- CATEGORY CARDS ---------- #

    colA, colB = st.columns(2)

    with colA:
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.markdown("### 📈 Top Performing Category")

        if total > 0:
            top_proc = df_dash["procedure"].value_counts().idxmax()
            top_total = len(df_dash[df_dash["procedure"] == top_proc])
            top_converted = len(
                df_dash[
                    (df_dash["procedure"] == top_proc) &
                    (df_dash["status"] == "Converted")
                ]
            )

            top_rate = (top_converted / top_total * 100) if top_total > 0 else 0

            st.markdown(f"<h2 style='color:#059669'>{top_rate:.1f}%</h2>", unsafe_allow_html=True)
            st.markdown(f"<div style='font-size:20px;font-weight:600'>{top_proc}</div>", unsafe_allow_html=True)
            st.markdown(f"<div style='color:#6b7280'>{top_converted} of {top_total} patients converted</div>", unsafe_allow_html=True)

        else:
            st.info("No Data")

        st.markdown("</div>", unsafe_allow_html=True)

    with colB:
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.markdown("### ⚠ Needs Attention")

        if pending > 0:
            worst_proc = df_dash[df_dash["status"] == "Pending"]["procedure"].value_counts().idxmax()
            worst_total = len(df_dash[df_dash["procedure"] == worst_proc])
            worst_pending = len(
                df_dash[
                    (df_dash["procedure"] == worst_proc) &
                    (df_dash["status"] == "Pending")
                ]
            )

            worst_rate = (worst_pending / worst_total * 100) if worst_total > 0 else 0

            st.markdown(f"<h2 style='color:#dc2626'>{worst_rate:.1f}%</h2>", unsafe_allow_html=True)
            st.markdown(f"<div style='font-size:20px;font-weight:600'>{worst_proc}</div>", unsafe_allow_html=True)
            st.markdown(f"<div style='color:#6b7280'>{worst_pending} pending cases</div>", unsafe_allow_html=True)

        else:
            st.success("No Pending Cases")

        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ---------- OVERALL ---------- #

    c5, c6, c7 = st.columns(3)

    with c5:
        st.markdown(f"""
        <div class='card'>
            <div class='card-title'>Total Advised</div>
            <div class='card-value'>{total}</div>
        </div>
        """, unsafe_allow_html=True)

    with c6:
        st.markdown(f"""
        <div class='card'>
            <div class='card-title'>Total Converted</div>
            <div class='card-value'>{converted}</div>
        </div>
        """, unsafe_allow_html=True)

    with c7:
        st.markdown(f"""
        <div class='card'>
            <div class='card-title'>Pending</div>
            <div class='card-value'>{pending}</div>
        </div>
        """, unsafe_allow_html=True)


# ================== PATIENTS ================== #

elif choice == "Patients":

    st.markdown('<div class="page-title">Patient Management</div>', unsafe_allow_html=True)

    # -------- FETCH MASTER DATA -------- #

    cur.execute("SELECT name FROM procedures")
    procedures = [x[0] for x in cur.fetchall()]

    cur.execute("SELECT name FROM iol_types")
    iol_types = [x[0] for x in cur.fetchall()]

    cur.execute(
        "SELECT name FROM doctors WHERE hospital_id=%s",
        (st.session_state.hospital_id,)
    )
    doctors = [x[0] for x in cur.fetchall()]

    cur.execute(
        "SELECT name FROM counsellors WHERE hospital_id=%s",
        (st.session_state.hospital_id,)
    )
    counsellors = [x[0] for x in cur.fetchall()]

    vision_list = [
        "6/6","6/9","6/12","6/18","6/24",
        "6/36","6/60","HM","PLPR+","PLPR-"
    ]

    # ================= ADD PATIENT ================= #

    st.markdown("### Add Patient")

    col1, col2 = st.columns(2)

    with col1:
        name = st.text_input("Patient Name", key="p_name")
        phone = st.text_input("WhatsApp Number", key="p_phone")
        city = st.text_input("City", key="p_city")
        age = st.number_input("Age", 1, 120, key="p_age")
        gender = st.selectbox("Gender", ["Male","Female"], key="p_gender")

    with col2:
        vision_od = st.selectbox("Vision OD", vision_list, key="p_od")
        vision_os = st.selectbox("Vision OS", vision_list, key="p_os")

        procedure = st.selectbox("Procedure", procedures, key="p_procedure")

        # 🔥 IOL SHOW ONLY FOR CATARACT
        if procedure == "Cataract":
            iol = st.selectbox("IOL Type", iol_types, key="p_iol")
        else:
            iol = None

        doctor = st.selectbox(
            "Doctor",
            doctors if doctors else ["Not Added"],
            key="p_doctor"
        )

        counsellor = st.selectbox(
            "Counsellor",
            counsellors if counsellors else ["Not Added"],
            key="p_counsellor"
        )

        cost = st.number_input("Estimated Cost", key="p_cost")
        status = st.selectbox("Status", ["Pending","Converted"], key="p_status")

    if st.button("Save Patient", key="save_patient_btn"):

        patient_id = "PAT" + str(uuid.uuid4())[:6]

        cur.execute("""
            INSERT INTO patients
            (patient_id,name,phone,city,age,gender,
             vision_od,vision_os,procedure,iol,
             doctor,counsellor,cost,status,
             created_on,hospital_id)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
        """, (
            patient_id,name,phone,city,age,gender,
            vision_od,vision_os,procedure,iol,
            doctor,counsellor,cost,status,
            datetime.now(),
            st.session_state.hospital_id
        ))

        conn.commit()
        st.success("Patient Saved Successfully ✅")
        st.rerun()

    st.markdown("---")

    # ================= PATIENT RECORDS ================= #

    st.markdown("### Patient Records")

    search = st.text_input(
        "Search by Name / Phone / Patient ID",
        key="patient_search"
    )

    cur.execute("""
        SELECT patient_id,name,phone,procedure,iol,
               doctor,counsellor,cost,status
        FROM patients
        WHERE hospital_id=%s
        ORDER BY created_on DESC
    """, (st.session_state.hospital_id,))

    rows = cur.fetchall()

    df_patients = pd.DataFrame(rows, columns=[
        "Patient ID","Name","Phone","Procedure","IOL",
        "Doctor","Counsellor","Cost","Status"
    ])

    if search:
        df_patients = df_patients[
            df_patients["Name"].str.contains(search, case=False, na=False) |
            df_patients["Phone"].str.contains(search, case=False, na=False) |
            df_patients["Patient ID"].str.contains(search, case=False, na=False)
        ]

    if not df_patients.empty:

        csv = df_patients.to_csv(index=False).encode("utf-8")
        st.download_button(
            "Download Patient Report",
            csv,
            "patients_export.csv",
            "text/csv"
        )

        st.markdown("---")

        header = st.columns([1,2,1,1,1,1,1,1,2])
        header[0].markdown("**ID**")
        header[1].markdown("**Name**")
        header[2].markdown("**Procedure**")
        header[3].markdown("**IOL**")
        header[4].markdown("**Doctor**")
        header[5].markdown("**Counsellor**")
        header[6].markdown("**Cost**")
        header[7].markdown("**Status**")
        header[8].markdown("**Actions**")

        st.markdown("---")

        for _, row in df_patients.iterrows():

            cols = st.columns([1,2,1,1,1,1,1,1,2])

            cols[0].write(row["Patient ID"])
            cols[1].write(row["Name"])
            cols[2].write(row["Procedure"])
            cols[3].write(row["IOL"] if row["IOL"] else "-")
            cols[4].write(row["Doctor"])
            cols[5].write(row["Counsellor"])
            cols[6].write(f"₹{row['Cost']}")
            cols[7].write(row["Status"])

            if row["Status"] == "Pending":

                if cols[8].button(
                    "Convert",
                    key=f"convert_{row['Patient ID']}"
                ):
                    cur.execute(
                        "UPDATE patients SET status='Converted' WHERE patient_id=%s",
                        (row["Patient ID"],)
                    )
                    conn.commit()
                    st.rerun()

                msg = f"Dear {row['Name']}, reminder for your {row['Procedure']} treatment."
                encoded = urllib.parse.quote(msg)
                wa_link = f"https://wa.me/{row['Phone']}?text={encoded}"

                cols[8].markdown(f"[WA]({wa_link})")

    else:
        st.info("No patients found.")


# ================= DAILY REMINDERS ================= #

elif choice == "Daily Reminders":

    st.markdown("""
    <style>
    .bucket-card {
        padding:20px;
        border-radius:16px;
        text-align:center;
        cursor:pointer;
        border:2px solid transparent;
        transition:0.2s;
    }
    .bucket-card:hover {
        transform:scale(1.02);
    }
    .bucket-title {
        font-size:16px;
        font-weight:600;
        margin-bottom:10px;
    }
    .bucket-count {
        font-size:32px;
        font-weight:700;
    }
    .bucket-sub {
        font-size:13px;
        margin-top:8px;
        color:#6b7280;
    }
    .section-card {
        background:white;
        padding:20px;
        border-radius:18px;
        box-shadow:0 6px 20px rgba(0,0,0,0.06);
    }
    </style>
    """, unsafe_allow_html=True)

    st.markdown("## Daily Reminders & Follow-ups")
    st.caption("AI-powered priority patient follow-up")

    # ---------------- FETCH DATA ---------------- #

    cur.execute("""
        SELECT patient_id, name, phone, procedure, cost, created_on
        FROM patients
        WHERE hospital_id=%s AND status='Pending'
        ORDER BY created_on DESC
    """, (st.session_state.hospital_id,))

    rows = cur.fetchall()

    if rows:
        df_pending = pd.DataFrame(rows, columns=[
            "patient_id","name","phone","procedure","cost","created_on"
        ])
        df_pending["created_on"] = pd.to_datetime(df_pending["created_on"])
        df_pending["Days"] = (pd.Timestamp.now() - df_pending["created_on"]).dt.days
    else:
        df_pending = pd.DataFrame(columns=[
            "patient_id","name","phone","procedure","cost","created_on","Days"
        ])

    # ---------------- BUCKETS ---------------- #

    bucket1 = df_pending[df_pending["Days"] <= 15]
    bucket2 = df_pending[(df_pending["Days"] > 15) & (df_pending["Days"] <= 30)]
    bucket3 = df_pending[(df_pending["Days"] > 30) & (df_pending["Days"] <= 60)]
    bucket4 = df_pending[(df_pending["Days"] > 60) & (df_pending["Days"] <= 90)]
    bucket5 = df_pending[df_pending["Days"] > 90]

    buckets = {
        "0-15 days": (bucket1, "#dbeafe"),
        "15-30 days": (bucket2, "#ccfbf1"),
        "30-60 days": (bucket3, "#fef9c3"),
        "60-90 days": (bucket4, "#ffedd5"),
        "90+ days": (bucket5, "#fee2e2"),
    }

    if "rem_filter" not in st.session_state:
        st.session_state.rem_filter = "all"

    # ---------------- BUCKET UI ---------------- #

    cols = st.columns(5)

    for i, (label, (data, color)) in enumerate(buckets.items()):
        with cols[i]:
            if st.button(f"{label}_{i}", key=f"bucket_{i}", use_container_width=True):
                st.session_state.rem_filter = label

            st.markdown(f"""
            <div class='bucket-card' style='background:{color};'>
                <div class='bucket-title'>{label}</div>
                <div class='bucket-count'>{len(data)}</div>
                <div class='bucket-sub'>Click to filter</div>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ---------------- FILTER LOGIC ---------------- #

    if st.session_state.rem_filter == "all":
        filtered = df_pending
    else:
        filtered = buckets[st.session_state.rem_filter][0]

    # ---------------- EXPORT ---------------- #

    colA, colB = st.columns([8,2])
    with colB:
        if not filtered.empty:
            csv = filtered.to_csv(index=False).encode("utf-8")
            st.download_button(
                "⬇ Export Filtered",
                csv,
                "pending_patients.csv",
                "text/csv",
                use_container_width=True
            )

    # ---------------- TABLE ---------------- #

    st.markdown("<div class='section-card'>", unsafe_allow_html=True)
    st.markdown(f"### Pending Patients ({len(filtered)})")

    if not filtered.empty:

        header = st.columns([3,2,1,2,2])
        header[0].markdown("**Patient Details**")
        header[1].markdown("**Category / Cost**")
        header[2].markdown("**Days Pending**")
        header[3].markdown("**AI Recommendation**")
        header[4].markdown("**WhatsApp Actions**")

        st.markdown("---")

        for _, row in filtered.iterrows():

            c1,c2,c3,c4,c5 = st.columns([3,2,1,2,2])

            c1.markdown(f"**{row['name']}**")
            c1.caption(row["phone"])

            c2.markdown(row["procedure"])
            c2.caption(f"₹{row['cost']}")

            c3.markdown(str(row["Days"]))

            if row["Days"] > 60:
                c4.error("High Priority")
            elif row["Days"] > 30:
                c4.warning("Moderate Priority")
            else:
                c4.success("Normal")

            msg = f"Dear {row['name']}, this is a reminder for your {row['procedure']} treatment. Please contact us."
            encoded = urllib.parse.quote(msg)
            wa_link = f"https://wa.me/{row['phone']}?text={encoded}"

            btn1, btn2 = c5.columns(2)

            if btn1.button("Convert", key=f"conv_{row['patient_id']}"):
                cur.execute(
                    "UPDATE patients SET status='Converted' WHERE patient_id=%s",
                    (row["patient_id"],)
                )
                conn.commit()
                st.rerun()

            btn2.markdown(f"[WA]({wa_link})")

    else:
        st.info("No pending patients in this filter")

    st.markdown("</div>", unsafe_allow_html=True)

# ================== CONVERSION ================== #

elif choice == "Conversion":

    st.markdown('<div class="page-title">Conversion Analytics</div>', unsafe_allow_html=True)
    st.markdown('<div class="page-sub">Analyze conversion patterns and trends</div>', unsafe_allow_html=True)

    # ---- FETCH DATA ---- #
    cur.execute("""
        SELECT procedure,
               COUNT(*) AS total,
               SUM(CASE WHEN status='Converted' THEN 1 ELSE 0 END) AS converted,
               SUM(CASE WHEN status='Pending' THEN 1 ELSE 0 END) AS pending
        FROM patients
        WHERE hospital_id=%s
        GROUP BY procedure
    """, (st.session_state.hospital_id,))

    rows = cur.fetchall()

    if not rows:
        st.info("No data available")
        st.stop()

    df_conv = pd.DataFrame(rows, columns=[
        "procedure", "total", "converted", "pending"
    ])

    df_conv["conversion_rate"] = (
        df_conv["converted"] / df_conv["total"] * 100
    ).round(1)

    # ---- CHART ---- #
    fig = px.bar(
        df_conv,
        x="procedure",
        y="conversion_rate",
        text="conversion_rate",
        labels={"conversion_rate": "Conversion %"},
    )

    fig.update_traces(texttemplate="%{text}%", textposition="outside")
    fig.update_layout(yaxis_range=[0, 100])

    st.plotly_chart(fig, use_container_width=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ---- KPI CARDS GRID ---- #

    cols = st.columns(2)

    for i, row in df_conv.iterrows():

        col = cols[i % 2]

        with col:

            st.markdown("""
                <div style="
                    background:white;
                    padding:25px;
                    border-radius:16px;
                    box-shadow:0 6px 20px rgba(0,0,0,0.08);
                ">
            """, unsafe_allow_html=True)

            # Procedure Title
            st.markdown(f"### {row['procedure']}")

            # Big Conversion %
            st.markdown(
                f"<h1 style='color:#ef4444;margin-bottom:5px;'>{row['conversion_rate']}%</h1>",
                unsafe_allow_html=True
            )

            st.markdown("<div style='color:#6b7280;margin-bottom:20px;'>conversion</div>",
                        unsafe_allow_html=True)

            # Bottom Metrics Row
            m1, m2, m3 = st.columns(3)

            m1.markdown(f"Total<br><strong>{int(row['total'])}</strong>", unsafe_allow_html=True)
            m2.markdown(
                f"<span style='color:#059669;'>Converted<br><strong>{int(row['converted'])}</strong></span>",
                unsafe_allow_html=True
            )
            m3.markdown(
                f"<span style='color:#f97316;'>Pending<br><strong>{int(row['pending'])}</strong></span>",
                unsafe_allow_html=True
            )

            st.markdown("</div>", unsafe_allow_html=True)
            st.markdown("<br>", unsafe_allow_html=True)


# ================== REVENUE ================== #

elif choice == "Revenue":

    if st.session_state.role != "hospital_admin":
        st.warning("Access Restricted")
        st.stop()

    st.markdown('<div class="page-title">Revenue Overview</div>', unsafe_allow_html=True)

    total = df["cost"].sum()
    collected = df[df["status"] == "Converted"]["cost"].sum()
    pending_rev = df[df["status"] == "Pending"]["cost"].sum()

    c1,c2,c3 = st.columns(3)
    c1.metric("Total Advised", f"₹{total:,.0f}")
    c2.metric("Collected", f"₹{collected:,.0f}")
    c3.metric("Pending", f"₹{pending_rev:,.0f}")

    fig = px.bar(df, x="procedure", y="cost", color="status")
    st.plotly_chart(fig, use_container_width=True)


# ================== MASTER CONTROL ================== #

elif choice == "Master Control":

    if st.session_state.role != "master":
        st.warning("Access Restricted")
        st.stop()

    st.markdown('<div class="page-title">Master SaaS Control Panel</div>', unsafe_allow_html=True)

    st.markdown("### Create New Hospital")

    hospital_name = st.text_input("Hospital Name")
    subscription_status = st.selectbox("Subscription", ["active","inactive"])

    if st.button("Create Hospital"):

        cur.execute(
            "INSERT INTO hospitals (name, subscription) VALUES (%s,%s)",
            (hospital_name, subscription_status)
        )
        conn.commit()

        st.success("Hospital Created")
        st.rerun()

    st.markdown("---")
    st.markdown("### Existing Hospitals")

    cur.execute("SELECT id,name,subscription FROM hospitals")
    hospitals = cur.fetchall()

    for h in hospitals:

        col1,col2,col3 = st.columns([3,1,1])

        col1.write(f"**{h[1]}**")
        col2.write(h[2])

        if col3.button("Toggle", key=h[0]):
            new_status = "inactive" if h[2]=="active" else "active"
            cur.execute(
                "UPDATE hospitals SET subscription=%s WHERE id=%s",
                (new_status, h[0])
            )
            conn.commit()
            st.rerun()

    st.markdown("---")
    st.markdown("### Create Hospital Admin")

    cur.execute("SELECT id,name FROM hospitals")
    hospital_list = cur.fetchall()

    hospital_options = {h[1]:h[0] for h in hospital_list}

    selected_hospital = st.selectbox("Select Hospital", list(hospital_options.keys()))
    admin_username = st.text_input("Admin Username")
    admin_password = st.text_input("Admin Password")

    if st.button("Create Hospital Admin"):

        cur.execute(
            "INSERT INTO users (username,password,role,hospital_id) VALUES (%s,%s,%s,%s)",
            (admin_username, admin_password, "hospital_admin", hospital_options[selected_hospital])
        )
        conn.commit()

        st.success("Hospital Admin Created")
        st.rerun()

# ================= PENDING ================= #

elif choice == "Pending":

    st.markdown("""
    <div class='page-title'>Pending Patients Tracker</div>
    <div class='page-sub'>Monitor ageing and follow-up priorities</div>
    """, unsafe_allow_html=True)

    # ---------- FETCH DATA ---------- #

    cur.execute("""
        SELECT patient_id,name,phone,procedure,doctor,cost,status,created_on
        FROM patients
        WHERE hospital_id=%s AND status='Pending'
        ORDER BY created_on DESC
    """, (st.session_state.hospital_id,))

    rows = cur.fetchall()

    if not rows:
        st.info("No pending patients.")
        st.stop()

    df_pending = pd.DataFrame(rows, columns=[
        "patient_id",
        "name",
        "phone",
        "procedure",
        "doctor",
        "cost",
        "status",
        "created_on"
    ])

    df_pending["created_on"] = pd.to_datetime(df_pending["created_on"])
    df_pending["Days"] = (pd.Timestamp.now() - df_pending["created_on"]).dt.days

  
    # ---------- TABLE ---------- #

    st.markdown("### Pending Patients")

    display_df = df_pending[[
        "patient_id",
        "name",
        "procedure",
        "doctor",
        "cost",
        "Days"
    ]]

    st.dataframe(display_df, use_container_width=True)

    csv = display_df.to_csv(index=False).encode("utf-8")

    st.download_button(
        "Download Pending Report",
        csv,
        "pending_patients.csv",
        "text/csv"
    )

# ================= DOCTORS ================= #

elif choice == "Doctors":

    st.markdown("""
    <div class='page-title'>Doctor Performance</div>
    <div class='page-sub'>Compare conversion rates and revenue by doctor</div>
    """, unsafe_allow_html=True)

    cur.execute("""
        SELECT doctor,
               COUNT(*) as total_cases,
               SUM(CASE WHEN status='Converted' THEN 1 ELSE 0 END) as converted,
               SUM(cost) as revenue
        FROM patients
        WHERE hospital_id=%s
        GROUP BY doctor
    """, (st.session_state.hospital_id,))
    
    rows = cur.fetchall()

    if not rows:
        st.info("No doctor data available.")
        st.stop()

    df_doc = pd.DataFrame(rows, columns=[
        "doctor","total_cases","converted","revenue"
    ])

    df_doc["conversion_rate"] = (
        df_doc["converted"] / df_doc["total_cases"] * 100
    ).round(1)

    df_doc["revenue"] = df_doc["revenue"].fillna(0)

    # -------- TOP PERFORMER -------- #

    top_doc = df_doc.sort_values("conversion_rate", ascending=False).iloc[0]

    st.markdown("""
    <div class='card' style='background:#e6f4f1;'>
    """, unsafe_allow_html=True)

    st.markdown("### 🏆 Top Performer")
    st.markdown(f"## {top_doc['doctor']}")
    st.markdown(f"""
    Conversion Rate: **{top_doc['conversion_rate']}%**  
    Revenue: **₹{top_doc['revenue']:,.0f}**
    """)

    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # -------- ALL DOCTORS CARDS -------- #

    for _, row in df_doc.iterrows():

        st.markdown("<div class='card'>", unsafe_allow_html=True)

        col1, col2, col3 = st.columns(3)

        col1.metric("Total Cases", row["total_cases"])
        col2.metric("Conversion %", f"{row['conversion_rate']}%")
        col3.metric("Revenue", f"₹{row['revenue']:,.0f}")

        st.markdown(f"### 👨‍⚕️ {row['doctor']}")

        st.markdown("</div>", unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)

# ================= SETTINGS ================= #

elif choice == "Settings":

    # 🔐 Restrict to Master Only
    if st.session_state.role != "master":
        st.stop()

    st.markdown("""
    <div class='page-title'>Hospital Settings</div>
    <div class='page-sub'>Control hospital configuration & master data</div>
    """, unsafe_allow_html=True)

    # -------- HOSPITAL INFO -------- #

    cur.execute(
        "SELECT name, subscription FROM hospitals WHERE id=%s",
        (st.session_state.hospital_id,)
    )
    hospital = cur.fetchone()

    st.markdown("### 🏥 Hospital Information")

    new_name = st.text_input("Hospital Name", value=hospital[0])

    subscription = st.selectbox(
        "Subscription Status",
        ["active", "inactive"],
        index=0 if hospital[1] == "active" else 1
    )

    if st.button("Save Hospital Settings"):

        cur.execute("""
            UPDATE hospitals
            SET name=%s, subscription=%s
            WHERE id=%s
        """, (
            new_name,
            subscription,
            st.session_state.hospital_id
        ))

        conn.commit()
        st.success("Hospital Settings Updated ✅")
        st.rerun()


    # -------- ADD DOCTOR -------- #

    st.markdown("### 👨‍⚕️ Doctors")

    new_doc = st.text_input("Add Doctor")

    if st.button("Add Doctor"):
        if new_doc:
            cur.execute("""
                INSERT INTO doctors (name, hospital_id)
                VALUES (%s,%s)
            """, (new_doc, st.session_state.hospital_id))
            conn.commit()
            st.success("Doctor Added ✅")
            st.rerun()

    cur.execute("""
        SELECT id, name FROM doctors
        WHERE hospital_id=%s
    """, (st.session_state.hospital_id,))
    docs = cur.fetchall()

    for d in docs:
        col1, col2 = st.columns([4,1])
        col1.write(d[1])
        if col2.button("Delete", key=f"doc_{d[0]}"):
            cur.execute("DELETE FROM doctors WHERE id=%s", (d[0],))
            conn.commit()
            st.rerun()

    st.markdown("---")

    # -------- ADD COUNSELLOR -------- #

    st.markdown("### 🧑‍💼 Counsellors")

    new_coun = st.text_input("Add Counsellor")

    if st.button("Add Counsellor"):
        if new_coun:
            cur.execute("""
                INSERT INTO counsellors (name, hospital_id)
                VALUES (%s,%s)
            """, (new_coun, st.session_state.hospital_id))
            conn.commit()
            st.success("Counsellor Added ✅")
            st.rerun()

    cur.execute("""
        SELECT id, name FROM counsellors
        WHERE hospital_id=%s
    """, (st.session_state.hospital_id,))
    couns = cur.fetchall()

    for c in couns:
        col1, col2 = st.columns([4,1])
        col1.write(c[1])
        if col2.button("Delete", key=f"coun_{c[0]}"):
            cur.execute("DELETE FROM counsellors WHERE id=%s", (c[0],))
            conn.commit()
            st.rerun()

    st.markdown("---")

    # -------- PROCEDURES -------- #

    st.markdown("### 🏥 Procedures")

    new_proc = st.text_input("Add Procedure")

    if st.button("Add Procedure"):
        if new_proc:
            cur.execute("INSERT INTO procedures (name) VALUES (%s)", (new_proc,))
            conn.commit()
            st.success("Procedure Added ✅")
            st.rerun()

    cur.execute("SELECT id, name FROM procedures")
    procs = cur.fetchall()

    for p in procs:
        col1, col2 = st.columns([4,1])
        col1.write(p[1])
        if col2.button("Delete", key=f"proc_{p[0]}"):
            cur.execute("DELETE FROM procedures WHERE id=%s", (p[0],))
            conn.commit()
            st.rerun()

    st.markdown("---")

    # -------- IOL TYPES -------- #

    st.markdown("### 👁 IOL Types")

    new_iol = st.text_input("Add IOL Type")

    if st.button("Add IOL"):
        if new_iol:
            cur.execute("INSERT INTO iol_types (name) VALUES (%s)", (new_iol,))
            conn.commit()
            st.success("IOL Type Added ✅")
            st.rerun()

    cur.execute("SELECT id, name FROM iol_types")
    iols = cur.fetchall()

    for i in iols:
        col1, col2 = st.columns([4,1])
        col1.write(i[1])
        if col2.button("Delete", key=f"iol_{i[0]}"):
            cur.execute("DELETE FROM iol_types WHERE id=%s", (i[0],))
            conn.commit()
            st.rerun()


# ================= DEMOGRAPHICS ================= #

elif choice == "Demographics":

    st.markdown("## Patient Demographics Intelligence")

    if not df.empty:

        # AGE GROUPS
        bins = [0,20,40,60,80,120]
        labels = ["0-20","21-40","41-60","61-80","80+"]

        df["age_group"] = pd.cut(df["age"], bins=bins, labels=labels)

        col1,col2 = st.columns(2)

        with col1:
            st.markdown("### Age Distribution")
            age_group = df["age_group"].value_counts().reset_index()
            age_group.columns=["Age Group","Count"]
            fig_age = px.bar(age_group, x="Age Group", y="Count")
            st.plotly_chart(fig_age, use_container_width=True)

        with col2:
            st.markdown("### Gender Distribution")
            fig_gender = px.pie(df, names="gender")
            st.plotly_chart(fig_gender, use_container_width=True)

        st.markdown("### City Analysis")
        city_group = df["city"].value_counts().reset_index()
        city_group.columns=["City","Patients"]
        fig_city = px.bar(city_group, x="City", y="Patients")
        st.plotly_chart(fig_city, use_container_width=True)

    else:
        st.info("No data available for demographics")
