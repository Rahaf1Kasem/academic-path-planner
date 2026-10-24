import streamlit as st
import networkx as nx
from pyvis.network import Network
import streamlit.components.v1 as components

# Page configuration and layout setup
st.set_page_config(
    page_title="Academic Pathway Planner",
    page_icon="🎓",
    layout="wide"
)

# Custom CSS to hide GitHub icon and link
hide_github_style = """
<style>
a[href*="github.com"] {
    display: none !important;
}
}
</style>
"""
st.markdown(hide_github_style, unsafe_allow_html=True)

st.title("🎓 Smart Academic Pathway Planner")
st.markdown("An interactive system to organize study plans, order courses by prerequisites, and distribute them across semesters automatically.")

# Initialize session state for courses
if "courses" not in st.session_state:
    st.session_state.courses = {
        "Programming 1": [],
        "Mathematics 1": [],
        "Programming 2": ["Programming 1"],
        "Data Structures": ["Programming 2", "Mathematics 1"],
        "Algorithms": ["Data Structures"],
        "Databases": ["Programming 2"]
    }

# Sidebar: Control Panel
st.sidebar.header("⚙️ Control Panel")

# 1. Add new course
with st.sidebar.expander("➕ Add New Course", expanded=True):
    new_course = st.text_input("Course Name:")
    existing_courses = list(st.session_state.courses.keys())
    selected_prereqs = st.multiselect("Prerequisites:", options=existing_courses)
    
    if st.button("Add Course"):
        if new_course.strip() == "":
            st.sidebar.error("Please enter a valid course name.")
        elif new_course in st.session_state.courses:
            st.sidebar.warning("Course already exists!")
        else:
            st.session_state.courses[new_course] = selected_prereqs
            st.sidebar.success(f"Added ({new_course}) successfully!")
            st.rerun()

# 2. Edit existing course prerequisites
with st.sidebar.expander("✏️ Edit Course Prerequisites"):
    course_to_edit = st.selectbox("Select Course:", options=["-- Select Course --"] + list(st.session_state.courses.keys()), key="edit_course_select")
    if course_to_edit != "-- Select Course --":
        current_prereqs = st.session_state.courses[course_to_edit]
        other_courses = list(st.session_state.courses.keys())
        new_prereqs = st.multiselect("Update Prerequisites:", options=other_courses, default=[p for p in current_prereqs if p in other_courses], key="edit_prereqs_select")
        
        if st.button("Save Changes"):
            st.session_state.courses[course_to_edit] = new_prereqs
            st.sidebar.success(f"Updated prerequisites for ({course_to_edit})!")
            st.rerun()

# 3. Delete a course
with st.sidebar.expander("🗑️ Delete Course"):
    course_to_delete = st.selectbox("Select Course to Delete:", options=["-- Select Course --"] + list(st.session_state.courses.keys()))
    if st.button("Confirm Deletion"):
        if course_to_delete != "-- Select Course --":
            del st.session_state.courses[course_to_delete]
            for c, prereqs in st.session_state.courses.items():
                if course_to_delete in prereqs:
                    st.session_state.courses[c].remove(course_to_delete)
            st.sidebar.success(f"Deleted ({course_to_delete}) successfully!")
            st.rerun()

# 4. Reset to default plan
if st.sidebar.button("🔄 Reset to Default Plan"):
    st.session_state.courses = {
        "Programming 1": [],
        "Mathematics 1": [],
        "Programming 2": ["Programming 1"],
        "Data Structures": ["Programming 2", "Mathematics 1"],
        "Algorithms": ["Data Structures"],
        "Databases": ["Programming 2"]
    }
    st.rerun()

# Processing and Scheduling Logic

def create_graph(courses_dict):
    G = nx.DiGraph()
    for course, prereqs in courses_dict.items():
        G.add_node(course)
        for p in prereqs:
            G.add_edge(p, course)
    return G

G = create_graph(st.session_state.courses)

def kahns_topological_sort(G):
    in_degree = {node: 0 for node in G.nodes()}
    for node in G.nodes():
        for neighbor in G.successors(node):
            in_degree[neighbor] += 1

    queue = [node for node in G.nodes() if in_degree[node] == 0]
    topo_order = []

    while queue:
        current = queue.pop(0)
        topo_order.append(current)

        for neighbor in G.successors(current):
            in_degree[neighbor] -= 1
            if in_degree[neighbor] == 0:
                queue.append(neighbor)

    if len(topo_order) != len(G.nodes()):
        return None, "🚨 Error: Circular dependency detected in the plan! Please review prerequisites."
    
    return topo_order, None

def schedule_semesters(G, topo_order):
    semesters = {}
    levels = {node: 0 for node in G.nodes()}
    
    for node in topo_order:
        predecessors = list(G.predecessors(node))
        if predecessors:
            max_level = max(levels[p] for p in predecessors)
            levels[node] = max_level + 1
        else:
            levels[node] = 0

    for node, lvl in levels.items():
        sem = lvl + 1
        if sem not in semesters:
            semesters[sem] = []
        semesters[sem].append(node)
        
    return semesters

# Main Interface

topo_order, error = kahns_topological_sort(G) if st.session_state.courses else (None, None)

col1, col2 = st.columns([1, 1.2])

with col1:
    st.subheader("📚 Course List & Prerequisites")
    if not st.session_state.courses:
        st.info("No courses added currently.")
    else:
        for course, prereqs in st.session_state.courses.items():
            prereq_str = ", ".join(prereqs) if prereqs else "None (Core)"
            st.write(f"- **{course}**: `Prerequisites:` {prereq_str}")

with col2:
    st.subheader("📊 Interactive Pathway Map")
    if not st.session_state.courses:
        st.info("Add courses to view the interactive map.")
    elif error:
        st.error("⚠️ Cannot render map due to circular dependencies.")
    else:
        net = Network(height="450px", width="100%", directed=True, bgcolor="#ffffff", font_color="#000000")
        
        for node in G.nodes():
            net.add_node(
                node, 
                label=node, 
                title=node, 
                color={"background": "#4A90E2", "border": "#2C3E50"},
                size=30, 
                font={"size": 18, "color": "#000000", "face": "Tahoma", "vadjust": -35}
            )
            
        for edge in G.edges():
            net.add_edge(edge[0], edge[1], color="#7F8C8D", width=2, arrows="to")
            
        net.set_options("""
        {
          "layout": {
            "hierarchical": {
              "enabled": true,
              "direction": "UD",
              "sortMethod": "directed",
              "nodeSpacing": 150,
              "levelSeparation": 150
            }
          },
          "physics": {
            "hierarchicalRepulsion": {
              "centralGravity": 0.0,
              "springLength": 100,
              "springConstant": 0.01,
              "nodeDistance": 120,
              "damping": 0.09
            }
          }
        }
        """)
        
        try:
            path = "tmp_graph.html"
            net.save_graph(path)
            with open(path, 'r', encoding='utf-8') as f:
                html_data = f.read()
            components.html(html_data, height=480)
        except Exception as e:
            st.error(f"Error rendering network: {e}")

st.markdown("---")
st.subheader("🚀 Automatic Scheduling")

if st.session_state.courses:
    if error:
        st.error(error)
    else:
        st.success("✅ Academic plan is valid and ready!")
        st.write("**Chronological Study Order:**", " ⬅️ ".join(topo_order))
        
        semesters = schedule_semesters(G, topo_order)
        
        st.markdown("### 🗓️ Proposed Semester Distribution:")
        cols = st.columns(len(semesters))
        for i, (sem, courses) in enumerate(semesters.items()):
            with cols[i]:
                st.markdown(f"#### Semester {sem}")
                for c in courses:
                    st.markdown(f"- 📖 {c}")