import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from schema import BatteryConfig, EnergyProfile
from solver import EnergySolver

# ---------------------------------------------------------
# Page Setup & Page Config
# ---------------------------------------------------------
st.set_page_config(
    page_title="Microgrid Energy Dispatch Lab",
    page_icon="⚡",
    layout="wide"
)

# ---------------------------------------------------------
# Custom CSS: Site Theme & Enlarged Sidebar Controls
# ---------------------------------------------------------
st.markdown("""
    <style>
    /* Main page background - Warm Linen/Cream */
    .stApp {
        background-color: #FAF7F2;
        color: #1E1B18;
    }

    /* Sidebar background (width left untouched) */
    [data-testid="stSidebar"] {
        background-color: #F2ECE4;
        border-right: 1px solid #E5DDCF;
    }

    /* Enlarged Sidebar Headers */
    [data-testid="stSidebar"] h1, 
    [data-testid="stSidebar"] h2, 
    [data-testid="stSidebar"] h3 {
        font-size: 1.35rem !important;
        font-weight: 700 !important;
        color: #1E1B18 !important;
    }

    /* Enlarged Sidebar Labels & Captions */
    [data-testid="stSidebar"] label, 
    [data-testid="stSidebar"] .stWidgetLabel p {
        font-size: 1.12rem !important;
        font-weight: 600 !important;
        color: #1E1B18 !important;
    }

    [data-testid="stSidebar"] p, 
    [data-testid="stSidebar"] .stCaption {
        font-size: 1.05rem !important;
        color: #4A443F !important;
    }

    /* Enlarged Sidebar Input Boxes & Slider Values */
    [data-testid="stSidebar"] input {
        font-size: 1.1rem !important;
    }
    
    [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p {
        font-size: 1.08rem !important;
    }

    /* Metric cards styling */
    div[data-testid="stMetric"] {
        background-color: #FFFFFF;
        border: 1px solid #EBE3D5;
        padding: 18px;
        border-radius: 12px;
        box-shadow: 0 2px 8px rgba(30, 27, 24, 0.04);
    }

    /* Graph Container Card */
    div[data-testid="stPlotlyChart"] {
        background-color: #FFFFFF;
        border: 1px solid #EBE3D5;
        border-radius: 14px;
        padding: 18px 18px 10px 18px;
        box-shadow: 0 2px 10px rgba(30, 27, 24, 0.04);
    }

    /* Global typography */
    h1, h2, h3, h4, h5, h6, p, span {
        color: #1E1B18 !important;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    }

    /* Expander styling */
    .streamlit-expanderHeader {
        background-color: #FFFFFF !important;
        border-radius: 8px;
        border: 1px solid #EBE3D5;
        font-size: 1.05rem !important;
    }
    </style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------
# Palette & Graph Style Constants
# ---------------------------------------------------------
COLOR_DEMAND    = "#1E1B18"  # High-contrast Charcoal
COLOR_RENEWABLE = "#2A7B54"  # Forest Green
COLOR_GRID      = "#DC4C3E"  # Terracotta Red
COLOR_SOC       = "#4F6BED"  # Warm Indigo

COLOR_TEXT      = "#1E1B18"  # Strong dark text for pure white background
COLOR_AXIS_LINE = "#38332E"  # Distinct axis lines & ticks
COLOR_GRIDLINE  = "#E8E2D8"  # Clear gridlines

# ---------------------------------------------------------
# Page Header
# ---------------------------------------------------------
st.title("Energy Dashboard")
st.markdown("Adjust key variables in the sidebar to simulate microgrid performance in real time.")

# ---------------------------------------------------------
# Sidebar Controls & Settings
# ---------------------------------------------------------
with st.sidebar:
    st.header("Controls")
    st.caption("Customize your battery and price parameters.")
    
    st.subheader("Battery Settings")
    battery_capacity = st.slider(
        "Battery Capacity (kWh)", 
        min_value=1.0, max_value=50.0, value=10.0, step=0.5,
        help="Maximum energy storage capacity."
    )
    initial_soc = st.slider(
        "Starting Charge Level (kWh)", 
        min_value=0.0, max_value=battery_capacity, value=2.0, step=0.5,
        help="Energy stored in the battery at the start of the day (Hour 0)."
    )

    st.divider()
    st.subheader("Price")
    grid_cost = st.number_input(
        "Grid Energy Price ($/kWh)", 
        min_value=0.01, max_value=2.0, value=0.12, step=0.01,
        help="Cost per kWh imported from the grid."
    )

    st.divider()
    st.subheader("Scaling Factors")
    demand_multiplier = st.slider(
        "Demand Scale", 
        min_value=0.5, max_value=2.0, value=1.0, step=0.1,
        help="Multiply baseline hourly electricity demand."
    )
    solar_multiplier = st.slider(
        "Solar Generation Scale", 
        min_value=0.5, max_value=2.0, value=1.0, step=0.1,
        help="Multiply baseline solar output."
    )

# ---------------------------------------------------------
# Baseline Profiles & Optimization Input
# ---------------------------------------------------------
base_demand = [1.5, 1.2, 1.0, 1.0, 1.2, 2.0, 3.5, 4.0, 3.0, 2.5, 2.0, 2.0, 
               2.2, 2.5, 3.0, 3.5, 4.5, 5.0, 4.0, 3.5, 2.5, 2.0, 1.8, 1.5]
base_renewable = [0.0, 0.0, 0.0, 0.0, 0.0, 0.5, 2.0, 4.5, 6.0, 7.5, 8.0, 8.0, 
                  7.0, 6.0, 4.0, 2.0, 0.5, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]

battery_cfg = BatteryConfig(
    capacity_kwh=battery_capacity,
    initial_soc_kwh=initial_soc
)

profile_data = EnergyProfile(
    demand=[d * demand_multiplier for d in base_demand],
    renewable=[r * solar_multiplier for r in base_renewable],
    grid_cost=[grid_cost] * 24
)

# ---------------------------------------------------------
# Optimization Execution & Display
# ---------------------------------------------------------
try:
    solver = EnergySolver(battery=battery_cfg, profile=profile_data)
    df = solver.solve()
    df["Hour"] = df.index
    
    # Summary Metrics
    total_grid_cost = (df["Grid_Import"] * grid_cost).sum()
    total_grid_kwh = df["Grid_Import"].sum()
    wasted_solar = df["Wasted_Renewable"].sum()

    st.subheader("Key Metrics")
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Est. Grid Cost", f"${total_grid_cost:.2f}")
    col2.metric("Grid Energy Drawn", f"{total_grid_kwh:.1f} kWh")
    col3.metric("Unused Solar Energy", f"{wasted_solar:.1f} kWh")
    col4.metric("Battery Capacity", f"{battery_capacity:.1f} kWh")

    st.markdown("---")

    # ---------------------------------------------------------
    # Plotly Visualizations (Pure White Canvas & Enhanced Labels/Ticks)
    # ---------------------------------------------------------
    fig = make_subplots(
        rows=2, cols=1, 
        shared_xaxes=True,
        vertical_spacing=0.15,
        subplot_titles=("Demand vs. Solar & Grid Import (kWh)", "Battery Charge")
    )

    # Top Chart Traces
    fig.add_trace(go.Scatter(
        x=df["Hour"], y=df["Demand"], name="Demand", 
        line=dict(color=COLOR_DEMAND, width=3, dash="dash")
    ), row=1, col=1)
    
    fig.add_trace(go.Scatter(
        x=df["Hour"], y=df["Renewable"], name="Solar Generation", 
        line=dict(color=COLOR_RENEWABLE, width=3)
    ), row=1, col=1)
    
    fig.add_trace(go.Scatter(
        x=df["Hour"], y=df["Grid_Import"], name="Grid Import", 
        line=dict(color=COLOR_GRID, width=3)
    ), row=1, col=1)

    # Bottom Chart Trace
    fig.add_trace(go.Scatter(
        x=df["Hour"], y=df["Battery_SoC"], name="Battery Storage Level", 
        fill="tozeroy", 
        fillcolor="rgba(79, 107, 237, 0.15)", 
        line=dict(color=COLOR_SOC, width=3)
    ), row=2, col=1)
    
    fig.add_hline(
        y=battery_capacity, line_dash="dot", line_color="#8C8275", line_width=2,
        annotation_text="Max Capacity", annotation_position="bottom right",
        annotation_font=dict(size=13, color=COLOR_TEXT),
        row=2, col=1
    )

    # Enlarge Subplot Titles
    fig.for_each_annotation(
        lambda a: a.update(font=dict(size=17, color=COLOR_TEXT, family="sans-serif"))
    )

    # Overall Layout & Legend Configuration
    fig.update_layout(
        template="plotly_white",
        paper_bgcolor="#FFFFFF",
        plot_bgcolor="#FFFFFF",
        font=dict(color=COLOR_TEXT, family="sans-serif", size=14),
        height=680, 
        hovermode="x unified",
        margin=dict(t=100, b=50, l=65, r=40),
        
        # Prominent Legend
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.08,
            xanchor="center",
            x=0.5,
            bgcolor="#FFFFFF",
            bordercolor="#D6CEC2",
            borderwidth=1.5,
            font=dict(size=14, color=COLOR_TEXT)
        )
    )

    # Shared Axis Options (Visible lines, thick tick marks, high-contrast labels)
    axis_styling = dict(
        showline=True,
        linecolor=COLOR_AXIS_LINE,
        linewidth=2,
        ticks="outside",
        ticklen=6,
        tickwidth=2,
        tickcolor=COLOR_AXIS_LINE,
        tickfont=dict(size=13, color=COLOR_TEXT),
        title_font=dict(size=15, color=COLOR_TEXT),
        showgrid=True,
        gridcolor=COLOR_GRIDLINE
    )

    # Apply axis options to subplots
    fig.update_xaxes(**axis_styling, row=1, col=1)
    fig.update_xaxes(**axis_styling, title_text="Hour of Day (0–23)", tickmode="linear", tick0=0, dtick=1, row=2, col=1)
    fig.update_yaxes(**axis_styling, title_text="Energy (kWh)", row=1, col=1)
    fig.update_yaxes(**axis_styling, title_text="Stored Level (kWh)", row=2, col=1)

    st.plotly_chart(fig, use_container_width=True)

    # Data Drawer
    with st.expander("🔍 Inspect Time-Series Dispatch Data"):
        st.dataframe(df.style.format("{:.2f}"), use_container_width=True)

except Exception as e:
    st.error(f"Optimization failed: {str(e)}")