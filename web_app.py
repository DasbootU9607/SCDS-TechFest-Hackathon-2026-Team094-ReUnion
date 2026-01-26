import streamlit as st
import time
import json
import random
import pandas as pd
import hashlib
import os
import base64
from dotenv import load_dotenv

# Database Imports
from models import SessionLocal, Job

load_dotenv()

# Try to import agents_system
try:
    from agents import CareerAIDEAgents
    # Instantiate the backend agents
    try:
        agents_system = CareerAIDEAgents()
    except Exception as e:
        # Fail silently for UI, error logged in terminal
        agents_system = None
except ImportError:
    agents_system = None

# --- DYNAMIC BACKGROUND GENERATOR ---
def get_dynamic_background():
    """Generates a random SVG wallpaper with multilingual career terms and logo watermark."""
    
    # 1. Base64 Encode Logo
    logo_path = "Documentations/Logo_OPT_White.png"
    logo_b64 = ""
    if os.path.exists(logo_path):
        with open(logo_path, "rb") as img_file:
            logo_b64 = base64.b64encode(img_file.read()).decode()
    
    # 2. Define Word Bank (Multilingual)
    words = [
        # English
        {"text": "CAREER", "font": "JetBrains Mono", "weight": 800},
        {"text": "SUCCESS", "font": "JetBrains Mono", "weight": 800},
        {"text": "AMBITION", "font": "JetBrains Mono", "weight": 800},
        {"text": "GROWTH", "font": "JetBrains Mono", "weight": 800},
        {"text": "FUTURE", "font": "JetBrains Mono", "weight": 800},
        {"text": "JOY", "font": "JetBrains Mono", "weight": 800},
        {"text": "PASSION", "font": "JetBrains Mono", "weight": 800},
        # French
        {"text": "ÉVOLUTION", "font": "Times New Roman", "style": "italic"},
        {"text": "RÊVE", "font": "Times New Roman", "style": "italic"},
        {"text": "PROGRÈS", "font": "Times New Roman", "style": "italic"},
        {"text": "AVENIR", "font": "Times New Roman", "style": "italic"},
        # Spanish
        {"text": "LOGRAR", "font": "Times New Roman", "style": "italic"},
        {"text": "AVANCE", "font": "Times New Roman", "style": "italic"},
        {"text": "ÉXITO", "font": "Times New Roman", "style": "italic"},
        # Chinese / Japanese
        {"text": "事业", "font": "Arial", "weight": 900},  # Career
        {"text": "成功", "font": "Arial", "weight": 900},  # Success
        {"text": "キャリア", "font": "Arial", "weight": 900}, # Career (JP)
        {"text": "夢", "font": "Arial", "weight": 900},      # Dream
    ]
    
    # 3. Generate Random SVG Elements
    svg_elements = []
    
    # Add Logo Watermark (Centered) if available
    if logo_b64:
        # 1200x1200 canvas, center is 600,600. Logo size ~400px wide?
        svg_elements.append(
            f'<image href="data:image/png;base64,{logo_b64}" x="350" y="450" width="500" height="300" opacity="0.05" filter="grayscale(100%)" transform="rotate(-15 600,600)" />'
        )
    
    # Generate ~25 random words scattered
    canvas_size = 1200
    for _ in range(25):
        word = random.choice(words)
        x = random.randint(50, canvas_size - 100)
        y = random.randint(50, canvas_size - 50)
        rot = random.randint(-45, 45)
        size = random.randint(20, 50)
        opacity = random.uniform(0.15, 0.25) # Slightly more visible
        
        font_style = f"font-family:'{word.get('font', 'sans-serif')}';"
        if 'weight' in word: font_style += f"font-weight:{word['weight']};"
        if 'style' in word: font_style += f"font-style:{word['style']};"
        
        svg_elements.append(
            f'<text x="{x}" y="{y}" transform="rotate({rot} {x},{y})" font-size="{size}" fill="white" fill-opacity="{opacity}" style="{font_style}text-transform:uppercase;">{word["text"]}</text>'
        )

    svg_content = "".join(svg_elements)
    svg = f"""<svg xmlns='http://www.w3.org/2000/svg' width='{canvas_size}' height='{canvas_size}' viewBox='0 0 {canvas_size} {canvas_size}'>{svg_content}</svg>"""
    
    # Encode SVG
    return base64.b64encode(svg.encode('utf-8')).decode('utf-8')

# --- 1. CONFIGURATION & STYLING ---
st.set_page_config(
    page_title="ReUnion",
    page_icon="Documentations/Logo_Trans.png",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Generate Dynamic Background on Run
bg_svg_b64 = get_dynamic_background()

# CUSTOM CSS - The "Transcendant" Theme
st.markdown(f"""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600&family=JetBrains+Mono:wght@400;500&display=swap');
    
    :root {{
        --bg-deep: #050505;
        --bg-card: rgba(20, 20, 20, 0.4);
        --glass-border: rgba(255, 255, 255, 0.08);
        --text-primary: #EDEDED;
        --text-secondary: #888888;
        --accent-glow: 0 0 20px rgba(120, 119, 198, 0.3);
        --accent-color: #7877C6; /* Linear-esque purple */
        --success-glow: 0 0 20px rgba(50, 200, 100, 0.2);
    }}

    /* GLOBAL RESET & ANIMATIONS */
    .stApp {{
        background-color: var(--bg-deep);
        /* Dynamic SVG Wallpaper */
        background-image: 
            radial-gradient(circle at 50% 0%, rgba(120, 119, 198, 0.15), transparent 40%),
            linear-gradient(to bottom, rgba(5,5,5,0.5) 0%, rgba(5,5,5,0.8) 100%),
            url("data:image/svg+xml;base64,{bg_svg_b64}");
        background-repeat: repeat;
        background-size: 1200px 1200px, 100% 100%, 1200px 1200px;
        background-attachment: fixed;
        color: var(--text-primary);
        font-family: 'Inter', sans-serif;
    }}

    @keyframes fadeIn {{
        from {{ opacity: 0; transform: translateY(10px); }}
        to {{ opacity: 1; transform: translateY(0); }}
    }}
    
    /* TYPOGRAPHY */
    h1, h2, h3 {{
        font-family: 'Inter', sans-serif;
        font-weight: 600;
        letter-spacing: -0.03em;
        color: white !important;
    }}
    
    .gradient-text {{
        background: linear-gradient(90deg, #FFFFFF, #999999);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }}

    /* HIDE STREAMLIT CHROME */
    #MainMenu, footer {{ visibility: hidden; }}
    [data-testid="stSidebar"] {{
        background-color: #0A0A0A;
        border-right: 1px solid var(--glass-border);
    }}

    /* CARDS (Glassmorphism) */
    .glass-card {{
        background: var(--bg-card);
        backdrop-filter: blur(12px);
        -webkit-backdrop-filter: blur(12px);
        border: 1px solid var(--glass-border);
        border-radius: 12px;
        padding: 24px;
        transition: all 0.3s cubic-bezier(0.25, 0.8, 0.25, 1);
        animation: fadeIn 0.5s ease-out forwards;
        position: relative;
        overflow: hidden;
    }}
    
    .glass-card:hover {{
        transform: translateY(-2px);
        border-color: rgba(255, 255, 255, 0.15);
        box-shadow: 0 10px 30px -10px rgba(0,0,0,0.5);
    }}

    /* BUTTONS */
    .stButton button {{
        background: linear-gradient(180deg, rgba(30,30,30,0.8) 0%, rgba(20,20,20,1) 100%);
        border: 1px solid var(--glass-border);
        color: white;
        border-radius: 8px;
        padding: 6px 16px;
        font-size: 13px;
        font-weight: 500;
        transition: all 0.2s;
        box-shadow: 0 2px 5px rgba(0,0,0,0.2);
    }}
    .stButton button:hover {{
        border-color: rgba(255,255,255,0.3);
        box-shadow: 0 0 10px rgba(255,255,255,0.1);
        color: white;
    }}

    /* ROADMAP NODES */
    .node-container {{
        display: flex;
        flex-direction: column;
        align-items: flex-start;
        position: relative;
        margin-left: 20px;
        padding-left: 20px;
        border-left: 1px solid rgba(255,255,255,0.1);
    }}
    .node-item {{
        margin-bottom: 24px;
        position: relative;
    }}
    .node-dot {{
        position: absolute;
        left: -25px;
        top: 6px;
        width: 10px;
        height: 10px;
        background: #000;
        border: 2px solid #555;
        border-radius: 50%;
        transition: all 0.3s ease;
        z-index: 10;
    }}
    .node-item.active .node-dot {{
        border-color: var(--accent-color);
        box-shadow: 0 0 10px var(--accent-color);
        background: var(--accent-color);
    }}
    
    /* TAGS */
    .tech-tag {{
        font-family: 'JetBrains Mono', monospace;
        font-size: 10px;
        background: rgba(255,255,255,0.05);
        border: 1px solid rgba(255,255,255,0.1);
        border-radius: 4px;
        padding: 2px 6px;
        color: #AAA;
    }}

    /* NAVIGATION HEADER */
    .nav-header {{
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding: 16px 0;
        margin-bottom: 40px;
        border-bottom: 1px solid rgba(255,255,255,0.05);
        position: sticky;
        top: 0;
        z-index: 100;
        margin-top: -60px; /* Counteract Streamlit padding */
    }}
</style>
""", unsafe_allow_html=True)

# --- 2. DATA MODELS & DB ACCESS ---

def get_db():
    return SessionLocal()

def update_job_status(job_id, new_status):
    """Update job status in the Central Database"""
    session = get_db()
    try:
        # job_id is external_id in our DB model based on ingest.py
        # But let's check how we load it. 
        # ingest.py: job_record.external_id = item['id']
        job = session.query(Job).filter(Job.external_id == job_id).first()
        if job:
            job.application_status = new_status
            session.commit()
            return True
        return False
    except Exception as e:
        st.error(f"Failed to update status: {e}")
        return False
    finally:
        session.close()

@st.cache_data(ttl=60) # Short cache for live status updates
def load_jobs_from_db():
    session = get_db()
    try:
        jobs = session.query(Job).all()
        data = []
        for j in jobs:
            # Reconstruct dictionary for DataFrame
            data.append({
                'id': j.external_id,
                'title': j.title,
                'company': j.company,
                'location': j.location,
                'salary': f"${j.salary_min} - ${j.salary_max}" if j.salary_max else f"${j.salary_min}",
                'description': j.description,
                'tags': j.skills_required if j.skills_required else [],
                'status': j.application_status,
                'match': random.randint(70, 95) # Placeholder AI Match Score
            })
        
        if not data:
            return pd.DataFrame()

        df = pd.DataFrame(data)
        df['logo'] = df['company'].apply(lambda x: x[0] if isinstance(x, str) else "?")
        df['roadmap'] = [[] for _ in range(len(df))] # Placeholder for roadmap in memory
        
        return df
    except Exception as e:
        st.error(f"Database Connection Error: {e}")
        return pd.DataFrame()
    finally:
        session.close()

# --- 3. COMPONENTS ---

def render_nav():
    st.markdown("""
    <div class="nav-header">
        <div style="font-family: 'JetBrains Mono'; font-weight: 600; color: #FFF; display: flex; align-items: center;">
            <span style="color: #7877C6; margin-right: 8px;">✦</span> REUNION <span style="opacity: 0.3; margin: 0 8px;">/</span> INTERFACE
        </div>
        <div style="font-size: 12px; color: #666; font-family: 'Inter'; border: 1px solid #333; padding: 4px 8px; border-radius: 4px;">
            Connected to Central DB
        </div>
    </div>
    
    <script>
    // Hotkey to toggle sidebar: Shift + S
    document.addEventListener('keydown', function(e) {
        if (e.shiftKey && e.key.toLowerCase() === 's') {
            const toggleBtn = window.parent.document.querySelector('[data-testid="stSidebarCollapsedControl"]') || 
                              window.parent.document.querySelector('[data-testid="stSidebarExpandedControl"]');
            if (toggleBtn) {
                toggleBtn.click();
            }
        }
    });
    </script>
    """, unsafe_allow_html=True)

def render_hero():
    # Center the logo
    _, col, _ = st.columns([1.5, 2, 1.5])
    with col:
        st.image("Documentations/Logo_Trans.png", use_container_width=True)

    st.markdown("""
    <div style="text-align: center; margin: 20px 0 60px 0;">
        <h1 style="font-size: 48px; margin-bottom: 16px;">
            <span class="gradient-text">Your Career,</span><br>
            <span style="color: #7877C6;">Leaping Further Ahead.</span>
        </h1>
        <p style="color: #888; max-width: 500px; margin: 0 auto; line-height: 1.6; font-size: 18px;">
            Amidst the volcanic volatility of the transparency gap, ReUnion serves as your immutable bedrock. We bridge the chasm of silent market shifts, realigning the static snapshots of your talent to reunite your siloed potential with the radical transparency of its true, innovative value.
        </p>
    </div>
    """, unsafe_allow_html=True)

def render_job_grid():
    # Load Real Data from DB
    jobs_df = load_jobs_from_db()
    
    if jobs_df.empty:
        st.warning("Central Database is empty. Please run 'python ingest.py' to populate data.")
        return

    # Sidebar Filters
    with st.sidebar:
        st.header("Profile")
        if 'user_profile_text' not in st.session_state:
            st.session_state.user_profile_text = "I am a Junior Data Scientist with experience in Python, Pandas, and Scikit-Learn. I have built a few projects predicting housing prices. I want to learn more about Deep Learning and Cloud deployment."
        
        user_profile_input = st.text_area("Your Skills / Resume", st.session_state.user_profile_text, height=150)
        st.session_state.user_profile_text = user_profile_input
        
        st.markdown("---")
        st.header("Filter Jobs")
        
        # Location Filter
        locations = sorted(jobs_df['location'].dropna().unique())
        selected_locations = st.multiselect("Location", locations)
        
        # Tech Stack Filter (Bonus Feature)
        all_skills = set()
        for skills in jobs_df['tags']:
            if isinstance(skills, list):
                all_skills.update(skills)
        sorted_skills = sorted(list(all_skills))
        selected_tech = st.multiselect("Tech Stack", sorted_skills)
        
        # Role Type Filter
        role_types = ["All", "Intern", "Junior", "Senior", "Manager"]
        selected_role = st.selectbox("Role Level", role_types)

    # Apply Filters
    filtered_df = jobs_df.copy()
    
    if selected_locations:
        filtered_df = filtered_df[filtered_df['location'].isin(selected_locations)]
        
    if selected_tech:
        # Filter rows where at least one selected tech is in the tags list
        filtered_df = filtered_df[filtered_df['tags'].apply(lambda tags: any(tech in tags for tech in selected_tech))]
        
    if selected_role != "All":
        filtered_df = filtered_df[filtered_df['title'].str.contains(selected_role, case=False, na=False)]

    # Grid Layout
    st.markdown("### <span style='opacity:0.7; font-size:14px; text-transform:uppercase; letter-spacing:1px;'>Opportunities</span>", unsafe_allow_html=True)
    
    if filtered_df.empty:
        st.warning("No jobs found matching your criteria.")
        return

    cols = st.columns(3)
    
    for i, (index, job) in enumerate(filtered_df.iterrows()):
        col = cols[i % 3]
        with col:
            # Determine card border color based on status
            status_color = "rgba(255,255,255,0.08)"

            st.markdown(f"""
            <div class="glass-card" style="height: 300px; display: flex; flex-direction: column; border-color: {status_color};">
                <div style="display: flex; justify-content: space-between; align-items: start; margin-bottom: 20px;">
                    <div style="width: 32px; height: 32px; background: rgba(255,255,255,0.1); border-radius: 6px; display: flex; align-items: center; justify-content: center; font-weight: bold;">{job['logo']}</div>
                    <div style="text-align:right;">
                        <div style="font-family: 'JetBrains Mono'; font-size: 12px; color: { '#7877C6' if job['match'] > 80 else '#888' }">{job['match']}% MATCH</div>
                        <div style="font-size: 10px; color: #AAA; margin-top:4px;">{job['status']}</div>
                    </div>
                </div>
                <h3 style="font-size: 16px; margin-bottom: 4px; color: white;">{job['title']}</h3>
                <p style="font-size: 13px; color: #888; margin-bottom: 16px;">{job['company']}</p>
                <div style="flex-grow: 1;">
                    <div style="display: flex; flex-wrap: wrap; gap: 6px;">
                        {''.join([f'<span class="tech-tag">{t}</span>' for t in job['tags'][:5]])}
                    </div>
                </div>
                <div style="border-top: 1px solid rgba(255,255,255,0.1); padding-top: 12px; display: flex; justify-content: space-between; align-items: center;">
                    <span style="font-size: 12px; color: #666;">{job['location']}</span>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            if st.button(f"View Roadmap", key=f"btn_{job['id']}_{i}", use_container_width=True):
                job_data = job.to_dict()
                
                if not job_data['roadmap']:
                    with st.spinner("Generating Roadmap..."):
                        if agents_system:
                            roadmap = agents_system.perform_gap_analysis(
                                st.session_state.user_profile_text, 
                                job_data['description']
                            )
                            job_data['roadmap'] = roadmap
                        else:
                            time.sleep(1)
                            job_data['roadmap'] = [
                                {"step": "Connect Agent", "desc": "AI Backend offline.", "type": "error", "status": "todo"}
                            ]
                
                st.session_state.selected_job = job_data
                st.session_state.view = 'roadmap'
                st.rerun()

def render_roadmap_detail(job):
    # Back Navigation
    c1, c2 = st.columns([1, 10])
    with c1:
        if st.button("← Back", use_container_width=True):
            st.session_state.view = 'dashboard'
            st.rerun()
            
    # Header & Tracking Control
    st.markdown(f"""
    <div style="margin: 20px 0 20px 0; border-bottom: 1px solid rgba(255,255,255,0.1); padding-bottom: 20px;">
        <div style="font-family:'JetBrains Mono'; color:#7877C6; font-size: 12px; margin-bottom: 8px;">{job['id']}</div>
        <h1 style="font-size: 32px; margin: 0;">{job['title']} @ {job['company']}</h1>
    </div>
    """, unsafe_allow_html=True)

    # Application Tracking (Write to DB)
    st.markdown("##### Application Tracking")
    status_options = ["New", "Applied", "Interviewing", "Offer", "Rejected"]
    try:
        current_index = status_options.index(job['status'])
    except:
        current_index = 0
        
    new_status = st.selectbox("Current Status", status_options, index=current_index, key="status_selector")
    
    if new_status != job['status']:
        if update_job_status(job['id'], new_status):
            st.success(f"Status updated to {new_status}!")
            # Update local state to reflect change immediately without full reload
            st.session_state.selected_job['status'] = new_status
            time.sleep(1)
            st.rerun()
    
    col_main, col_chat = st.columns([1.5, 1])
    
    with col_main:
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("#### <span style='opacity:0.6'>SKILL ACQUISITION PLAN</span>", unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)
        
        # Render Nodes
        for i, step in enumerate(job['roadmap']):
            step_status = step.get('status', 'todo')
            active_cls = "active" if step_status == "in-progress" else ""
            opacity = "0.4" if step_status == "todo" else "1.0"
            color = "#7877C6" if step_status == "in-progress" else ("#32C864" if step_status == "done" else "#888")
            
            st.markdown(f"""
            <div class="node-container">
                <div class="node-item {active_cls}" style="opacity: {opacity};">
                    <div class="node-dot" style="background: {color}; border-color: {color}; box-shadow: 0 0 10px {color};"></div>
                    <div class="glass-card" style="padding: 16px; margin-top: -10px;">
                        <div style="font-size: 11px; text-transform: uppercase; letter-spacing: 1px; color: {color}; margin-bottom: 4px;">{step['type']}</div>
                        <div style="font-weight: 600; font-size: 15px; color: white;">{step['step']}</div>
                        <div style="font-size: 13px; color: #888; margin-top: 4px;">{step['desc']}</div>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)

    with col_chat:
        st.markdown("""
        <div style="background: rgba(255,255,255,0.03); border: 1px solid rgba(255,255,255,0.05); border-radius: 12px; height: 100%; padding: 20px;">
            <div style="font-family:'JetBrains Mono'; font-size:12px; color:#666; margin-bottom:20px;">AI ASSISTANT CONTEXT</div>
        """, unsafe_allow_html=True)
        
        # Chat History
        chat_container = st.container(height=350)
        with chat_container:
            for msg in st.session_state.chat_history:
                align = "right" if msg["role"] == "user" else "left"
                bg = "rgba(120, 119, 198, 0.2)" if msg["role"] == "user" else "rgba(255,255,255,0.05)"
                st.markdown(f"""
                <div style="display:flex; justify-content:{align}; margin-bottom:10px;">
                    <div style="background:{bg}; padding:8px 12px; border-radius:8px; font-size:13px; max-width:80%;">
                        {msg['content']}
                    </div>
                </div>
                """, unsafe_allow_html=True)
        
        # Input
        if prompt := st.chat_input("Ask ReUnion about this role..."):
            st.session_state.chat_history.append({"role": "user", "content": prompt})
            
            if agents_system:
                try:
                    context = f"Job: {job['title']} at {job['company']}. Roadmap: {json.dumps(job['roadmap'])}"
                    response = agents_system.process_query(f"Context: {context}. User: {prompt}", st.session_state.user_data)
                    st.session_state.chat_history.append({"role": "assistant", "content": response['answer']})
                except Exception as e:
                    st.session_state.chat_history.append({"role": "assistant", "content": "System offline."})
            else:
                 # Simulating AI response for UI demo
                time.sleep(0.5)
                st.session_state.chat_history.append({"role": "assistant", "content": f"I can help you with {job['title']}. The roadmap suggests focusing on {job['roadmap'][0]['step']} first."})
            
            st.rerun()

        st.markdown("</div>", unsafe_allow_html=True)

# --- 4. MAIN APP LOGIC ---

def main():
    if 'view' not in st.session_state:
        st.session_state.view = 'dashboard'
    if 'selected_job' not in st.session_state:
        st.session_state.selected_job = None
    if 'user_data' not in st.session_state:
        st.session_state.user_data = {'role': 'Data Scientist', 'interests': 'AI'}
    if 'chat_history' not in st.session_state:
        st.session_state.chat_history = []

    render_nav()
    
    if st.session_state.view == 'dashboard':
        render_hero()
        render_job_grid()
    elif st.session_state.view == 'roadmap' and st.session_state.selected_job:
        render_roadmap_detail(st.session_state.selected_job)

if __name__ == "__main__":
    main()