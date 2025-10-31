"""
Streamlit web interface for the abstractive text summarizer.

Provides an alternative interactive UI with sidebar controls and
real-time parameter adjustment.
"""

import streamlit as st

from app.summarizer_app import CFG, TextSummarizer, extract_text_from_file


def initialize_session_state():
    """Initialize Streamlit session state variables."""
    if "summarizer" not in st.session_state:
        st.session_state.summarizer = TextSummarizer(CFG.default_model)
        st.session_state.current_model = CFG.default_model


def main():
    """Main Streamlit application."""
    st.set_page_config(
        page_title="Text Summarizer",
        page_icon="📝",
        layout="wide",
    )

    st.title("📝 Abstractive Text Summarizer")
    st.markdown(
        "Summarize long texts using Hugging Face Transformers. "
        "Supports pasted text or .txt/.pdf file uploads."
    )

    initialize_session_state()

    # Sidebar controls
    with st.sidebar:
        st.header("⚙️ Configuration")

        model_name = st.selectbox(
            "Select Model",
            options=CFG.available_models,
            index=CFG.available_models.index(CFG.default_model),
            help="Choose a summarization model. FLAN-T5-small is fastest on CPU.",
        )

        # Load model if changed
        if model_name != st.session_state.current_model:
            with st.spinner(f"Loading {model_name}..."):
                st.session_state.summarizer = TextSummarizer(model_name)
                st.session_state.current_model = model_name
            st.success(f"✓ Model loaded: {model_name}")

        st.markdown("---")
        st.subheader("Generation Parameters")

        max_length = st.slider(
            "Max Summary Length (tokens)",
            min_value=50,
            max_value=500,
            value=150,
            step=10,
            help="Maximum length of generated summary.",
        )

        min_length = st.slider(
            "Min Summary Length (tokens)",
            min_value=10,
            max_value=200,
            value=30,
            step=5,
            help="Minimum length of generated summary.",
        )

        num_beams = st.slider(
            "Beam Search Beams",
            min_value=1,
            max_value=8,
            value=4,
            step=1,
            help="Number of beams for beam search. Higher = better quality, slower.",
        )

        do_sample = st.checkbox(
            "Use Sampling (vs Beam Search)",
            value=False,
            help="Enable sampling for more diverse outputs.",
        )

        temperature = st.slider(
            "Temperature (sampling only)",
            min_value=0.1,
            max_value=2.0,
            value=1.0,
            step=0.1,
            help="Higher = more random. Only used if sampling is enabled.",
        )

        top_p = st.slider(
            "Top-p (nucleus sampling)",
            min_value=0.0,
            max_value=1.0,
            value=0.95,
            step=0.05,
            help="Nucleus sampling parameter. Only used if sampling is enabled.",
        )

    # Main content area
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("📥 Input")

        input_method = st.radio(
            "Choose input method:",
            options=["Paste Text", "Upload File"],
            horizontal=True,
        )

        if input_method == "Paste Text":
            text_input = st.text_area(
                "Enter text to summarize:",
                height=300,
                placeholder="Paste your text here...",
            )
        else:
            uploaded_file = st.file_uploader(
                "Upload .txt or .pdf file:",
                type=["txt", "pdf"],
            )
            if uploaded_file is not None:
                try:
                    text_input = extract_text_from_file(uploaded_file.name)
                    st.success(f"✓ Extracted {len(text_input)} characters from file")
                except Exception as e:
                    st.error(f"Error extracting file: {str(e)}")
                    text_input = ""
            else:
                text_input = ""

    with col2:
        st.subheader("📤 Output")

        if st.button("🚀 Summarize", use_container_width=True):
            if not text_input.strip():
                st.warning("Please enter text or upload a file.")
            else:
                try:
                    with st.spinner("Summarizing..."):
                        summary = st.session_state.summarizer.summarize(
                            text_input,
                            max_length=max_length,
                            min_length=min_length,
                            num_beams=num_beams,
                            temperature=temperature,
                            top_p=top_p,
                            do_sample=do_sample,
                        )
                    st.success("✓ Summarization complete!")
                    st.text_area(
                        "Summary:",
                        value=summary,
                        height=300,
                        disabled=True,
                    )

                    # Display statistics
                    st.markdown("---")
                    col_stats1, col_stats2, col_stats3 = st.columns(3)
                    with col_stats1:
                        st.metric("Input Length", f"{len(text_input)} chars")
                    with col_stats2:
                        st.metric("Summary Length", f"{len(summary)} chars")
                    with col_stats3:
                        ratio = len(summary) / len(text_input) if text_input else 0
                        st.metric("Compression Ratio", f"{ratio:.1%}")

                except Exception as e:
                    st.error(f"Error during summarization: {str(e)}")


if __name__ == "__main__":
    main()

