"""Shared CSS styles and UI helpers for the coaching app."""

import streamlit as st


def inject_custom_css() -> None:
    """Inject custom CSS for a polished coaching-app look."""
    st.markdown(
        """
        <style>
        /* --- Global tweaks --- */
        .block-container {
            padding-top: 2rem;
            padding-bottom: 2rem;
        }

        /* Sidebar branding area */
        [data-testid="stSidebar"] > div:first-child {
            padding-top: 1rem;
        }
        .sidebar-brand {
            text-align: center;
            padding: 1.2rem 0.5rem;
            margin-bottom: 1rem;
            border-bottom: 1px solid #e0d8f0;
        }
        .sidebar-brand h2 {
            margin: 0;
            font-size: 1.25rem;
            color: #7C5CFC;
        }
        .sidebar-brand p {
            margin: 0.3rem 0 0 0;
            font-size: 0.82rem;
            color: #666;
        }

        /* Card-like containers */
        .ui-card {
            background: #ffffff;
            border: 1px solid #e8e4f0;
            border-radius: 12px;
            padding: 1.5rem;
            margin-bottom: 1rem;
            box-shadow: 0 1px 4px rgba(124, 92, 252, 0.06);
        }

        /* Metric cards row */
        .metric-card {
            background: linear-gradient(135deg, #F0ECF9 0%, #ffffff 100%);
            border: 1px solid #e0d8f0;
            border-radius: 12px;
            padding: 1.2rem 1rem;
            text-align: center;
        }
        .metric-card .metric-value {
            font-size: 2rem;
            font-weight: 700;
            color: #7C5CFC;
            line-height: 1.2;
        }
        .metric-card .metric-label {
            font-size: 0.85rem;
            color: #666;
            margin-top: 0.3rem;
        }

        /* Step indicator */
        .step-indicator {
            display: flex;
            align-items: center;
            gap: 0.5rem;
            margin-bottom: 0.8rem;
        }
        .step-badge {
            background: #7C5CFC;
            color: white;
            border-radius: 50%;
            width: 28px;
            height: 28px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 0.85rem;
            font-weight: 600;
            flex-shrink: 0;
        }
        .step-badge.done {
            background: #4CAF50;
        }
        .step-badge.pending {
            background: #ccc;
        }
        .step-title {
            font-size: 1rem;
            font-weight: 600;
            color: #1E1E2F;
        }

        /* Client card */
        .client-card {
            background: #ffffff;
            border: 1px solid #e8e4f0;
            border-radius: 10px;
            padding: 1rem 1.2rem;
            margin-bottom: 0.75rem;
            transition: box-shadow 0.2s;
        }
        .client-card:hover {
            box-shadow: 0 2px 8px rgba(124, 92, 252, 0.12);
        }
        .client-card .client-name {
            font-size: 1.05rem;
            font-weight: 600;
            color: #1E1E2F;
        }
        .client-card .client-meta {
            font-size: 0.82rem;
            color: #888;
            margin-top: 0.2rem;
        }
        .client-card .client-notes {
            font-size: 0.88rem;
            color: #555;
            margin-top: 0.4rem;
            font-style: italic;
        }

        /* Session summary field styling */
        .field-tag {
            display: inline-block;
            background: #F0ECF9;
            color: #5a3fc7;
            border-radius: 6px;
            padding: 0.15rem 0.6rem;
            font-size: 0.8rem;
            font-weight: 600;
            margin-bottom: 0.4rem;
        }

        /* Welcome hero */
        .hero-section {
            text-align: center;
            padding: 2rem 1rem 1.5rem 1rem;
        }
        .hero-section h1 {
            font-size: 2.2rem;
            color: #1E1E2F;
            margin-bottom: 0.3rem;
        }
        .hero-section p {
            font-size: 1.1rem;
            color: #666;
            max-width: 550px;
            margin: 0 auto;
        }

        /* Feature cards on home page */
        .feature-card {
            background: #ffffff;
            border: 1px solid #e8e4f0;
            border-radius: 12px;
            padding: 1.5rem;
            text-align: center;
            height: 100%;
            transition: transform 0.2s, box-shadow 0.2s;
        }
        .feature-card:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(124, 92, 252, 0.1);
        }
        .feature-card .feature-icon {
            font-size: 2.2rem;
            margin-bottom: 0.5rem;
        }
        .feature-card h3 {
            font-size: 1.05rem;
            color: #1E1E2F;
            margin: 0.3rem 0;
        }
        .feature-card p {
            font-size: 0.88rem;
            color: #666;
            margin: 0;
        }

        /* Emotional state badge */
        .emotion-badge {
            display: inline-block;
            background: linear-gradient(135deg, #F0ECF9, #e8dff5);
            color: #5a3fc7;
            border-radius: 20px;
            padding: 0.35rem 1rem;
            font-size: 0.92rem;
            font-weight: 500;
        }

        /* Better expander headers */
        .streamlit-expanderHeader {
            font-weight: 600 !important;
        }

        /* Divider color */
        hr {
            border-color: #e8e4f0 !important;
        }

        /* Page subtitle */
        .page-subtitle {
            font-size: 1rem;
            color: #888;
            margin-top: -0.8rem;
            margin-bottom: 1.5rem;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_sidebar_brand() -> None:
    """Render branded sidebar header."""
    with st.sidebar:
        st.markdown(
            """
            <div class="sidebar-brand">
                <h2>🎙️ Coach Notes</h2>
                <p>Tu asistente de coaching</p>
            </div>
            """,
            unsafe_allow_html=True,
        )


def step_indicator(number: int, title: str, done: bool = False) -> None:
    """Render a step indicator with number badge and title."""
    badge_class = "done" if done else ""
    check = "✓" if done else str(number)
    st.markdown(
        f"""
        <div class="step-indicator">
            <div class="step-badge {badge_class}">{check}</div>
            <span class="step-title">{title}</span>
        </div>
        """,
        unsafe_allow_html=True,
    )


def metric_card(value: str, label: str) -> None:
    """Render a styled metric card."""
    st.markdown(
        f"""
        <div class="metric-card">
            <div class="metric-value">{value}</div>
            <div class="metric-label">{label}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def page_header(title: str, subtitle: str = "") -> None:
    """Render a page title with optional subtitle."""
    st.title(title)
    if subtitle:
        st.markdown(f'<p class="page-subtitle">{subtitle}</p>', unsafe_allow_html=True)
