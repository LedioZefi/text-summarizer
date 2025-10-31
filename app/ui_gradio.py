"""
Gradio web interface for the abstractive text summarizer.

Provides an interactive UI for text input, file upload, model selection,
and parameter tuning.
"""

import gradio as gr

from app.summarizer_app import CFG, TextSummarizer, extract_text_from_file


class SummarizerUI:
    """Gradio interface for text summarization."""

    def __init__(self):
        """Initialize the UI with default model."""
        self.summarizer = None
        self.current_model = CFG.default_model
        self._load_model(CFG.default_model)

    def _load_model(self, model_name: str) -> str:
        """
        Load a new model.

        Args:
            model_name: Hugging Face model identifier.

        Returns:
            Status message.
        """
        try:
            self.summarizer = TextSummarizer(model_name)
            self.current_model = model_name
            return f"✓ Model loaded: {model_name}"
        except Exception as e:
            return f"✗ Error loading model: {str(e)}"

    def _process_file(self, file) -> str:
        """
        Extract text from uploaded file.

        Args:
            file: Uploaded file object.

        Returns:
            Extracted text or error message.
        """
        if file is None:
            return ""
        try:
            text = extract_text_from_file(file.name)
            return text
        except Exception as e:
            return f"Error extracting file: {str(e)}"

    def summarize(
        self,
        text: str,
        model_name: str,
        max_length: int,
        min_length: int,
        num_beams: int,
        temperature: float,
        top_p: float,
        do_sample: bool,
    ) -> str:
        """
        Summarize input text with specified parameters.

        Args:
            text: Input text to summarize.
            model_name: Selected model name.
            max_length: Maximum summary length.
            min_length: Minimum summary length.
            num_beams: Number of beams for beam search.
            temperature: Sampling temperature.
            top_p: Nucleus sampling parameter.
            do_sample: Whether to use sampling.

        Returns:
            Generated summary or error message.
        """
        if not text.strip():
            return "Please enter text or upload a file."

        # Load model if changed
        if model_name != self.current_model:
            status = self._load_model(model_name)
            if "Error" in status:
                return status

        try:
            summary = self.summarizer.summarize(
                text,
                max_length=max_length,
                min_length=min_length,
                num_beams=num_beams,
                temperature=temperature,
                top_p=top_p,
                do_sample=do_sample,
            )
            return summary
        except Exception as e:
            return f"Error during summarization: {str(e)}"

    def build_interface(self) -> gr.Blocks:
        """
        Build the Gradio interface.

        Returns:
            Gradio Blocks interface.
        """
        with gr.Blocks(title="Text Summarizer") as demo:
            gr.Markdown("# 📝 Abstractive Text Summarizer")
            gr.Markdown(
                "Summarize long texts using Hugging Face Transformers. "
                "Supports pasted text or .txt/.pdf file uploads."
            )

            with gr.Row():
                with gr.Column(scale=1):
                    gr.Markdown("### Model Selection")
                    model_dropdown = gr.Dropdown(
                        choices=CFG.available_models,
                        value=CFG.default_model,
                        label="Model",
                        info="Select a summarization model",
                    )
                    model_status = gr.Textbox(
                        value=f"✓ Model loaded: {CFG.default_model}",
                        label="Status",
                        interactive=False,
                    )

                with gr.Column(scale=2):
                    gr.Markdown("### Input")
                    text_input = gr.Textbox(
                        label="Text to Summarize",
                        placeholder="Paste your text here...",
                        lines=10,
                    )
                    file_input = gr.File(
                        label="Or upload .txt/.pdf file",
                        file_types=[".txt", ".pdf"],
                    )

            with gr.Row():
                gr.Markdown("### Generation Parameters")

            with gr.Row():
                max_length = gr.Slider(
                    minimum=50,
                    maximum=500,
                    value=150,
                    step=10,
                    label="Max Summary Length (tokens)",
                )
                min_length = gr.Slider(
                    minimum=10,
                    maximum=200,
                    value=30,
                    step=5,
                    label="Min Summary Length (tokens)",
                )

            with gr.Row():
                num_beams = gr.Slider(
                    minimum=1,
                    maximum=8,
                    value=4,
                    step=1,
                    label="Beam Search Beams",
                )
                do_sample = gr.Checkbox(
                    value=False,
                    label="Use Sampling (vs Beam Search)",
                )

            with gr.Row():
                temperature = gr.Slider(
                    minimum=0.1,
                    maximum=2.0,
                    value=1.0,
                    step=0.1,
                    label="Temperature (sampling only)",
                )
                top_p = gr.Slider(
                    minimum=0.0,
                    maximum=1.0,
                    value=0.95,
                    step=0.05,
                    label="Top-p (nucleus sampling)",
                )

            with gr.Row():
                summarize_btn = gr.Button("🚀 Summarize", variant="primary")
                clear_btn = gr.Button("🔄 Clear")

            summary_output = gr.Textbox(
                label="Summary",
                lines=8,
                interactive=False,
            )

            # Event handlers
            file_input.change(
                fn=self._process_file,
                inputs=file_input,
                outputs=text_input,
            )

            model_dropdown.change(
                fn=self._load_model,
                inputs=model_dropdown,
                outputs=model_status,
            )

            summarize_btn.click(
                fn=self.summarize,
                inputs=[
                    text_input,
                    model_dropdown,
                    max_length,
                    min_length,
                    num_beams,
                    temperature,
                    top_p,
                    do_sample,
                ],
                outputs=summary_output,
            )

            clear_btn.click(
                fn=lambda: ("", ""),
                outputs=[text_input, summary_output],
            )

        return demo


def main():
    """Launch the Gradio interface."""
    ui = SummarizerUI()
    demo = ui.build_interface()
    demo.launch(share=False, server_name="127.0.0.1", server_port=7860)


if __name__ == "__main__":
    main()

