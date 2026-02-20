import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime

# --- Utility Functions ---
def format_pages(start, end):
    if pd.isna(start) and pd.isna(end): return ""
    elif pd.isna(end): return str(start)
    else: return f"{int(start)}-{int(end)}"

def count_authors(authors_str):
    if pd.isna(authors_str): return 0
    return len(str(authors_str).split(';'))

@st.cache_data
def load_data(uploaded_file):
    df = pd.read_csv(uploaded_file)
    for col in ['Article Title', 'Abstract', 'Author Keywords', 'Authors', 'Index']:
        if col not in df.columns:
            df[col] = ""
    return df

def semantic_search(df, query):
    if not query: return df
    query = str(query).lower().strip()
    mask = (
        df['Article Title'].str.lower().str.contains(query, na=False) |
        df['Abstract'].str.lower().str.contains(query, na=False) |
        df['Author Keywords'].str.lower().str.contains(query, na=False) |
        df['Authors'].str.lower().str.contains(query, na=False)
    )
    return df[mask]

# --- State Management ---
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "role" not in st.session_state:
    st.session_state.role = None
if "username" not in st.session_state:
    st.session_state.username = ""
if "submissions" not in st.session_state:
    st.session_state.submissions = [] 

# --- Login Page ---
def login_page():
    st.title("🔐 Faculty Annual Appraisal Portal")
    st.markdown("Please log in to access the appraisal form or admin dashboard.")
    
    with st.container():
        st.markdown("### Sign In")
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        submitted = st.button("Login", type="primary", use_container_width=True)
        
        if submitted:
            if username == "admin" and password == "admin123":
                st.session_state.logged_in = True
                st.session_state.role = "admin"
                st.session_state.username = "Administrator"
                st.rerun()
            elif username.startswith("faculty") and password == "password":
                st.session_state.logged_in = True
                st.session_state.role = "faculty"
                st.session_state.username = username
                st.rerun()
            else:
                st.error("Invalid credentials. Try faculty1/password or admin/admin123.")

# --- Faculty Form Page (Google Form Style) ---
def faculty_page(df):
    st.title("📝 Annual Appraisal Form")
    st.markdown(f"**Applicant:** {st.session_state.username} | **Date:** {datetime.now().strftime('%B %d, %Y')}")
    st.info("Please complete all sections below. This form auto-calculates your base score upon submission.")
    
    # --- Section 1: Teaching ---
    st.divider()
    st.header("Section 1: Teaching Responsibilities")
    st.markdown("Enter details for lecture sections taken over the last academic year.")
    teaching_data = pd.DataFrame(columns=["Subject", "Section(s)/No. of Students", "Score"])
    edited_teaching = st.data_editor(teaching_data, num_rows="dynamic", use_container_width=True, key="t_edit")

    # --- Section 2: Publications ---
    st.divider()
    st.header("Section 2: Professional & Career Development")
    st.markdown("Search the institute database and select your published papers. They will be automatically categorized.")
    
    selected_sci = 0
    selected_non_sci = 0
    selected_scopus = 0
    
    if df.empty:
        st.warning("⚠️ The Central Publication CSV has not been uploaded by the Admin yet.")
    else:
        search_query = st.text_input("🔍 Search publications (Title, Abstract, Keywords, or Author):")
        search_results = semantic_search(df, search_query)
        
        if not search_results.empty:
            search_results.insert(0, "Select", False)
            edited_df = st.data_editor(
                search_results[['Select', 'Article Title', 'Authors', 'Index', 'Publication Year']],
                hide_index=True, use_container_width=True, key="pub_edit"
            )
            selected_papers = edited_df[edited_df['Select'] == True]
            
            if not selected_papers.empty:
                indexes = selected_papers['Index'].astype(str).str.upper()
                selected_sci = len(selected_papers[indexes.str.contains('SCI', na=False)])
                selected_non_sci = len(selected_papers[indexes.str.contains('ESCI', na=False)])
                selected_scopus = len(selected_papers[indexes.isin(['SCOPUS'])])
                
                st.success(f"✅ Auto-Categorized: {selected_sci} SCI | {selected_non_sci} Non-SCI | {selected_scopus} Scopus")

    # --- Section 3: Projects ---
    st.divider()
    st.header("Section 3: Infrastructure & Research Projects")
    st.markdown("List any ongoing or completed grants, consultancies, or infrastructure projects.")
    projects_data = pd.DataFrame(columns=["Project Title", "Cost (Lakhs)", "Agency", "Status"])
    edited_projects = st.data_editor(projects_data, num_rows="dynamic", use_container_width=True, key="p_edit")

    # --- Section 4: Thesis & Patents ---
    st.divider()
    st.header("Section 4: Thesis Supervision & Patents")
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("**Ph.D. / Masters Thesis Completed**")
        thesis_data = pd.DataFrame(columns=["Student Name", "Thesis Title", "Defense Date"])
        edited_thesis = st.data_editor(thesis_data, num_rows="dynamic", use_container_width=True, key="th_edit")
    with col2:
        st.markdown("**Patents Published / Granted**")
        patents_data = pd.DataFrame(columns=["Patent Title", "Status", "Date"])
        edited_patents = st.data_editor(patents_data, num_rows="dynamic", use_container_width=True, key="pat_edit")

    # --- Section 5: Goals & Submit ---
    st.divider()
    st.header("Section 5: Future Goals & Feedback")
    col3, col4 = st.columns(2)
    with col3:
        target_sci = st.selectbox("Number of Target SCI Publications:", ["0", "1", "2", "3", "4", "5+"])
    with col4:
        target_srs = st.selectbox("Targeted SRS Score:", ["< 3.0", "3.0 - 4.0", "4.0 - 4.5", "4.5+"])
    
    difficulties = st.text_area("Difficulties and Suggestions regarding academic assignments/self-growth (if any):")
    
    # --- Final Submission Area ---
    st.divider()
    st.markdown("### Declaration")
    st.checkbox("I confirm that the information provided above is accurate and true to the best of my knowledge.")
    
    submit_col1, submit_col2, submit_col3 = st.columns([1, 2, 1])
    with submit_col2:
        if st.button("🚀 Submit Complete Appraisal Form", type="primary", use_container_width=True):
            
            # Calculate Mock Scores
            teaching_score = pd.to_numeric(edited_teaching['Score'], errors='coerce').sum() if not edited_teaching.empty else 0
            pub_score = (selected_sci * 15) + (selected_non_sci * 10) + (selected_scopus * 5)
            proj_score = len(edited_projects) * 20
            total_score = teaching_score + pub_score + proj_score
            
            if total_score >= 100: rating = "Outstanding"
            elif total_score >= 60: rating = "Good"
            elif total_score >= 30: rating = "Developing"
            else: rating = "Poor"

            submission_record = {
                "Faculty Name": st.session_state.username,
                "Date Submitted": datetime.now().strftime("%Y-%m-%d %H:%M"),
                "Total Score": total_score,
                "Rating": rating,
                "SCI Papers": selected_sci,
                "Scopus Papers": selected_scopus,
                "Projects": len(edited_projects),
                "Target SCI Next Year": target_sci,
                "Feedback": difficulties
            }
            st.session_state.submissions.append(submission_record)
            st.success("🎉 Appraisal Submitted Successfully! You can now log out, and the Admin will review your profile.")
            st.balloons()

# --- Admin Page ---
def admin_page(df):
    st.title("🛡️ Administrator Dashboard")
    st.markdown("Review submitted appraisals and assign final committee ratings.")
    
    st.sidebar.markdown("### 🗄️ Central Database")
    uploaded_file = st.sidebar.file_uploader("Upload Institute Publication CSV", type=['csv'])
    if uploaded_file:
        df = load_data(uploaded_file)
        st.sidebar.success("Database active & ready for faculty searches.")

    st.divider()
    
    if len(st.session_state.submissions) == 0:
        st.info("No appraisals have been submitted yet. When faculty members submit their forms, they will appear here.")
    else:
        st.subheader("📋 Faculty Submissions Overview")
        sub_df = pd.DataFrame(st.session_state.submissions)
        st.dataframe(sub_df[["Faculty Name", "Date Submitted", "Total Score", "Rating"]], use_container_width=True)
        
        st.markdown("### 🔍 Detailed Reviews")
        for idx, sub in enumerate(st.session_state.submissions):
            with st.expander(f"Review: {sub['Faculty Name']} | Auto-Rating: {sub['Rating']} | Score: {sub['Total Score']}"):
                col1, col2 = st.columns(2)
                with col1:
                    st.write(f"**SCI Papers claimed:** {sub['SCI Papers']}")
                    st.write(f"**Scopus Papers claimed:** {sub['Scopus Papers']}")
                    st.write(f"**Projects ongoing:** {sub['Projects']}")
                with col2:
                    st.write(f"**Goals (Target SCI):** {sub['Target SCI Next Year']}")
                    st.write(f"**Faculty Feedback/Difficulties:**\n{sub['Feedback']}")
                
                st.markdown("---")
                st.markdown("**Final Committee Decision:**")
                dec_col1, dec_col2 = st.columns([3, 1])
                with dec_col1:
                    st.selectbox("Final Committee Rating Override:", ["Outstanding", "Good", "Developing", "Poor"], index=["Outstanding", "Good", "Developing", "Poor"].index(sub['Rating']), key=f"override_{idx}")
                with dec_col2:
                    st.markdown("<br>", unsafe_allow_html=True) # spacing
                    st.button("Approve & Finalize", key=f"approve_{idx}", type="primary", use_container_width=True)

# --- Main Routing ---
def main():
    st.set_page_config(page_title="Appraisal Portal", layout="wide")
    
    # Initialize empty dataframe for central DB
    df = pd.DataFrame() 

    # Logic to load central data automatically if file is in the same directory (for testing)
    try:
        df = pd.read_csv("Sample_Data.xlsx - Sheet1.csv")
    except:
        pass 

    if not st.session_state.logged_in:
        login_page()
    else:
        # Header with Logout
        col_header1, col_header2 = st.columns([8, 1])
        with col_header1:
            pass # Keep left empty for alignment
        with col_header2:
            st.button("Log Out", on_click=lambda: st.session_state.update({"logged_in": False, "role": None}))
        
        # Route to appropriate page
        if st.session_state.role == "faculty":
            faculty_page(df)
        elif st.session_state.role == "admin":
            admin_page(df)

if __name__ == "__main__":
    main()