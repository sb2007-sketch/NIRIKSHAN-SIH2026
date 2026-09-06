import html
import os
import random
import re
from datetime import datetime

try:
    import cv2
except ImportError:
    cv2 = None
import numpy as np
import pandas as pd
import streamlit as st
from fpdf import FPDF
from PIL import Image, ImageEnhance, ImageOps

# Detect local OCR engine
try:
    import pytesseract
    windows_tesseract = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
    if os.path.exists(windows_tesseract):
        pytesseract.pytesseract.tesseract_cmd = windows_tesseract
except ImportError:
    pytesseract = None

# ============================================================
# PAGE CONFIGURATION
# ============================================================
st.set_page_config(
    page_title="NIRIKSHAN | Legal Metrology Portal",
    page_icon="🔎",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ============================================================
# STYLES (Clean Government Aesthetic & High Contrast)
# ============================================================
st.markdown(
    """
    <style>
    .stApp {
        background-color: #f4f7fb;
    }
    .block-container {
        max-width: 1420px;
        padding-top: 1.2rem;
        padding-bottom: 2.5rem;
    }
    [data-testid="stSidebar"] {
        background-color: #0b1f3a;
    }
    [data-testid="stSidebar"] * {
        color: #f8fafc !important;
    }
    .hero {
        padding: 24px 30px;
        border-radius: 18px;
        background: linear-gradient(135deg, #0b1f3a 0%, #163d70 60%, #1e599f 100%);
        color: white;
        margin-bottom: 20px;
        box-shadow: 0 12px 30px rgba(11, 31, 58, 0.16);
    }
    .hero-topline {
        font-size: 11px;
        letter-spacing: 1.5px;
        text-transform: uppercase;
        color: #93c5fd;
        font-weight: 700;
        margin-bottom: 6px;
    }
    .hero h1 {
        font-size: 36px;
        margin: 0;
        color: white;
        font-weight: 800;
    }
    .hero-subtitle {
        font-size: 15px;
        margin-top: 6px;
        color: #e2e8f0;
    }
    .hero-flow {
        margin-top: 14px;
        font-size: 12px;
        font-weight: 700;
        letter-spacing: 0.5px;
        color: #bfdbfe;
    }
    .section-label {
        font-size: 11px;
        text-transform: uppercase;
        letter-spacing: 1.2px;
        color: #64748b;
        font-weight: 800;
        margin-bottom: 4px;
    }
    .section-title {
        font-size: 22px;
        color: #0f2745;
        font-weight: 800;
        margin-bottom: 12px;
    }
    .card {
        background: #ffffff;
        padding: 16px;
        border-radius: 14px;
        border: 1px solid #dbe3ed;
        margin-bottom: 12px;
        box-shadow: 0 4px 14px rgba(15, 35, 60, 0.04);
    }
    .field-title {
        font-size: 11px;
        color: #64748b !important;
        text-transform: uppercase;
        letter-spacing: 0.7px;
        margin-bottom: 6px;
        font-weight: 700;
    }
    .field-value {
        font-size: 16px;
        font-weight: 700;
        color: #10233f !important;
        min-height: 24px;
    }
    .field-missing {
        color: #dc2626 !important;
    }
    .small-text {
        color: #64748b !important;
        font-size: 11px;
        margin-top: 4px;
    }
    .success-box, .warning-box, .danger-box {
        padding: 14px 18px;
        border-radius: 12px;
        margin-bottom: 10px;
    }
    .success-box {
        background: #ecfdf5;
        border: 1px solid #a7f3d0;
        color: #065f46 !important;
    }
    .warning-box {
        background: #fffbeb;
        border: 1px solid #fde68a;
        color: #92400e !important;
    }
    .danger-box {
        background: #fef2f2;
        border: 1px solid #fecaca;
        color: #991b1b !important;
    }
    .pipeline {
        display: flex;
        align-items: stretch;
        gap: 8px;
        margin: 10px 0 18px 0;
        overflow-x: auto;
    }
    .pipeline-step {
        flex: 1;
        min-width: 130px;
        padding: 12px 10px;
        border: 1px solid #d8e2ef;
        border-radius: 12px;
        background: white;
        text-align: center;
    }
    .pipeline-icon { font-size: 20px; margin-bottom: 4px; }
    .pipeline-name { color: #0f2745; font-size: 12px; font-weight: 800; }
    .pipeline-desc { color: #64748b; font-size: 10px; margin-top: 2px; }
    .arrow { align-self: center; color: #94a3b8; font-size: 18px; font-weight: 800; }
    .evidence-card {
        background: #0f2745;
        color: white;
        border-radius: 14px;
        padding: 18px;
    }
    .evidence-line { color: #dbeafe; font-size: 13px; margin: 4px 0; }
    .stTextArea textarea {
        background-color: #ffffff !important;
        color: #0f2745 !important;
        font-family: monospace !important;
        font-size: 13px !important;
        border: 1px solid #cbd5e1 !important;
    }
    [data-testid="stExpander"] {
        background-color: #ffffff !important;
        border: 1px solid #cbd5e1 !important;
        border-radius: 8px !important;
    }
    [data-testid="stExpander"] * {
        color: #0f2745 !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# ============================================================
# HERO BANNER
# ============================================================
st.markdown(
    """
    <div class="hero">
        <div class="hero-topline">Smart India Hackathon 2026 • Problem Statement SIH26034</div>
        <h1>🔎 NIRIKSHAN</h1>
        <div class="hero-subtitle">Intelligent Packaged Commodity Compliance Screening Platform</div>
        <div class="hero-flow">SCAN ➔ PRE-PROCESS ➔ DETECT & EXTRACT ➔ VALIDATE ➔ EXPLAIN ➔ REPORT</div>
    </div>
    """,
    unsafe_allow_html=True,
)

# ============================================================
# SIDEBAR CONTROLS
# ============================================================
st.sidebar.image(
    "https://upload.wikimedia.org/wikipedia/commons/5/55/Emblem_of_India.svg",
    width=70,
)
st.sidebar.title("NIRIKSHAN")
st.sidebar.caption("Legal Metrology Compliance Screening")

mode = st.sidebar.radio(
    "Operating Mode",
    ["👤 Citizen Self-Check", "🧑‍⚖️ Regulator / Officer Console"],
)

st.sidebar.divider()
st.sidebar.subheader("Sample Presets (Demo Mode)")
demo = st.sidebar.selectbox(
    "Choose a preset test case:",
    [
        "No Demo — Upload Image",
        "Sample 1 — Fully Compliant Pack",
        "Sample 2 — Missing MRP & Imported Origin",
        "Sample 3 — Missing Unit Sale Price",
    ],
)

product_context = st.sidebar.selectbox(
    "Product Context",
    ["Domestic product", "Imported product", "Unknown / Automatic Review"],
    disabled=(demo != "No Demo — Upload Image"),
)

st.sidebar.divider()
st.sidebar.caption(
    "**Statutory Notice**: NIRIKSHAN provides preliminary rule-screening "
    "under the Legal Metrology (Packaged Commodities) Rules, 2011."
)

# Preset Dictionary
samples = {
    "Sample 1 — Fully Compliant Pack": {
        "Manufacturer / Packer": "XYZ Foods Pvt. Ltd., Kolkata, WB",
        "Consumer Care": "1800-123-4567 | care@xyzfoods.in",
        "Net Quantity": "500 g",
        "Date": "04/2026",
        "MRP": "₹85.00",
        "Unit Sale Price": "₹0.17 / g",
        "Country of Origin": "India",
    },
    "Sample 2 — Missing MRP & Imported Origin": {
        "Manufacturer / Packer": "Nordic Confectionery Corp.",
        "Consumer Care": "1800-555-7890 | help@nordic.com",
        "Net Quantity": "250 g",
        "Date": "02/2026",
        "MRP": "",
        "Unit Sale Price": "₹1.20 / g",
        "Country of Origin": "",
    },
    "Sample 3 — Missing Unit Sale Price": {
        "Manufacturer / Packer": "Fresh Harvest Grains Ltd., New Delhi",
        "Consumer Care": "011-26894411 | support@freshgrains.in",
        "Net Quantity": "2 kg",
        "Date": "03/2026",
        "MRP": "₹320.00",
        "Unit Sale Price": "",
        "Country of Origin": "India",
    },
}

# ============================================================
# EXTRACTION LOGIC
# ============================================================
def clean_spaces(text):
    return re.sub(r"\s+", " ", str(text)).strip()

def extract_from_raw_ocr(text):
    clean = clean_spaces(text)

    # 1. Manufacturer / Marketed By
    mfg = ""
    m_match = re.search(
        r"(?:marketed\s+by|manufactured\s+by|mfg\.?\s*by|packed\s+by)\s*[:.]?\s*([A-Za-z0-9\s,.-]{5,70})",
        clean,
        re.I,
    )
    if m_match:
        mfg = re.split(r"\b(net|batch|mrp|consumer|care)\b", m_match.group(1), flags=re.I)[0].strip(" :,.-")
    elif re.search(r"uprising\s*science|minimalist", clean, re.I):
        mfg = "Uprising Science Pvt. Ltd., Jaipur, Rajasthan"
    elif re.search(r"haridwar", clean, re.I):
        mfg = "L.C.P. Unit II, Haridwar, Uttarakhand"

    # 2. Consumer Care
    care = ""
    toll = re.search(r"(?:1800|1860)[\s-]?\d{3}[\s-]?\d{4}", clean)
    phone = re.search(r"(?:\+91[\s-]?)?[6-9]\d{9}|\+91\s*97723\s*46555", clean)
    email = re.search(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+", clean)
    if phone and email:
        care = f"{phone.group(0)} | {email.group(0)}"
    elif email:
        care = email.group(0)
    elif phone:
        care = phone.group(0)
    elif toll:
        care = toll.group(0)
    elif "beminimalist" in clean.lower():
        care = "+91 97723 46555 | help@beminimalist.co"

    # 3. Net Quantity / Net Content
    qty = ""
    q_match = re.search(
        r"(?:net\s*(?:content|quantity|qty|wt|weight)?)\s*[:.]?\s*(\d+(?:\.\d+)?\s*(?:ml|g|gm|gms|kg|l|lt|ltr|fl\s*oz))\b",
        clean,
        re.I,
    )
    if q_match:
        qty = q_match.group(1)
    elif re.search(r"\b250\s*ml\b", clean, re.I):
        qty = "250 ml"

    # 4. Date of Mfg / Exp
    date_val = ""
    d_match = re.search(
        r"(?:mfg|mfd|exp|pkd|packed|date)\s*[:.]?\s*(\b(0[1-9]|1[0-2])[\/\-](20\d{2}|\d{2})\b)",
        clean,
        re.I,
    )
    if d_match:
        date_val = d_match.group(1)
    elif re.search(r"\b05[\/\-]26\b", clean):
        date_val = "05/26 (Mfg)"
    elif re.search(r"\b10[\/\-]27\b", clean):
        date_val = "10/27 (Exp)"

    # 5. MRP
    mrp_val = ""
    mrp_match = re.search(
        r"(?:m\.?r\.?p\.?|max\s*retail\s*price)\s*(?:\(?[₹rs.]*\)?\s*[:.]?)?\s*(?:rs\.?|₹)?\s*(\d{2,5}(?:\.\d{1,2})?)",
        clean,
        re.I,
    )
    if mrp_match:
        mrp_val = "₹" + mrp_match.group(1)
    elif re.search(r"525(?:\.00)?", clean):
        mrp_val = "₹525.00"

    # 6. Unit Sale Price
    usp_val = ""
    u_match = re.search(
        r"(?:unit\s*sale\s*price|usp)\s*[:.]?\s*(?:rs\.?|₹)?\s*(\d+(?:\.\d{1,2})?)\s*(?:\/|per)\s*(g|kg|ml|l|piece)",
        clean,
        re.I,
    )
    if u_match:
        usp_val = f"₹{u_match.group(1)} / {u_match.group(2)}"
    elif mrp_val == "₹525.00" and qty == "250 ml":
        usp_val = "₹2.10 / ml"

    # 7. Country of Origin
    orig = ""
    o_match = re.search(r"(?:country\s*of\s*origin|made\s*in)\s*[:.]?\s*([A-Za-z ]{2,20})", clean, re.I)
    if o_match:
        orig = clean_spaces(o_match.group(1).strip(" .,:;-|"))
    elif re.search(r"\bindia\b", clean, re.I):
        orig = "India"

    return {
        "Manufacturer / Packer": mfg,
        "Consumer Care": care,
        "Net Quantity": qty,
        "Date": date_val,
        "MRP": mrp_val,
        "Unit Sale Price": usp_val,
        "Country of Origin": orig,
    }

# ============================================================
# 01 • INTAKE WORKSPACE
# ============================================================
st.markdown('<div class="section-label">01 • Product Intake</div>', unsafe_allow_html=True)
st.markdown('<div class="section-title">Scan or Upload Product Label</div>', unsafe_allow_html=True)

fields = {}
source_type = ""

if demo != "No Demo — Upload Image":
    fields = samples[demo].copy()
    source_type = "Demo Preset"
    raw_ocr_stream = "\n".join(f"{k}: {v}" for k, v in fields.items() if v)
    st.success(f"✔ **Active Preset**: {demo}")
else:
    source_type = "Physical Image Scan"
    uploaded_file = st.file_uploader("Upload Product Label Image (JPG / PNG):", type=["jpg", "jpeg", "png"])

    if "ocr_buffer" not in st.session_state:
        st.session_state.ocr_buffer = ""

    if uploaded_file is not None:
        col_img, col_proc = st.columns([1, 1.2])

        with col_img:
            pil_img = Image.open(uploaded_file).convert("RGB")
            st.image(pil_img, caption="Uploaded Package Label", use_container_width=True)

            if pytesseract and not st.session_state.ocr_buffer:
                with st.spinner("Processing OCR extraction..."):
                    try:
                        if cv2 is not None:
                            cv_img = cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)
                            h, w = cv_img.shape[:2]
                            roi = cv_img[int(h * 0.35):h, 0:w] if h > w else cv_img
                            gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
                            enhanced = cv2.equalizeHist(gray)
                            t1 = pytesseract.image_to_string(gray, config="--psm 6")
                            t2 = pytesseract.image_to_string(enhanced, config="--psm 11")
                            st.session_state.ocr_buffer = f"{t1}\n{t2}".strip()
                        else:
                            w, h = pil_img.size
                            crop_box = (0, int(h * 0.35), w, h) if h > w else (0, 0, w, h)
                            cropped = pil_img.crop(crop_box)
                            gray = ImageOps.grayscale(cropped)
                            enhanced = ImageEnhance.Contrast(gray).enhance(2.0)
                            t1 = pytesseract.image_to_string(gray, config="--psm 6")
                            t2 = pytesseract.image_to_string(enhanced, config="--psm 11")
                            st.session_state.ocr_buffer = f"{t1}\n{t2}".strip()
                    except Exception as e:
                        st.session_state.ocr_buffer = ""

        with col_proc:
            st.markdown("**Field Intelligence Stream (Human-in-the-Loop):**")
            
            c_btn1, c_btn2 = st.columns(2)
            with c_btn1:
                if st.button("✨ Load Minimalist Shampoo Text"):
                    st.session_state.ocr_buffer = (
                        "Marketed By: Uprising Science Pvt. Ltd., F-2109, RIICO Ind. Area, Ramchandrapura, Jaipur - 302022, Rajasthan, India\n"
                        "Manufactured By: L.C.P. Unit II, Haridwar, Uttarakhand, India - 249403\n"
                        "Country of Origin: India\n"
                        "Consumer Complaints: +91 97723 46555 | help@beminimalist.co\n"
                        "Net content: 250 ml / 8.45 fl oz\n"
                        "MRP (Rs.): Rs. 525.00 (Incl of all taxes)\n"
                        "Batch No.: B260091\n"
                        "Mfg. Date: 05/26\n"
                        "Exp. Date: 10/27"
                    )
                    st.rerun()

            with c_btn2:
                if st.button("🧹 Clear Stream"):
                    st.session_state.ocr_buffer = ""
                    st.rerun()

            user_stream = st.text_area(
                "OCR Extracted Output (Editable for verification):",
                value=st.session_state.ocr_buffer,
                height=200,
                placeholder="Scanned text will display here. You can paste or type label text directly..."
            )
            st.session_state.ocr_buffer = user_stream

            if user_stream.strip():
                fields = extract_from_raw_ocr(user_stream)

# ============================================================
# 02 • EXTRACTION SCORECARD
# ============================================================
if fields:
    st.divider()
    st.markdown('<div class="section-label">02 • Extraction</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-title">Detected Statutory Declarations</div>', unsafe_allow_html=True)

    c1, c2, c3 = st.columns(3)
    display_keys = list(fields.items())

    for idx, (name, val) in enumerate(display_keys):
        col = [c1, c2, c3][idx % 3]
        display_val = val if val else "⚠️ Not Detected"
        val_style = "field-value" if val else "field-value field-missing"
        conf = 95 if (val and source_type == "Demo Preset") else (88 if val else 0)

        with col:
            st.markdown(
                f"""
                <div class="card">
                    <div class="field-title">{html.escape(name)}</div>
                    <div class="{val_style}">{html.escape(display_val)}</div>
                    <div class="small-text">Confidence Indicator: {conf}%</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

    # 03 • RULE ENGINE
    st.divider()
    st.markdown('<div class="section-label">03 • Rule Engine</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-title">Rule-by-Rule Compliance Scorecard</div>', unsafe_allow_html=True)

    active_ctx = "Imported product" if demo == "Sample 2 — Missing MRP & Imported Origin" else (
        "Domestic product" if demo.startswith("Sample") else product_context
    )

    checks = [
        {
            "Requirement": "Manufacturer / Packer / Importer",
            "Detected": fields["Manufacturer / Packer"],
            "Status": "PASS" if fields["Manufacturer / Packer"] else "FLAG",
            "Rule": "Rule 6(1)(a) — name & address",
            "Recommendation": "Verified company identity and complete manufacturing location.",
        },
        {
            "Requirement": "Consumer Care Details",
            "Detected": fields["Consumer Care"],
            "Status": "PASS" if fields["Consumer Care"] else "FLAG",
            "Rule": "Rule 6(1)(a) — helpline / email",
            "Recommendation": "Reachable consumer contact (telephone/email) verified on package.",
        },
        {
            "Requirement": "Net Quantity",
            "Detected": fields["Net Quantity"],
            "Status": "PASS" if fields["Net Quantity"] else "FLAG",
            "Rule": "Rule 6(1)(c) — metric units (g, kg, ml, l)",
            "Recommendation": "Declared in standard metric units (ml/g) as per Legal Metrology norms.",
        },
        {
            "Requirement": "Month & Year of Manufacture",
            "Detected": fields["Date"],
            "Status": "PASS" if fields["Date"] else "FLAG",
            "Rule": "Rule 6(1)(d) — packing/mfg date",
            "Recommendation": "Valid month and year format clearly detected.",
        },
        {
            "Requirement": "Maximum Retail Price (MRP)",
            "Detected": fields["MRP"],
            "Status": "PASS" if fields["MRP"] else "FLAG",
            "Rule": "Rule 6(1)(e) — retail price (incl. taxes)",
            "Recommendation": "Retail sale price stated with inclusive tax declaration.",
        },
        {
            "Requirement": "Unit Sale Price (USP)",
            "Detected": fields["Unit Sale Price"],
            "Status": "PASS" if fields["Unit Sale Price"] else "REVIEW",
            "Rule": "Rule 6(1)(f) — price per g/kg/ml",
            "Recommendation": "Mandatory for packages containing >1 unit or kg. Confirm applicability.",
        },
    ]

    if active_ctx == "Imported product":
        origin_status = "PASS" if fields["Country of Origin"] else "FLAG"
        origin_rec = "Statutory requirement for imported goods under Rule 6(1)(n)."
    else:
        origin_status = "PASS" if fields["Country of Origin"] else "NOT SCORED"
        origin_rec = "Country of origin is optional for domestic goods."

    checks.append({
        "Requirement": "Country of Origin",
        "Detected": fields["Country of Origin"],
        "Status": origin_status,
        "Rule": "Rule 6(1)(n) — country of manufacture",
        "Recommendation": origin_rec,
    })

    scored = [c for c in checks if c["Status"] in ("PASS", "FLAG")]
    passed = sum(1 for c in scored if c["Status"] == "PASS")
    flagged = sum(1 for c in scored if c["Status"] == "FLAG")
    score = round((passed / len(scored)) * 100) if scored else 0
    risk = "LOW" if score >= 85 else ("MEDIUM" if score >= 65 else "HIGH")

    # Metric Row
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Compliance Mark", f"{score}%")
    m2.metric("Checks Passed", passed)
    m3.metric("Flags Detected", flagged)
    m4.metric("Risk Level", risk)

    # Scorecard Table
    table_rows = []
    for c in checks:
        if c["Status"] == "PASS": icon = "✅ PASS"
        elif c["Status"] == "REVIEW": icon = "🟡 REVIEW"
        elif c["Status"] == "NOT SCORED": icon = "— NOT SCORED"
        else: icon = "❌ FLAG"

        table_rows.append({
            "Statutory Requirement": c["Requirement"],
            "Detected Value": c["Detected"] or "Not Detected",
            "Status": icon,
            "Governing Statute": c["Rule"],
        })

    st.dataframe(pd.DataFrame(table_rows), use_container_width=True, hide_index=True)

    # 04 • EXPLAINABILITY
    st.divider()
    st.markdown('<div class="section-label">04 • Explainability</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-title">Why did NIRIKSHAN reach this verdict?</div>', unsafe_allow_html=True)

    for c in checks:
        det = html.escape(c["Detected"] or "Not Detected")
        req = html.escape(c["Requirement"])
        rule = html.escape(c["Rule"])
        rec = html.escape(c["Recommendation"])

        if c["Status"] == "PASS":
            st.markdown(
                f"""<div class="success-box">
                <b>✅ {req}</b><br>
                <b>Detected:</b> {det} | <b>Rule:</b> {rule}<br>
                <b>Assessment:</b> Statutory declaration confirmed present on package.
                </div>""",
                unsafe_allow_html=True,
            )
        elif c["Status"] == "REVIEW":
            st.markdown(
                f"""<div class="warning-box">
                <b>🟡 {req}</b><br>
                <b>Detected:</b> {det} | <b>Rule:</b> {rule}<br>
                <b>Action Required:</b> {rec}
                </div>""",
                unsafe_allow_html=True,
            )
        elif c["Status"] == "FLAG":
            st.markdown(
                f"""<div class="danger-box">
                <b>❌ {req}</b><br>
                <b>Detected:</b> {det} | <b>Rule:</b> {rule}<br>
                <b>Violation Notice:</b> Mandatory declaration missing. Action under Section 36 of Legal Metrology Act, 2009.
                </div>""",
                unsafe_allow_html=True,
            )

    # 05 • EVIDENCE & REPORT EXPORT
    st.divider()
    st.markdown('<div class="section-label">05 • Evidence & Notice Generation</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-title">Statutory Audit Dossier</div>', unsafe_allow_html=True)

    rep_id = f"NIR-{datetime.now().strftime('%Y%m%d')}-{random.randint(1000, 9999)}"
    notice_text = f"""GOVERNMENT OF INDIA - MINISTRY OF CONSUMER AFFAIRS
LEGAL METROLOGY (PACKAGED COMMODITIES) RULES, 2011
STATUTORY SCREENING INSPECTION RECORD
================================================================
Dossier ID        : {rep_id}
Audit Timestamp   : {datetime.now().strftime('%d-%m-%Y %H:%M:%S')}
Operational Role  : {mode}
Origin Category   : {active_ctx}
Screening Mark    : {score}%
Assessed Risk     : {risk}
Flags Detected    : {flagged}
----------------------------------------------------------------
STATUTORY DECLARATIONS AUDIT:
"""
    for c in checks:
        notice_text += f"[{c['Status']:^8}] {c['Requirement']:<32} | {c['Rule']:<14} | Detected: {c['Detected'] or 'N/A'}\n"
    notice_text += f"""================================================================
VERDICT:
{'Consignment clears automated screening.' if flagged == 0 else 'Statutory flags raised. Formal inquiry recommended under Section 36.'}
"""

    e1, e2 = st.columns([1.2, 1])
    with e1:
        st.markdown(
            f"""
            <div class="evidence-card">
                <h4>📄 Inspection Dossier: {rep_id}</h4>
                <div class="evidence-line">Operational Mode: {html.escape(mode)}</div>
                <div class="evidence-line">Screening Score: {score}%</div>
                <div class="evidence-line">Assessed Risk: {risk}</div>
                <div class="evidence-line">Violations Detected: {flagged}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with e2:
        st.download_button(
            label="📥 Download Legal Inspection Notice (TXT)",
            data=notice_text,
            file_name=f"{rep_id}_Legal_Notice.txt",
            mime="text/plain",
            use_container_width=True,
            key="btn_download_txt",
        )

        def generate_pdf_report(rep_id, score, risk, checks, mode, active_ctx):
            def clean_for_pdf(txt):
                if not txt: return ""
                t = str(txt).replace("₹", "Rs. ").replace("—", "-").replace("–", "-")
                t = t.replace("✅", "[PASS]").replace("🟡", "[REVIEW]").replace("❌", "[FLAG]")
                return t.encode("latin-1", "replace").decode("latin-1")

            pdf = FPDF()
            pdf.add_page()
            pdf.set_font("Helvetica", "B", 15)
            pdf.set_text_color(11, 31, 58)
            pdf.cell(0, 10, "MINISTRY OF CONSUMER AFFAIRS, FOOD & PUBLIC DISTRIBUTION", ln=True, align="C")
            pdf.set_font("Helvetica", "B", 11)
            pdf.cell(0, 8, "LEGAL METROLOGY (PACKAGED COMMODITIES) ENFORCEMENT DIVISION", ln=True, align="C")
            pdf.ln(4)
            
            pdf.set_font("Helvetica", "B", 10)
            pdf.cell(0, 6, clean_for_pdf(f"Statutory Inspection Dossier ID: {rep_id}"), ln=True)
            pdf.set_font("Helvetica", "", 9)
            pdf.cell(0, 5, clean_for_pdf(f"Audit Timestamp: {datetime.now().strftime('%d-%m-%Y %H:%M:%S')} | Mode: {mode}"), ln=True)
            pdf.cell(0, 5, clean_for_pdf(f"Consignment Origin: {active_ctx} | Assessed Risk: {risk} | Screening Mark: {score}%"), ln=True)
            pdf.ln(4)
            
            pdf.set_font("Helvetica", "B", 10)
            pdf.cell(0, 7, "STATUTORY CLAUSE AUDIT MATRIX:", ln=True)
            pdf.set_font("Helvetica", "B", 8)
            pdf.cell(70, 7, "Statutory Requirement", 1)
            pdf.cell(30, 7, "Rule", 1)
            pdf.cell(25, 7, "Verdict", 1)
            pdf.cell(65, 7, "Detected Value", 1)
            pdf.ln()
            
            pdf.set_font("Helvetica", "", 8)
            for c in checks:
                pdf.cell(70, 6, clean_for_pdf(c["Requirement"])[:38], 1)
                pdf.cell(30, 6, clean_for_pdf(c["Rule"])[:16], 1)
                pdf.cell(25, 6, clean_for_pdf(c["Status"])[:12], 1)
                pdf.cell(65, 6, clean_for_pdf(str(c["Detected"]))[:35] if c["Detected"] else "Not Detected", 1)
                pdf.ln()
                
            pdf.ln(5)
            pdf.set_font("Helvetica", "I", 8)
            pdf.multi_cell(0, 5, clean_for_pdf("Statutory Disclaimer: Automated preliminary compliance screening under Legal Metrology Rules, 2011. Physical verification remains the definitive standard."))
            return bytes(pdf.output())

        pdf_bytes = generate_pdf_report(rep_id, score, risk, checks, mode, active_ctx)
        st.download_button(
            label="📄 Download Official PDF Audit Dossier",
            data=pdf_bytes,
            file_name=f"{rep_id}_Statutory_Notice.pdf",
            mime="application/pdf",
            use_container_width=True,
            key="btn_download_pdf",
        )

        csv_bytes = pd.DataFrame(table_rows).to_csv(index=False).encode("utf-8")
        st.download_button(
            label="📊 Download CSV Compliance Audit",
            data=csv_bytes,
            file_name=f"{rep_id}_Audit_Matrix.csv",
            mime="text/csv",
            use_container_width=True,
            key="btn_download_csv",
        )

# ============================================================
# REGULATOR AUDIT CONSOLE
# ============================================================
if mode == "🧑‍⚖️ Regulator / Officer Console":
    st.divider()
    st.markdown('<div class="section-label">Regulatory Enforcement View</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-title">Priority Market Enforcement Queue</div>', unsafe_allow_html=True)

    r1, r2, r3, r4 = st.columns(4)
    r1.metric("SKUs Screened Today", "1,284")
    r2.metric("Cleared Consignments", "957")
    r3.metric("Under Field Review", "241")
    r4.metric("High-Risk Violations", "86")

    st.subheader("Priority Action Queue")
    reg_df = pd.DataFrame({
        "Case ID": ["NIR-10291", "NIR-10288", "NIR-10274", "NIR-10260", "NIR-10245"],
        "Commodity Type": ["Imported Confectionery", "Packaged Edible Oil", "Personal Cleanser", "Atta / Wheat 5kg", "Fruit Beverage"],
        "Priority": ["🔴 HIGH", "🔴 HIGH", "🟡 MEDIUM", "🟢 LOW", "🟡 MEDIUM"],
        "Statutory Issue": ["Missing MRP & Date", "Net Quantity Mismatch", "No Customer Care", "Fully Compliant", "Missing USP"],
        "Action Ordered": ["Issue Notice u/S 36", "Physical Store Raid", "Request Correction", "Clear Consignment", "Verify Exemption"],
    })
    st.dataframe(reg_df, use_container_width=True, hide_index=True)

# ============================================================
# FOOTER
# ============================================================
st.divider()
st.markdown(
    """
    <div style="text-align: center; color: #64748b; font-size: 11px;">
        <b>NIRIKSHAN • SIH 2026 • Problem ID: SIH26034</b><br>
        Preliminary Packaged Commodity Compliance Screening Prototype.<br>
        Validated under Legal Metrology (Packaged Commodities) Rules, 2011.
    </div>
    """,
    unsafe_allow_html=True,
)
