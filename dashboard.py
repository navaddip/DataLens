"""
# Run Instructions:
# 1. Ensure you have streamlit and plotly installed: pip install streamlit plotly pandas
# 2. Run the app: streamlit run dashboard.py
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import ingestion
import dimensions
import scoring
import roles
import io

# Page Configuration
st.set_page_config(
    page_title="GenAI Data Quality Agent",
    page_icon="🛡️",
    layout="wide"
)

# Custom CSS for Professional Look
st.markdown("""
    <style>
    .main {
        background-color: #f9f9f9;
    }
    .metric-card {
        background-color: #ffffff;
        padding: 20px;
        border-radius: 10px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        text-align: center;
    }
    .stHeader {
        background-color: #ffffff;
        padding: 1rem;
        border-bottom: 2px solid #f0f2f6;
    }
    </style>
    """, unsafe_allow_html=True)

# Helper for caching
@st.cache_data
def process_data(file):
    # Rewind file if needed (not needed for UploadedFile but good practice if using streams)
    file.seek(0)
    df = pd.read_csv(file)
    metadata = ingestion.extract_metadata(df)
    dim_scores = dimensions.calculate_all_dimensions(metadata)
    base_dqs = scoring.calculate_base_dqs(dim_scores)
    return metadata, dim_scores, base_dqs

# --- Sidebar ---
st.sidebar.title("🛡️ GenAI DQS Agent")
st.sidebar.markdown("---")

uploaded_file = st.sidebar.file_uploader("Upload Dataset (CSV)", type=['csv'])

# --- Main Content ---
st.title("Universal Data Quality Scoring System")
st.markdown("### Trusted, Explainable, Role-Aware Quality Metrics")

if uploaded_file is not None:
    try:
        # Process Data (Cached)
        metadata, dim_scores, base_dqs = process_data(uploaded_file)

        # --- Dynamic Role Filtering ---
        all_roles = roles.get_all_role_names()
        applicable_roles = []
        hidden_roles_count = 0
        
        for r in all_roles:
            prof = roles.get_role_profile(r)
            if roles.is_role_applicable(prof, metadata.signals):
                applicable_roles.append(r)
            else:
                hidden_roles_count += 1
        
        # Determine Default Index (Executive if present, else 0)
        default_index = 0
        if "Executive / Leadership" in applicable_roles:
            default_index = applicable_roles.index("Executive / Leadership")
            
        # Add Selectbox to Sidebar NOW (after processing)
        st.sidebar.markdown("---")
        selected_role = st.sidebar.selectbox(
            "Select Applicable Stakeholder Role", 
            applicable_roles, 
            index=default_index,
            help="Roles are filtered automatically based on dataset signals."
        )
        
        if hidden_roles_count > 0:
            st.sidebar.info(f"ℹ️ {hidden_roles_count} roles hidden due to incompatible dataset signals (e.g. non-payment data).")

        # --- Top Section: Base DQS (The Source of Truth) ---
        st.markdown("---")
        col1, col2 = st.columns([1, 2])
        
        with col1:
            st.markdown('<div class="metric-card">', unsafe_allow_html=True)
            
            fig_gauge = go.Figure(go.Indicator(
                mode = "gauge+number",
                value = base_dqs,
                title = {'text': "Universal Base DQS"},
                gauge = {
                    'axis': {'range': [0, 100]},
                    'bar': {'color': "darkblue"},
                    'steps': [
                        {'range': [0, 50], 'color': "#ffebee"},
                        {'range': [50, 80], 'color': "#fff3e0"},
                        {'range': [80, 100], 'color': "#e8f5e9"}
                    ],
                    'threshold': {
                        'line': {'color': "red", 'width': 4},
                        'thickness': 0.75,
                        'value': 100
                    }
                }
            ))
            fig_gauge.update_layout(height=300, margin=dict(l=20, r=20, t=50, b=20))
            st.plotly_chart(fig_gauge, use_container_width=True)
            
            st.caption("Immutable, Universal 'Trust Score' for this dataset.")
            st.markdown('</div>', unsafe_allow_html=True)

        with col2:
            st.subheader("Data Quality Dimensions Breakdown")
            
            # Radar Chart
            categories = list(dim_scores.keys())
            values = list(dim_scores.values())
            
            fig_radar = go.Figure()
            fig_radar.add_trace(go.Scatterpolar(
                r=values,
                theta=[c.title() for c in categories],
                fill='toself',
                name='Current Dataset',
                line_color='blue'
            ))
            fig_radar.update_layout(
                polar=dict(
                    radialaxis=dict(
                        visible=True,
                        range=[0, 100]
                    )),
                showlegend=False,
                height=350,
                margin=dict(l=40, r=40, t=20, b=20)
            )
            st.plotly_chart(fig_radar, use_container_width=True)

        # --- Role Aware Section ---
        st.markdown("---")
        st.subheader(f"Role-Aware Interpretation: {selected_role}")
        
        role_profile = roles.get_role_profile(selected_role)
        # UPDATED: Pass metadata for signal check
        role_score, risk_detected = roles.calculate_role_score(base_dqs, dim_scores, role_profile, metadata)
        
        r_col1, r_col2 = st.columns([1, 2])
        
        with r_col1:
            if role_score is not None:
                st.metric(
                    label="Role-Adjusted Utility Score (RUS)", 
                    value=f"{role_score}", 
                    delta=f"{role_score - base_dqs:.2f} vs Base",
                    help="This score interprets the Base DQS based on your role's priorities. It does NOT replace the Base DQS."
                )
                
                if not risk_detected:
                    st.success("✅ No Critical Risks")
                else:
                    st.error(f"⚠️ {role_profile['risk_level']} Risk Detected")
            else:
                st.warning("⚠️ Role Not Applicable")
                st.caption("Dataset lacks required signals.")
            
        with r_col2:
            st.markdown("**Contextual Analysis**")
            # Pass metadata here too
            explanation = roles.explain_role_impact(role_profile, dim_scores, metadata)
            st.markdown(explanation)

        # Explicit Comparison (Governance View)
        with st.expander("Compare Scores (Governance View)", expanded=False):
            role_label = f"Role Score ({selected_role})"
            
            if role_score is not None:
                if risk_detected:
                    role_label += " ⚠️"
                else:
                    role_label += " ✅"
                
                score_val = role_score
                color_val = "teal" if not risk_detected else "orange"
            else:
                role_label += " (N/A)"
                score_val = 0
                color_val = "gray"

            comp_data = {
                "Score Type": ["Universal Base DQS (Immutable)"],
                "Value": [base_dqs]
            }
            
            if role_score is not None:
                comp_data["Score Type"].append(role_label)
                comp_data["Value"].append(score_val)

            color_map = {
                "Universal Base DQS (Immutable)": "darkblue"
            }
            if role_score is not None:
                color_map[role_label] = color_val

            fig_comp = px.bar(
                comp_data, x="Value", y="Score Type", orientation='h',
                text="Value", color="Score Type",
                color_discrete_map=color_map
            )
            fig_comp.update_layout(xaxis_range=[0, 100], height=200)
            st.plotly_chart(fig_comp, use_container_width=True)

        # --- Metadata Summary (Safe View) ---
        st.markdown("---")
        st.subheader("Dataset Metadata (Safe View)")
        
        m_col1, m_col2, m_col3, m_col4 = st.columns(4)
        m_col1.metric("Rows", metadata.row_count)
        m_col2.metric("Columns", len(metadata.column_names))
        m_col3.metric("Completeness Check", f"{dim_scores['completeness']:.1f}%")
        m_col4.metric("Audit Hash", metadata.audit_hash[:8] + "...")

        with st.expander("View Full Metadata Stats"):
            st.json(metadata.__dict__, expanded=False)

    except Exception as e:
        st.error(f"Error processing dataset: {e}")
        st.write("Please ensure your CSV works with the ingestion rules.")

else:
    # Landing Page State
    st.info("👋 Welcome! Please upload a payment dataset (CSV) to begin.")
    
    st.markdown("""
    ### About this System
    This GenAI Agent provides a **Universal, Dimension-Based Data Quality Score**.
    
    **Key Features:**
    - **7 Dimensions of Quality**: Accuracy, Completeness, Consistency, Timeliness, Uniqueness, Validity, Integrity.
    - **Governance First**: No raw data is stored or displayed.
    - **Role-Awareness**: Get insights tailored to Fraud, Compliance, or Engineering without distorting the truth.
    """)
    
    # Show placeholder role selector explaining it's dynamic
    st.sidebar.selectbox("Select Stakeholder Role", ["Upload data first..."], disabled=True)
    st.sidebar.markdown("---")
    st.sidebar.info(
        "**System Status**: Secure Mode\n"
        "Raw data is **never** displayed or stored.\n"
        "Only metadata is processed."
    )
