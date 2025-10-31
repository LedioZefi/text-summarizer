# Text Summarizer

Ever had a long article, research paper, or document you needed to understand quickly? This tool does exactly that — it reads your text and creates a concise summary in seconds. No GPU needed, runs smoothly on your laptop.

## What It Does

- **Summarizes text** — Paste any text or upload a file (.txt or .pdf), get a summary back
- **Works offline** — Runs on CPU, no cloud dependency
- **Multiple models** — Choose between fast (FLAN-T5-small) or high-quality (BART) summaries
- **Two interfaces** — Use Gradio (web-based) or Streamlit (dashboard-style), whatever you prefer
- **Handles long documents** — Automatically breaks up long texts and summarizes them intelligently
- **Customizable** — Adjust summary length, quality, and generation style to your needs

## Getting Started (5 minutes)

### 1. Clone & Setup

```bash
git clone https://github.com/LedioZefi/text-summarizer.git
cd text-summarizer
python3 -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Run It

**Option A: Gradio (recommended for first-time users)**
```bash
python -m app.ui_gradio
```
Opens at `http://127.0.0.1:7860` — just paste text or upload a file and click Summarize.

**Option B: Streamlit (dashboard-style interface)**
```bash
streamlit run app/ui_streamlit.py
```
Opens at `http://localhost:8501` — similar functionality, different layout.

### 3. Test It

Copy the sample text from `examples/sample_text.txt`, paste it into the UI, and hit Summarize. You should get a summary in a few seconds.

## How to Use

### In the Web Interface

1. **Pick a model** — The default (FLAN-T5-small) is fast. If you want better quality, try BART.
2. **Add your text** — Paste it directly or upload a .txt/.pdf file
3. **Tweak settings (optional)** — Adjust summary length, quality, etc. Most people just use defaults.
4. **Click Summarize** — Wait a few seconds, get your summary

### In Your Code

```python
from app.summarizer_app import TextSummarizer

summarizer = TextSummarizer()  # Uses default model
summary = summarizer.summarize("Your long text here...")
print(summary)
```

Want to use a different model or adjust quality?

```python
summarizer = TextSummarizer("facebook/bart-large-cnn")  # Higher quality
summary = summarizer.summarize(
    "Your text...",
    max_length=150,      # Longer summaries
    num_beams=4,         # Better quality (slower)
)
```

## Models: Speed vs Quality

| Model | Speed | Quality | Memory | When to Use |
|-------|-------|---------|--------|------------|
| FLAN-T5-small | ⚡⚡⚡ Fast | ⭐⭐⭐ Good | 🟢 Low | Testing, quick summaries |
| T5-base | ⚡⚡ Medium | ⭐⭐⭐⭐ Better | 🟡 Medium | Balanced choice |
| BART-large-cnn | ⚡ Slow | ⭐⭐⭐⭐⭐ Best | 🔴 High | When quality matters most |

## Customization

Want to tweak how it works? Edit `models/model_config.json`:

```json
{
  "default_model": "google/flan-t5-small",
  "available_models": ["google/flan-t5-small", "facebook/bart-large-cnn", "google-t5/t5-base"],
  "device": "cpu",
  "max_input_chars": 200000,
  "chunk_tokens": 880,
  "stride_tokens": 80,
  "target_sentences_per_chunk": [1, 3]
}
```

**What each setting does:**
- `default_model` — Which model loads when you start the app
- `device` — Use "cpu" or "cuda" (if you have a GPU)
- `max_input_chars` — Reject inputs longer than this
- `chunk_tokens` — How many tokens to process at once (lower = less memory)
- `stride_tokens` — How much overlap between chunks (higher = better context)

## Tips & Tricks

- **First time?** Use FLAN-T5-small. It's fast and good enough for most things.
- **Need better summaries?** Switch to BART in the UI. It's slower but noticeably better.
- **Running out of memory?** Lower `chunk_tokens` in the config or use a smaller model.
- **Want different summaries each time?** Enable "sampling" in the UI for more variety.
- **Long documents?** The app automatically breaks them into chunks and summarizes each part.

## File Types

- **.txt** — Plain text (UTF-8 works best)
- **.pdf** — PDF documents (automatically extracted)

## Troubleshooting

**"It's slow"** — You're probably using BART. Try FLAN-T5-small for speed. Or just wait, it's worth it.

**"Out of memory"** — Use FLAN-T5-small, or lower `chunk_tokens` in the config.

**"PDF won't upload"** — Make sure it's a real PDF (not scanned images). If it still fails, try converting to text first.

**"Models won't download"** — Check your internet. Models download automatically on first use. If stuck, try:
```bash
python -c "from transformers import AutoTokenizer, AutoModelForSeq2SeqLM; \
AutoTokenizer.from_pretrained('google/flan-t5-small'); \
AutoModelForSeq2SeqLM.from_pretrained('google/flan-t5-small')"
```

## What's Next?

- Multi-language support
- Batch processing (summarize multiple files at once)
- Export to PDF/Word
- Fine-tuning on custom data
- API endpoint for integration

## Contributing

Found a bug? Have an idea? Open an issue or submit a PR. All contributions welcome.

## License

MIT — use it however you want.

---

**Built with Hugging Face Transformers, PyTorch, and a lot of coffee ☕**

