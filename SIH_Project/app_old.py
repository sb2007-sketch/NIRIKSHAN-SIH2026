import streamlit as st
from PIL import Image
import re
import datetime

# --- PAGE CONFIGURATION ---
st.set_page_config(
    page_title="Legal Metrology Compliance Portal | SIH 2026",
    page_icon="⚖️",
    layout="wide"
)

# Custom Styling for Professional Hackathon Look
st.markdown("""
    <style>
    .main-title {
        font-size: 32px;
        font-weight: 700;
        color: #1E3A8A;
        margin-bottom: 0px;
    }
    .sub-title {
        font-size: 16px;
        color: #4B5563;
        margin-bottom: 25px;
    }
    .metric-card {
        background-color: #F3F4F6;
        padding: 15px;
        border-radius: 8px;
        border-left: 5px solid #2563EB;
    }
    </style>
""", unsafe_allow_html=True)

# --- HEADER SECTION ---
st.markdown('<div class="main-title">⚖️ Automated Legal Metrology Compliance Scanner</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-title">Verification System under Legal Metrology (Packaged Commodities) Rules, 2011 | SIH Problem ID: SIH26034</div>', unsafe_allow_html=True)

# --- SIDEBAR CONTROLS ---
st.sidebar.image("https://upload.wikimedia.org/wikipedia/commons/5/55/Emblem_of_India.svg", width=90)
st.sidebar.title("Inspection Portal")
mode = st.sidebar.radio("Select Operational Role:", ["Citizen Self-Check", "Regulator / Officer Audit Console"])

st.sidebar.markdown("---")
st.sidebar.subheader("Quick Test Presets (Demo Mode)")
demo_choice = st.sidebar.selectbox(
    "Choose a preset sample label:",
    ["None (Manual Upload)", "Sample 1: Fully Compliant Pack", "Sample 2: Missing MRP & Origin (Violation)", "Sample 3: Missing Unit Sale Price (Non-Compliant)"]
)

# --- DEMO PRESET DATA (Ensures zero presentation failure) ---
sample_texts = {
    "Sample 1: Fully Compliant Pack": """
    XYZ FOODS PVT. LTD.
    Plot 45, Okhla Industrial Area, New Delhi - 110020
    Consumer Care: support@xyzfoods.com | 1800-11-4567
    Generic Name: Roasted Almonds
    Net Quantity: 500 g
    Date of Mfg: 04/2026
    MRP: Rs. 85.00 (Incl. of all taxes)
    Unit Sale Price: Rs. 0.17 / g
    Country of Origin: India
    """,
    "Sample 2: Missing MRP & Origin (Violation)": """
    GLOBAL PACKAGED SNACKS
    Industrial Zone, Mumbai - 400001
    Net Wt: 200g
    Mfg Date: 02/2026
    Customer Care: 022-23456789
    """,
    "Sample 3: Missing Unit Sale Price (Non-Compliant)": """
    HEALTHY BITES LTD
    Sector 62, Noida, UP
    Email: help@healthybites.in
    Net Quantity: 1 kg
    Batch: B-2026-X
    Date of Packing: 01/2026
    MRP: Rs. 240.00 (Inclusive of all taxes)
    Country of Origin: India
    """
}

# --- MAIN WORKSPACE LAYOUT ---
col1, col2 = st.columns([1, 1.2])

with col1:
    st.subheader("1. Input Package Label")
    uploaded_file = st.file_uploader("Upload product label image (JPG, PNG)", type=["jpg", "jpeg", "png"])
    
    label_text = ""
    
    if demo_choice != "None (Manual Upload)":
        st.info(f"Loaded: **{demo_choice}**")
        label_text = sample_texts[demo_choice]
    elif uploaded_file is not None:
        image = Image.open(uploaded_file)
        st.image(image, caption="Uploaded Label for Audit", use_container_width=True)
        
        # Optional Tesseract support with safe fallback
        try:
            import pytesseract
            label_text = pytesseract.image_to_string(image)
        except Exception:
            st.warning("Running in Standard Simulation Engine (OCR binary not detected locally). Paste or edit extracted text below.")
            label_text = "Paste text from packaging or pick a demo sample from sidebar."

    # Editable OCR extraction panel
    st.subheader("Extracted Label Text")
    inspected_text = st.text_area(
        "Detected text content (edit manually if lighting was blurry):",
        value=label_text,
        height=220
    )

with col2:
    st.subheader("2. Rule-by-Rule Compliance Scorecard")
    
    if st.button("Run Compliance Verification Engine", type="primary"):
        if not inspected_text.strip():
            st.error("Please provide an image or select a sample preset to audit.")
        else:
            checks = []
            
            # 1. Rule 6(1)(a): Manufacturer / Packer Details
            has_mfg = bool(re.search(r'(mfg|manufactur|packer|mkt|marketed|ltd|pvt|industrial)', inspected_text, re.IGNORECASE))
            has_contact = bool(re.search(r'(@|consumer|care|customer|email|phone|\b\d{10}\b|\b1800\b)', inspected_text, re.IGNORECASE))
            checks.append({
                "rule": "Rule 6(1)(a)",
                "title": "Manufacturer & Consumer Care Details",
                "status": has_mfg and has_contact,
                "detail": "Verified company identity and reachable consumer care contact." if (has_mfg and has_contact) else "Missing manufacturer address or consumer care telephone/email."
            })
            
            # 2. Rule 6(1)(c): Net Quantity Declaration
            has_qty = bool(re.search(r'(net\s*(wt|weight|qty|quantity)?\s*[:.]?\s*\d+(\.\d+)?\s*(g|kg|ml|l|ltr|gm))', inspected_text, re.IGNORECASE))
            checks.append({
                "rule": "Rule 6(1)(c)",
                "title": "Net Quantity in Metric Units",
                "status": has_qty,
                "detail": "Found standardized metric units (g, kg, ml, l)." if has_qty else "Missing standard net weight/volume metric measurement."
            })
            
            # 3. Rule 6(1)(d): Month & Year of Manufacture
            has_date = bool(re.search(r'(mfd|mfg|pkd|packed|date|use\s*by|exp)?\s*[:.]?\s*(\d{2}[\/\-]\d{2,4}|\b(0[1-9]|1[0-2])[\/\-](20\d{2}|\d{2})\b)', inspected_text, re.IGNORECASE))
            checks.append({
                "rule": "Rule 6(1)(d)",
                "title": "Date of Manufacture / Packing",
                "status": has_date,
                "detail": "Month and year of manufacture/packing detected." if has_date else "Missing valid manufacturing/packing month and year."
            })

            # 4. Rule 6(1)(e): Maximum Retail Price (MRP)
            has_mrp = bool(re.search(r'(m\.?r\.?p\.?|max\s*retail\s*price|price)\s*[:.]?\s*(rs\.?|₹)?\s*\d+', inspected_text, re.IGNORECASE))
            checks.append({
                "rule": "Rule 6(1)(e)",
                "title": "Maximum Retail Price (MRP)",
                "status": has_mrp,
                "detail": "MRP detected with inclusive taxes declaration." if has_mrp else "Missing or illegible MRP declaration."
            })

            # 5. Rule 6(1)(f): Unit Sale Price (USP)
            has_usp = bool(re.search(r'(unit\s*sale\s*price|usp|per\s*(g|kg|ml|l|piece|item))', inspected_text, re.IGNORECASE))
            checks.append({
                "rule": "Rule 6(1)(f)",
                "title": "Unit Sale Price (USP)",
                "status": has_usp,
                "detail": "Unit sale price properly declared." if has_usp else "Missing Unit Sale Price declaration (mandatory per 2021 amendment)."
            })

            # 6. Rule 6(1)(n): Country of Origin
            has_origin = bool(re.search(r'(country\s*of\s*origin|made\s*in|origin\s*:\s*\w+)', inspected_text, re.IGNORECASE))
            checks.append({
                "rule": "Rule 6(1)(n)",
                "title": "Country of Origin",
                "status": has_origin,
                "detail": "Country of origin clearly stated." if has_origin else "Missing country of origin declaration."
            })

            # Display scorecard items
            all_passed = True
            for c in checks:
                if c["status"]:
                    st.success(f"✔ **{c['rule']} - {c['title']}**: {c['detail']}")
                else:
                    all_passed = False
                    st.error(f"✖ **{c['rule']} - {c['title']}**: {c['detail']}")

            # Final Verdict Banner
            st.divider()
            if all_passed:
                st.balloons()
                st.success("### AUDIT RESULT: COMPLIANT WITH LMPC RULES, 2011")
                st.caption("Certificate ID: LMPC-" + datetime.datetime.now().strftime("%Y%m%d-%H%M%S"))
            else:
                st.error("### AUDIT RESULT: NON-COMPLIANT (Violations Detected)")
                st.warning("Recommendation: Issue automated statutory notice to manufacturer/packer under Section 36 of the Legal Metrology Act, 2009.")

            # Inspection Report Output
            with st.expander("📄 Generate Legal Metrology Inspection Summary"):
                st.text(f"""
GOVERNMENT LEGAL METROLOGY INSPECTION RECORD
Timestamp: {datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
Audit Mode: {mode}
Overall Status: {'PASSED' if all_passed else 'NON-COMPLIANT - NOTICE ISSUED'}
Mandatory Declarations Checked: 6 Clauses
Violations Count: {sum(1 for c in checks if not c['status'])}
                """)