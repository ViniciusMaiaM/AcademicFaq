import streamlit as st


def load_custom_css():

    st.markdown(
        """
    <style>
        .main-header {
            text-align: center;
            padding: 1rem 0;
            background: linear-gradient(90deg, #1f4e79 0%, #2d5aa0 100%);
            color: white;
            border-radius: 10px;
            margin-bottom: 2rem;
        }
        .example-question {
            background-color: #21507e;
            padding: 0.5rem;
            border-radius: 5px;
            margin: 0.2rem 0;
            cursor: pointer;
            border-left: 3px solid #1f4e79;
        }
        .example-question:hover {
            background-color: #21507e;
        }
        .source-card {
            background-color: #21507e;
            padding: 1rem;
            border-radius: 8px;
            border-left: 4px solid #1f4e79;
            margin: 0.5rem 0;
        }
        .stats-card {
            background-color: #21507e;
            padding: 1rem;
            border-radius: 8px;
            text-align: center;
        }
        .cached-badge {
            background-color: #21507e;
            color: white;
            padding: 0.2rem 0.5rem;
            border-radius: 12px;
            font-size: 0.8rem;
            margin-left: 0.5rem;
        }
        .response-time {
            color: #666;
            font-size: 0.8rem;
            font-style: italic;
        }
    </style>
    """,
        unsafe_allow_html=True,
    )
