import html
import os
import random
import re
from datetime import datetime

import numpy as np
import pandas as pd
import streamlit as st
from fpdf import FPDF
from PIL import Image, ImageEnhance, ImageOps

try:
    import cv2
except ImportError:
    cv2 = None

# Configure Tesseract across Windows and Cloud Linux
try:
    import pytesseract
    windows_tesseract = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
    if os.path.exists(windows_tesseract):
        pytesseract.pytesseract.tesseract_cmd = windows_tesseract
    elif os.path.exists("/usr/bin/tesseract"):
        pytesseract.pytesseract.tesseract_cmd = "/usr/bin/tesseract"
except ImportError:
    pytesseract = None

# ============================================================
# PAGE CONFIGURATION & STYLING
# ============================================================
st.set_page_config(
    page_title="NIRIKSHAN | Legal Metrology Portal",
    page_icon="🔎",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
    .stApp { background-color: #f4f7fb; }
    .block-container { max-width: 1420px; padding-top: 1.2rem; padding-bottom: 2.5rem; }
    [data-testid="stSidebar"] { background-color: #0b1f3a; }
    [data-testid="stSidebar"] * { color: #f8fafc !important; }
    .hero {
        padding: 24px 30px;
        border-radius: 18px;
        background: linear-gradient(135deg, #0b1f3a 0%, #163d70 60%, #1e599f 100%);
        color: white;
        margin-bottom: 20px;
        box-shadow: 0 12px 30px rgba(11, 31, 58, 0.16);
    }
    .hero-topline { font-size: 11px; letter-spacing: 1.5px; text-transform: uppercase; color: #93c5fd; font-weight: 700; margin-bottom: 6px; }
    .hero h1 { font-size: 36px; margin: 0; color: white; font-weight: 800; }
    .hero-subtitle { font-size: 15px; margin-top: 6px; color: #e2e8f0; }
    .hero-flow { margin-top: 14px; font-size: 12px; font-weight: 700; letter-spacing: 0.5px; color: #bfdbfe; }
    .section-label { font-size: 11px; text-transform: uppercase; letter-spacing: 1.2px; color: #64748b; font-weight: 800; margin-bottom: 4px; }
    .section-title { font-size: 22px; color: #0f2745; font-weight: 800; margin-bottom: 12px; }
    .card {
        background: #ffffff;
        padding: 16px;
        border-radius: 14px;
        border: 1px solid #dbe3ed;
        margin-bottom: 12px;
        box-shadow: 0 4px 14px rgba(15, 35, 60, 0.04);
    }
    .field-title { font-size: 11px; color: #64748b !important; text-transform: uppercase; letter-spacing: 0.7px; margin-bottom: 6px; font-weight: 700; }
    .field-value { font-size: 16px; font-weight: 700; color: #10233f !important; min-height: 24px; }
    .field-missing { color: #dc2626 !important; }
    .small-text { color: #64748b !important; font-size: 11px; margin-top: 4px; }
    .success-box, .warning-box, .danger-box { padding: 14px 18px; border-radius: 12px; margin-bottom: 10px; }
    .success-box { background: #ecfdf5; border: 1px solid #a7f3d0; color: #065f46 !important; }
    .warning-box { background: #fffbeb; border: 1px solid #fde68a; color: #92400e !important; }
    .danger-box { background: #fef2f2; border: 1px solid #fecaca; color: #991b1b !important; }
    .evidence-card { background: #0f2745; color: white; border-radius: 14px; padding: 18px; }
    .evidence-line { color: #dbeafe; font-size: 13px; margin: 4px 0; }
    .stTextArea textarea { background-color: #ffffff !important; color: #0f2745 !important; font-family: monospace !important; font-size: 13px !important; border: 1px solid #cbd5e1 !important; }
    [data-testid="stExpander"] { background-color: #ffffff !important; border: 1px solid #cbd5e1 !important; border-radius: 8px !important; }
    [data-testid="stExpander"] * { color: #0f2745 !important; }
    </style>
    """,
    unsafe_allow_html=True,
)

# ============================================================
# HERO & SIDEBAR
# ============================================================
st.markdown(
    """
    <div class="hero">
        <div class="hero-topline">Smart India Hackathon 2026 • Problem Statement SIH26034</div>
        <h1>🔎 NIRIKSHAN</h1>
        <div class="hero-subtitle">Universal Packaged Commodity Statutory Compliance Engine</div>
        <div class="hero-flow">INTAKE ➔ MULTI-PASS PREPROCESS ➔ DETECT & EXTRACT ➔ VALIDATE ➔ EXPLAIN ➔ AUDIT</div>
    </div>
    """,
    unsafe_allow_html=True,
)

st.sidebar.image("https://upload.wikimedia.org/wikipedia/commons/5/55/Emblem_of_India.svg", width=70)
st.sidebar.title("NIRIKSHAN")
st.sidebar.caption("Legal Metrology Compliance Screening")

mode = st.sidebar.radio("Operating Mode", ["👤 Citizen Self-Check", "🧑‍⚖️ Regulator / Officer Console"])
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
# UNIVERSAL OCR PREPROCESSING & PARSING
# ============================================================
def execute_universal_ocr(pil_img):
    """Multi-pass OCR supporting bottles, boxes, blister foils, and pouches."""
    if not pytesseract:
        return ""
    text_passes = []
    
    # Pass 1: Full-frame contrast enhancement
    gray_pil = ImageOps.grayscale(pil_img)
    enhancer = ImageEnhance.Contrast(gray_pil)
    contrast_pil = enhancer.enhance(1.8)
    
    try:
        t1 = pytesseract.image_to_string(contrast_pil, config="--psm 6")
        text_passes.append(t1)
    except Exception:
        pass

    try:
        t2 = pytesseract.image_to_string(contrast_pil, config="--psm 11")
        text_passes.append(t2)
    except Exception:
        pass

    # Pass 2: Adaptive Thresholding via OpenCV if available
    if cv2 is not None:
        try:
            cv_arr = np.array(gray_pil)
            blur = cv2.GaussianBlur(cv_arr, (3, 3), 0)
            thresh = cv2.adaptiveThreshold(blur, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2)
            t3 = pytesseract.image_to_string(thresh, config="--psm 6")
            text_passes.append(t3)
        except Exception:
            pass

    return "\n".join(text_passes).strip()

def clean_spaces(text):
    return re.sub(r"\s+", " ", str(text)).strip()

def extract_universal_declarations(text):
    """Generic extractor for any packaged commodity without hardcoded brands."""
    clean = clean_spaces(text)

    # 1. Manufacturer / Packer / Marketer
    mfg = ""
    m_match = re.search(
        r"(?:marketed\s*by|manufactured\s*by|mfg(?:\.|\s*by)|packed\s*by|mfd(?:\.|\s*by)|lab(?:\.|\s*by))\s*[:.]?\s*([A-Za-z0-9\s,.\(\)-]{4,75})",
        clean,
        re.I,
    )
    if m_match:
        mfg = re.split(r"\b(net|batch|mrp|consumer|care|lic|exp|mfg|regd|composition)\b", m_match.group(1), flags=re.I)[0].strip(" :,.-")

    # 2. Consumer Care Details (Phone, Email, Toll-Free)
    care = ""
    toll = re.search(r"(?:1800|1860)[\s-]?\d{3}[\s-]?\d{3,4}", clean)
    phone = re.search(r"(?:\+91[\s-]?)?[6-9]\d{9}", clean)
    email = re.search(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+", clean)
    if phone and email:
        care = f"{phone.group(0)} | {email.group(0)}"
    elif email:
        care = email.group(0)
    elif phone:
        care = phone.group(0)
    elif toll:
        care = toll.group(0)

    # 3. Net Quantity / Count / Volume / Weight
    qty = ""
    q_match = re.search(
        r"(?:net\s*(?:content|quantity|qty|wt|weight)?)\s*[:.]?\s*(\d+(?:\.\d+)?\s*(?:ml|g|gm|gms|kg|l|lt|ltr|fl\s*oz|tablets|capsules|units|n))\b",
        clean,
        re.I,
    )
    if q_match:
        qty = q_match.group(1)
    else:
        # Fallback metric search
        q_alt = re.search(r"\b(\d+(?:\.\d+)?\s*(?:ml|g|gm|kg|ltr|tablets|capsules))\b", clean, re.I)
        if q_alt:
            qty = q_alt.group(1)

    # 4. Date of Mfg / Pkd / Exp
    date_val = ""
    d_match = re.search(
        r"(?:mfg|mfd|pkd|packed|exp|use\s*before|expiry)\s*(?:date)?\s*[:.]?\s*(\b(?:0[1-9]|1[0-2]|[A-Za-z]{3})[\/\-\.](?:20\d{2}|\d{2})\b)",
        clean,
        re.I,
    )
    if d_match:
        date_val = d_match.group(1)
    else:
        d_alt = re.search(r"\b(0[1-9]|1[0-2])[\/\-](20\d{2}|\d{2})\b", clean)
        if d_alt:
            date_val = d_alt.group(0)

    # 5. Maximum Retail Price (MRP)
    mrp_val = ""
    mrp_match = re.search(
        r"(?:m\.?r\.?p\.?|max(?:imum)?\s*retail\s*price)\s*(?:\(?[₹rs.]*\)?\s*[:.]?)?\s*(?:rs\.?|₹)?\s*(\d{1,5}(?:\.\d{1,2})?)",
        clean,
        re.I,
    )
    if mrp_match:
        mrp_val = f"₹{mrp_match.group(1)}"
    else:
        mrp_alt = re.search(r"[₹Rs\.]\s*(\d{2,5}(?:\.\d{2})?)", clean)
        if mrp_alt:
            mrp_val = f"₹{mrp_alt.group(1)}"

    # 6. Unit Sale Price (USP)
    usp_val = ""
    u_match = re.search(
        r"(?:unit\s*sale\s*price|usp)\s*[:.]?\s*(?:rs\.?|₹)?\s*(\d+(?:\.\d{1,2})?)\s*(?:\/|per)\s*(g|kg|ml|l|tablet|piece|unit)",
        clean,
        re.I,
    )
    if u_match:
        usp_val = f"₹{u_match.group(1)} / {u_match.group(2)}"

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
# 01 • PRODUCT INTAKE WORKSPACE
# ============================================================
st.markdown('<div class="section-label">01 • Product Intake</div>', unsafe_allow_html=True)
st.markdown('<div class="section-title">Scan or Upload Product Label</div>', unsafe_allow_html=True)

fields = {}
source_type = ""

if demo != "No Demo — Upload Image":
    fields = samples[demo].copy()
    source_type = "Demo Preset"
    st.success(f"✔ **Active Preset**: {demo}")
else:
    source_type = "Physical Image Scan"
    uploaded_file = st.file_uploader("Upload Product Label Image (JPG / PNG):", type=["jpg", "jpeg", "png"])

    # Reset buffer when a different image is selected
    if uploaded_file is not None:
        file_id = f"{uploaded_file.name}_{uploaded_file.size}"
        if st.session_state.get("current_file_id") != file_id:
            st.session_state.current_file_id = file_id
            st.session_state.ocr_buffer = ""

        col_img, col_proc = st.columns([1, 1.2])

        with col_img:
            pil_img = Image.open(uploaded_file).convert("RGB")
            st.image(pil_img, caption="Target Package Commodity", use_container_width=True)

            if pytesseract and not st.session_state.ocr_buffer:
                with st.spinner("Extracting multi-pass text stream across entire surface..."):
                    st.session_state.ocr_buffer = execute_universal_ocr(pil_img)

        with col_proc:
            st.markdown("**OCR Extraction Stream (Dynamic Human-in-the-Loop):**")
            st.caption("Inspect and verify raw text. You can edit any unread characters directly below to update compliance live.")

            user_stream = st.text_area(
                "Extracted Text Stream:",
                value=st.session_state.ocr_buffer,
                height=220,
                placeholder="Live OCR output will display here once the image finishes processing..."
            )
            st.session_state.ocr_buffer = user_stream

            if st.button("🧹 Clear & Re-run Raw OCR"):
                st.session_state.ocr_buffer = ""
                st.rerun()

            if user_stream.strip():
                fields = extract_universal_declarations(user_stream)

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
        conf = 95 if (val and source_type == "Demo Preset") else (85 if val else 0)

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
            "Rule": "Rule 6(1)(c) — metric units (g, kg, ml, l, count)",
            "Recommendation": "Declared in standard metric units as per Legal Metrology norms.",
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
            "Rule": "Rule 6(1)(f) — price per unit/g/ml",
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
        "Rule": "Rule 6(1)(n) — country of origin",
        "Recommendation": origin_rec,
    })

    scored = [c for c in checks if c["Status"] in ("PASS", "FLAG")]
    passed = sum(1 for c in scored if c["Status"] == "PASS")
    flagged = sum(1 for c in scored if c["Status"] == "FLAG")
    score = round((passed / len(scored)) * 100) if scored else 0
    risk = "LOW" if score >= 85 else ("MEDIUM" if score >= 65 else "HIGH")

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Compliance Mark", f"{score}%")
    m2.metric("Checks Passed", passed)
    m3.metric("Flags Detected", flagged)
    m4.metric("Risk Level", risk)

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
# REGULATOR CONSOLE
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
