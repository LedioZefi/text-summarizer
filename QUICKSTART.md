# Quick Start Guide

## 1. Setup (One-time)

```bash
# Create virtual environment
python3.10 -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

## 2. Run Gradio Interface (Recommended)

```bash
python -m app.ui_gradio
```

Then open: **http://127.0.0.1:7860**

## 3. Or Run Streamlit Interface

```bash
streamlit run app/ui_streamlit.py
```

Then open: **http://localhost:8501**

## 4. Test with Sample Text

1. Open the UI
2. Copy text from `examples/sample_text.txt`
3. Paste into the text area
4. Click **Summarize**

## Key Features

✅ **Default Model**: `google/flan-t5-small` (fast, CPU-friendly)  
✅ **Alternative Models**: BART, T5 (higher quality, slower)  
✅ **File Support**: Upload .txt or .pdf files  
✅ **Long Text**: Automatic chunking with overlap  
✅ **Tunable**: Adjust beam search, sampling, temperature  

## Configuration

Edit `models/model_config.json` to:
- Change default model
- Adjust chunk size
- Set device (cpu/cuda)
- Modify generation parameters

## Programmatic Usage

```python
from app.summarizer_app import TextSummarizer

summarizer = TextSummarizer("google/flan-t5-small")
summary = summarizer.summarize("Your long text here...")
print(summary)
```

## Troubleshooting

**Model download fails?**
```bash
python -c "from transformers import AutoTokenizer; \
AutoTokenizer.from_pretrained('google/flan-t5-small')"
```

**Out of memory?**
- Use `google/flan-t5-small` (smallest)
- Reduce `chunk_tokens` in config
- Reduce `max_length` in UI

**PDF extraction fails?**
```bash
pip install pymupdf pdfplumber
```

## Next Steps

- Read full README.md for detailed documentation
- Explore different models in the UI
- Adjust generation parameters for your use case
- Fine-tune on custom data (future enhancement)

---

**Happy summarizing! 🚀**

