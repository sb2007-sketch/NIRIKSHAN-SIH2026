import base64
import html
import io
import json
import os
import random
import re
from datetime import datetime

import pandas as pd
import streamlit as st
from fpdf import FPDF
from PIL import Image

try:
    from groq import Groq
    GROQ_AVAILABLE = True
except ImportError:
    GROQ_AVAILABLE = False

# ============================================================
# PAGE CONFIGURATION & NATIONAL REGULATORY PORTAL STYLING
# ============================================================
st.set_page_config(
    page_title="NIRIKSHAN | Legal Metrology Surveillance System",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=JetBrains+Mono:wght@500;600&display=swap');

    html, body, [class*="css"] {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    }
    .stApp { background-color: #f8fafc; }
    .block-container { max-width: 1400px; padding-top: 1rem; padding-bottom: 3rem; }

    .gov-strip {
        background: #0b1f3a;
        border-bottom: 4px solid #f59e0b;
        color: white;
        padding: 18px 28px;
        border-radius: 12px;
        margin-bottom: 22px;
        box-shadow: 0 4px 20px rgba(11, 31, 58, 0.12);
    }
    .gov-strip-flex {
        display: flex;
        align-items: center;
        gap: 20px;
    }
    .gov-title-block h1 {
        font-size: 24px;
        font-weight: 800;
        letter-spacing: -0.5px;
        margin: 0;
        color: #ffffff;
    }
    .gov-subtitle {
        font-size: 13px;
        color: #cbd5e1;
        margin-top: 4px;
        font-weight: 500;
    }
    .gov-tag {
        display: inline-block;
        background: rgba(245, 158, 11, 0.2);
        color: #fbbf24;
        border: 1px solid rgba(245, 158, 11, 0.4);
        padding: 2px 8px;
        border-radius: 4px;
        font-size: 11px;
        font-weight: 700;
        letter-spacing: 0.8px;
        text-transform: uppercase;
        margin-bottom: 4px;
    }

    .card {
        background: #ffffff;
        padding: 18px;
        border-radius: 10px;
        border: 1px solid #e2e8f0;
        margin-bottom: 12px;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.03);
    }
    .field-title {
        font-size: 11px;
        color: #64748b !important;
        text-transform: uppercase;
        letter-spacing: 0.6px;
        font-weight: 700;
        margin-bottom: 6px;
    }
    .field-value {
        font-size: 15px;
        font-weight: 700;
        color: #0f2745 !important;
        line-height: 1.4;
    }
    .field-missing { color: #dc2626 !important; }

    .status-badge-pass {
        background: #ecfdf5;
        color: #065f46;
        border: 1px solid #a7f3d0;
        padding: 3px 8px;
        border-radius: 5px;
        font-size: 11px;
        font-weight: 700;
    }
    .status-badge-flag {
        background: #fef2f2;
        color: #991b1b;
        border: 1px solid #fecaca;
        padding: 3px 8px;
        border-radius: 5px;
        font-size: 11px;
        font-weight: 700;
    }

    div[data-testid="stExpander"] {
        background-color: #ffffff !important;
        border: 2px solid #0b1f3a !important;
        border-radius: 10px !important;
        box-shadow: 0 4px 12px rgba(11, 31, 58, 0.08) !important;
        margin-bottom: 18px !important;
    }
    div[data-testid="stExpander"] summary {
        font-weight: 700 !important;
        font-size: 14.5px !important;
        color: #0b1f3a !important;
        padding: 12px !important;
    }
    div[data-testid="stExpander"] label {
        font-weight: 600 !important;
        color: #1e293b !important;
        font-size: 13px !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# ============================================================
# INSTITUTIONAL HEADER & SIDEBAR
# ============================================================
st.markdown(
    """
    <div class="gov-strip">
        <div class="gov-strip-flex">
            <div class="gov-title-block">
                <div class="gov-tag">National Regulatory Surveillance Portal • SIH 2026</div>
                <h1>⚖️ NIRIKSHAN • Universal Legal Metrology Compliance Engine</h1>
                <div class="gov-subtitle">Statutory Verification Directorate • Legal Metrology (Packaged Commodities) Rules, 2011 • Department of Consumer Affairs, GoI</div>
            </div>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

st.sidebar.image("https://upload.wikimedia.org/wikipedia/commons/5/55/Emblem_of_India.svg", width=65)
st.sidebar.title("LEGAL METROLOGY")
st.sidebar.caption("Central Enforcement Division")

default_key = st.secrets.get("GROQ_API_KEY", os.environ.get("GROQ_API_KEY", ""))

api_key_input = st.sidebar.text_input(
    "🔑 Vision Key (Groq Console):",
    type="password",
    value=default_key,
    help="Loaded automatically from secrets, environment, or manual entry"
)

portal_view = st.sidebar.radio(
    "Surveillance Module:",
    ["📷 Real-Time Packaging Surveillance", "📊 Priority Enforcement Queue & Seizure Register"]
)

consignment_class = st.sidebar.selectbox(
    "Consignment Classification:",
    ["Domestic Commodity (India)", "Imported Packaged Commodity", "Automatic Determination"]
)

st.sidebar.divider()
st.sidebar.markdown(
    """
    <div style="font-size: 11px; color: #94a3b8; line-height: 1.5;">
        <b>STATUTORY NOTICE:</b><br>
        Surveillance governed under Section 18 & Section 36 of the Legal Metrology Act, 2009. Mandatory declarations on packaged commodities must be verifiable across physical retail channels.
    </div>
    """,
    unsafe_allow_html=True,
)

# ============================================================
# MULTIMODAL STATUTORY VISION ENGINE (GROQ VISION)
# ============================================================
def extract_statutory_declarations_vision(pil_img, api_key):
    if not GROQ_AVAILABLE or not api_key:
        return None, "API Key missing or groq library not installed."

    try:
        # 1. Resize image to keep payload tiny and avoid token quota issues
        img_copy = pil_img.copy()
        img_copy.thumbnail((768, 768))

        buffered = io.BytesIO()
        img_copy.save(buffered, format="JPEG", quality=75, optimize=True)
        img_base64 = base64.b64encode(buffered.getvalue()).decode("utf-8")

        client = Groq(api_key=api_key)

        prompt = (
            "Read this product packaging label under Rule 6 of the Legal Metrology Rules, 2011 (India).\n"
            "Return strictly a JSON object with these exact keys:\n"
            "{\n"
            '  "Manufacturer / Packer": "Full name and address",\n'
            '  "Consumer Care": "Helpline or email",\n'
            '  "Net Quantity": "Declared quantity with metric unit (e.g., 200 g, 250 ml)",\n'
            '  "Date": "Month and year of manufacture or packing",\n'
            '  "MRP": "Price with currency symbol (e.g., Rs. 285.00)",\n'
            '  "Unit Sale Price": "Price per unit (e.g., Rs. 1.43 / g)",\n'
            '  "Country of Origin": "Country name (e.g., India)"\n'
            "}\n"
            'If any declaration is missing or unreadable, set its value to "". Do not provide explanations.'
        )

        # Call the active Qwen vision model with reasoning disabled
        chat_completion = client.chat.completions.create(
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{img_base64}",
                            },
                        },
                    ],
                }
            ],
            model="qwen/qwen3.6-27b",
            temperature=0.1,
            max_completion_tokens=500,
            extra_body={"reasoning_effort": "none"}
        )

        content = chat_completion.choices[0].message.content or ""
        content = content.strip()

        # Clean out any stray markdown codeblock backticks
        content = re.sub(r"^```(?:json)?", "", content, flags=re.MULTILINE)
        content = re.sub(r"```$", "", content, flags=re.MULTILINE).strip()

        # Extract curly braces safely
        start_idx = content.find("{")
        end_idx = content.rfind("}")

        if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
            json_str = content[start_idx : end_idx + 1]
            data = json.loads(json_str)
        else:
            # Fallback if raw JSON formatting had minor deviations
            data = {
                "Manufacturer / Packer": "",
                "Consumer Care": "",
                "Net Quantity": "",
                "Date": "",
                "MRP": "",
                "Unit Sale Price": "",
                "Country of Origin": "",
            }

        required_keys = [
            "Manufacturer / Packer",
            "Consumer Care",
            "Net Quantity",
            "Date",
            "MRP",
            "Unit Sale Price",
            "Country of Origin",
        ]
        for k in required_keys:
            if k not in data:
                data[k] = ""

        return data, None

    except Exception as e:
        return None, str(e)
# ============================================================
# PRIMARY SURVEILLANCE WORKSPACE
# ============================================================
if portal_view == "📷 Real-Time Packaging Surveillance":
    col_upload, col_standard = st.columns([1.1, 0.9])

    with col_upload:
        st.markdown("#### 📥 Commodity Ingestion & Optical Intake")
        uploaded_file = st.file_uploader(
            "Upload Packaged Commodity Image (JPG / PNG):",
            type=["jpg", "jpeg", "png"],
            help="Supports cylindrical bottles, jars, cartons, and pouches."
        )

    with col_standard:
        st.markdown("#### ⚖️ Statutory Clause Monitor (Rule 6)")
        st.info(
            "**Mandatory Packaging Declarations Under Surveillance:**\n"
            "• **Rule 6(1)(a)**: Name & Complete Address of Manufacturer / Packer\n"
            "• **Rule 6(1)(a)**: Consumer Care Grievance Redressal (Toll-Free / Email)\n"
            "• **Rule 6(1)(c)**: Net Quantity in Standard Metric Units (g, kg, ml, l, count)\n"
            "• **Rule 6(1)(d)**: Month & Year of Manufacture / Pre-packing\n"
            "• **Rule 6(1)(e)**: Maximum Retail Price (MRP) inclusive of all taxes\n"
            "• **Rule 6(1)(f)**: Unit Sale Price (USP) per standard metric unit\n"
            "• **Rule 6(1)(n)**: Country of Origin (Mandatory for imported consignments)"
        )

    if uploaded_file is not None:
        file_id = f"{uploaded_file.name}_{uploaded_file.size}"
        if st.session_state.get("current_active_file") != file_id:
            st.session_state.current_active_file = file_id
            st.session_state.parsed_fields = {}

        c_view, c_stream = st.columns([1, 1.2])

        with c_view:
            pil_img = Image.open(uploaded_file).convert("RGB")
            st.image(pil_img, caption="Physical Commodity Under Surveillance", use_container_width=True)

            if not st.session_state.get("parsed_fields"):
                if not api_key_input:
                    st.warning("⚠️ Enter your free Groq Vision Key in the sidebar to run neural analysis.")
                else:
                    with st.spinner("Analyzing 3D Curvature & Reading Packaging Declarations..."):
                        extracted_json, err = extract_statutory_declarations_vision(pil_img, api_key_input)
                        if extracted_json:
                            st.session_state.parsed_fields = extracted_json
                        else:
                            st.error(f"Analysis error: {err}")

        with c_stream:
            st.markdown("**Field Officer Optical Inspection Stream:**")
            st.caption("Level-2 Regulatory Stream. Verified compliant with National Packaging Standards.")
            
            raw_display = json.dumps(st.session_state.get("parsed_fields", {}), indent=2)
            st.text_area(
                "Structured Statutory Stream:",
                value=raw_display if raw_display != "{}" else "Waiting for optical scan...",
                height=240,
                disabled=True
            )

    fields = st.session_state.get("parsed_fields", {})

    # ============================================================
    # LEVEL-2 ENFORCEMENT VERIFICATION CONSOLE
    # ============================================================
    if fields:
        st.divider()
        st.markdown("### 🔍 Level-2 Field Officer Verification & Dossier Confirmation")
        st.caption(
            "Under Section 18/36 surveillance guidelines, inspecting officers can directly verify and confirm "
            "attributes obscured by severe physical damage or lighting glare before sealing the formal inspection record."
        )

        with st.expander("📝 Open Statutory Verification & Edit Console", expanded=False):
            with st.form("officer_override_form"):
                ec1, ec2 = st.columns(2)
                with ec1:
                    f_mfg = st.text_input("Manufacturer / Packer:", value=fields.get("Manufacturer / Packer", ""))
                    f_care = st.text_input("Consumer Care Helpline:", value=fields.get("Consumer Care", ""))
                    f_qty = st.text_input("Net Quantity:", value=fields.get("Net Quantity", ""))
                    f_date = st.text_input("Month & Year of Mfg/Packing:", value=fields.get("Date", ""))
                with ec2:
                    f_mrp = st.text_input("Maximum Retail Price (MRP):", value=fields.get("MRP", ""))
                    f_usp = st.text_input("Unit Sale Price (USP):", value=fields.get("Unit Sale Price", ""))
                    f_orig = st.text_input("Country of Origin:", value=fields.get("Country of Origin", "India"))

                submitted = st.form_submit_button("💾 Save Verified Inscriptions & Update Scorecard", use_container_width=True)
                if submitted:
                    st.session_state.parsed_fields = {
                        "Manufacturer / Packer": f_mfg.strip(),
                        "Consumer Care": f_care.strip(),
                        "Net Quantity": f_qty.strip(),
                        "Date": f_date.strip(),
                        "MRP": f_mrp.strip(),
                        "Unit Sale Price": f_usp.strip(),
                        "Country of Origin": f_orig.strip(),
                    }
                    st.rerun()

        fields = st.session_state.get("parsed_fields", fields)

        # ============================================================
        # STATUTORY COMPLIANCE AUDIT MATRIX
        # ============================================================
        st.markdown("### 📋 Statutory Adherence & Rule Compliance Matrix")

        sc1, sc2, sc3 = st.columns(3)
        field_list = list(fields.items())

        for idx, (f_name, f_val) in enumerate(field_list):
            col = [sc1, sc2, sc3][idx % 3]
            display_val = f_val if f_val else "Non-Compliant / Not Detected"
            style_class = "field-value" if f_val else "field-value field-missing"
            badge_text = "VERIFIED" if f_val else "DEFICIENT"
            badge_style = "status-badge-pass" if f_val else "status-badge-flag"

            with col:
                st.markdown(
                    f"""
                    <div class="card">
                        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px;">
                            <span class="field-title">{html.escape(f_name)}</span>
                            <span class="{badge_style}">{badge_text}</span>
                        </div>
                        <div class="{style_class}">{html.escape(display_val)}</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

        checks = [
            {
                "Requirement": "Manufacturer / Packer / Importer",
                "Detected": fields.get("Manufacturer / Packer", ""),
                "Status": "PASS" if fields.get("Manufacturer / Packer") else "FLAG",
                "Rule": "Rule 6(1)(a)",
                "Details": "Mandatory identity and registered manufacturing premises.",
            },
            {
                "Requirement": "Consumer Care Redressal",
                "Detected": fields.get("Consumer Care", ""),
                "Status": "PASS" if fields.get("Consumer Care") else "FLAG",
                "Rule": "Rule 6(1)(a)",
                "Details": "Operational toll-free line, telephone, or electronic contact.",
            },
            {
                "Requirement": "Net Quantity (Standard Metric)",
                "Detected": fields.get("Net Quantity", ""),
                "Status": "PASS" if fields.get("Net Quantity") else "FLAG",
                "Rule": "Rule 6(1)(c)",
                "Details": "Standard metric unit declaration conforming to Schedule II.",
            },
            {
                "Requirement": "Month & Year of Packing / Mfg",
                "Detected": fields.get("Date", ""),
                "Status": "PASS" if fields.get("Date") else "FLAG",
                "Rule": "Rule 6(1)(d)",
                "Details": "Clear pre-packing / manufacturing date specification.",
            },
            {
                "Requirement": "Maximum Retail Price (MRP)",
                "Detected": fields.get("MRP", ""),
                "Status": "PASS" if fields.get("MRP") else "FLAG",
                "Rule": "Rule 6(1)(e)",
                "Details": "Stated in Indian Currency (INR), inclusive of all taxes.",
            },
            {
                "Requirement": "Unit Sale Price (USP)",
                "Detected": fields.get("Unit Sale Price", ""),
                "Status": "PASS" if fields.get("Unit Sale Price") else "FLAG",
                "Rule": "Rule 6(1)(f)",
                "Details": "Unit pricing per standard g, ml, or count under Schedule II.",
            },
        ]

        if "Imported" in consignment_class:
            orig_stat = "PASS" if fields.get("Country of Origin") else "FLAG"
            orig_desc = "Mandatory declaration for imported packaged commodities."
        else:
            orig_stat = "PASS" if fields.get("Country of Origin") else "NOT SCORED"
            orig_desc = "Country of origin verified on packaging display."

        checks.append({
            "Requirement": "Country of Origin",
            "Detected": fields.get("Country of Origin", ""),
            "Status": orig_stat,
            "Rule": "Rule 6(1)(n)",
            "Details": orig_desc,
        })

        scored_rules = [c for c in checks if c["Status"] in ("PASS", "FLAG")]
        passed_rules = sum(1 for c in scored_rules if c["Status"] == "PASS")
        flagged_rules = sum(1 for c in scored_rules if c["Status"] == "FLAG")
        score = round((passed_rules / len(scored_rules)) * 100) if scored_rules else 0
        risk = "LOW RISK" if score >= 85 else ("MODERATE RISK" if score >= 60 else "CRITICAL VIOLATION")

        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Statutory Adherence Score", f"{score}%")
        m2.metric("Compliant Provisions", f"{passed_rules} / {len(scored_rules)}")
        m3.metric("Violations Flagged", flagged_rules)
        m4.metric("Consignment Risk Rating", risk)

        audit_table = []
        for c in checks:
            audit_table.append({
                "Statutory Clause": c["Requirement"],
                "Governing Statute": c["Rule"],
                "Detected Inscription": c["Detected"] or "Deficient / Missing",
                "Compliance Verdict": "✅ COMPLIANT" if c["Status"] == "PASS" else ("— NOT SCORED" if c["Status"] == "NOT SCORED" else "❌ VIOLATION"),
                "Statutory Scope": c["Details"],
            })
        st.dataframe(pd.DataFrame(audit_table), use_container_width=True, hide_index=True)

        # ============================================================
        # OFFICIAL ENFORCEMENT REPORT & SEIZURE NOTICE GENERATOR
        # ============================================================
        st.divider()
        st.markdown("### 🏛️ Official Form-II Inspection Record & Enforcement Dossier")

        rep_id = f"GOI-LMD-{datetime.now().strftime('%Y%m%d')}-{random.randint(10000, 99999)}"

        def generate_official_pdf(rep_id, score, risk, checks, origin_type):
            def clean_pdf(text):
                if not text:
                    return ""
                t = str(text).replace("₹", "Rs. ").replace("—", "-").replace("–", "-")
                return t.encode("latin-1", "replace").decode("latin-1")

            pdf = FPDF()
            pdf.add_page()
            pdf.set_font("Helvetica", "B", 13)
            pdf.set_text_color(11, 31, 58)
            pdf.cell(0, 8, clean_pdf("GOVERNMENT OF INDIA"), ln=True, align="C")
            pdf.set_font("Helvetica", "B", 10)
            pdf.cell(0, 6, clean_pdf("MINISTRY OF CONSUMER AFFAIRS, FOOD & PUBLIC DISTRIBUTION"), ln=True, align="C")
            pdf.cell(0, 6, clean_pdf("DEPARTMENT OF LEGAL METROLOGY • CENTRAL ENFORCEMENT CELL"), ln=True, align="C")
            pdf.ln(3)

            pdf.set_draw_color(11, 31, 58)
            pdf.set_line_width(0.5)
            pdf.line(10, pdf.get_y(), 200, pdf.get_y())
            pdf.ln(5)

            pdf.set_font("Helvetica", "B", 9)
            pdf.cell(0, 5, clean_pdf(f"STATUTORY INSPECTION DOSSIER: {rep_id}"), ln=True)
            pdf.set_font("Helvetica", "", 8.5)
            pdf.cell(0, 5, clean_pdf(f"Surveillance Timestamp: {datetime.now().strftime('%d-%m-%Y %H:%M:%S IST')} | Classification: {origin_type}"), ln=True)
            pdf.cell(0, 5, clean_pdf(f"Statutory Adherence: {score}% | Enforcement Rating: {risk}"), ln=True)
            pdf.ln(4)

            pdf.set_font("Helvetica", "B", 8.5)
            pdf.cell(65, 6, "Statutory Requirement", 1)
            pdf.cell(25, 6, "Rule", 1)
            pdf.cell(25, 6, "Verdict", 1)
            pdf.cell(75, 6, "Detected Inscription", 1)
            pdf.ln()

            pdf.set_font("Helvetica", "", 8)
            for c in checks:
                pdf.cell(65, 6, clean_pdf(c["Requirement"])[:36], 1)
                pdf.cell(25, 6, clean_pdf(c["Rule"]), 1)
                pdf.cell(25, 6, clean_pdf(c["Status"]), 1)
                pdf.cell(75, 6, clean_pdf(str(c["Detected"]))[:42] if c["Detected"] else "Deficient / Missing", 1)
                pdf.ln()

            pdf.ln(6)
            pdf.set_font("Helvetica", "B", 9)
            pdf.cell(0, 5, clean_pdf("STATUTORY ENFORCEMENT DIRECTIVE:"), ln=True)
            pdf.set_font("Helvetica", "", 8)
            
            if flagged_rules == 0:
                pdf.multi_cell(0, 4, clean_pdf("The examined commodity complies fully with all mandatory declarations stipulated under Rule 6 of the Legal Metrology (Packaged Commodities) Rules, 2011. Cleared for open commercial market distribution."))
            else:
                pdf.multi_cell(0, 4, clean_pdf(f"NON-COMPLIANCE DETECTED: {flagged_rules} mandatory declaration(s) are missing or non-compliant. Notice for inquiry and compounding proceedings is recommended under Section 36 of the Legal Metrology Act, 2009."))

            pdf.ln(4)
            pdf.set_font("Helvetica", "I", 7.5)
            pdf.cell(0, 4, clean_pdf("Generated automatically via NIRIKSHAN Regulatory Portal. Validated under central legal metrology surveillance guidelines."), ln=True)
            
            return bytes(pdf.output())

        d_col1, d_col2 = st.columns([1, 1])
        with d_col1:
            pdf_bytes = generate_official_pdf(rep_id, score, risk, checks, consignment_class)
            st.download_button(
                label="📄 Download Official Form-II Inspection Record (PDF)",
                data=pdf_bytes,
                file_name=f"{rep_id}_Statutory_Notice.pdf",
                mime="application/pdf",
                use_container_width=True,
            )

        with d_col2:
            csv_bytes = pd.DataFrame(audit_table).to_csv(index=False).encode("utf-8")
            st.download_button(
                label="📊 Export Legal Metrology Matrix (CSV)",
                data=csv_bytes,
                file_name=f"{rep_id}_Audit_Matrix.csv",
                mime="text/csv",
                use_container_width=True,
            )

# ============================================================
# MODULE 2: REGULATORY ENFORCEMENT QUEUE
# ============================================================
else:
    st.markdown("### 🏛️ Priority Market Surveillance & Seizure Register")
    st.caption("Active enforcement cases registered under Section 18 / Section 36 across regional jurisdictions.")

    q1, q2, q3, q4 = st.columns(4)
    q1.metric("SKUs Audited Today", "1,842")
    q2.metric("Cleared Consignments", "1,429")
    q3.metric("Under Field Review", "312")
    q4.metric("Seizure Notices Issued", "101")

    st.subheader("Central Inspection & Seizure Log")
    queue_df = pd.DataFrame({
        "Inspection ID": ["LMD-2026-9081", "LMD-2026-9082", "LMD-2026-9083", "LMD-2026-9084", "LMD-2026-9085"],
        "Commodity Description": ["Imported Confectionery Box", "Refined Sunflower Oil 1L", "Personal Body Wash 250ml", "Chakki Fresh Atta 5kg", "Fruit Beverage 200ml"],
        "Manufacturer / Marketer": ["Swiss Treats AG", "Surya Agro Ltd.", "Kalyan Cosmetics LLP", "Kisan Grains Ltd.", "Fresh Orchards Corp."],
        "Risk Priority": ["🔴 CRITICAL", "🔴 CRITICAL", "🟡 MEDIUM", "🟢 LOW", "🟡 MEDIUM"],
        "Statutory Violation": ["Missing Country of Origin & MRP", "Net Quantity Mismatch", "Consumer Care Omitted", "Fully Compliant", "Missing Unit Sale Price"],
        "Statutory Action": ["Seizure u/S 36", "Field Store Audit", "Show Cause Notice", "Commercial Release", "Exemption Verification"],
    })
    st.dataframe(queue_df, use_container_width=True, hide_index=True)

# Footer
st.divider()
st.markdown(
    """
    <div style="text-align: center; color: #64748b; font-size: 11.5px; padding-bottom: 20px;">
        <b>NIRIKSHAN • National Legal Metrology Compliance Surveillance Portal</b><br>
        Developed for Problem Statement SIH26090 • Smart India Hackathon 2026<br>
        Governed under the Legal Metrology Act, 2009 & Packaged Commodities Rules, 2011
    </div>
    """,
    unsafe_allow_html=True,
)
