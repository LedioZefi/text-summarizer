"""
Abstractive Text Summarizer using Hugging Face Transformers.

This module provides core summarization functionality with support for:
- Multiple transformer models (FLAN-T5, BART, T5)
- Long-text chunking with sentence-aware splitting
- PDF and text file input
- Configurable generation parameters
"""

import json
import os
import re
from pathlib import Path
from typing import Optional, Tuple

import nltk
import torch
from transformers import AutoModelForSeq2SeqLM, AutoTokenizer

# Robust runtime check (handles clean venvs and CI)
for res, key in [("tokenizers/punkt", "punkt"),
                 ("tokenizers/punkt_tab/english", "punkt_tab")]:
    try:
        nltk.data.find(res)
    except LookupError:
        nltk.download(key, quiet=True)

# # Download required NLTK data for sentence tokenization
# try:
#     nltk.data.find("tokenizers/punkt")
# except LookupError:
#     nltk.download("punkt", quiet=True)
#     nltk.download("punkt_tab", quiet=True)



class SummarizerConfig:
    """Load and manage summarizer configuration."""

    def __init__(self, config_path: str = "models/model_config.json"):
        """
        Initialize configuration from JSON file.

        Args:
            config_path: Path to model_config.json relative to project root.
        """
        # Resolve path relative to project root
        if not os.path.isabs(config_path):
            project_root = Path(__file__).parent.parent
            config_path = project_root / config_path

        with open(config_path, "r") as f:
            cfg = json.load(f)

        self.default_model = cfg["default_model"]
        self.available_models = cfg["available_models"]
        self.device = cfg["device"]
        self.max_input_chars = cfg["max_input_chars"]
        self.chunk_tokens = cfg["chunk_tokens"]
        self.stride_tokens = cfg["stride_tokens"]
        self.target_sentences_per_chunk = cfg["target_sentences_per_chunk"]


CFG = SummarizerConfig()


class TextSummarizer:
    """Abstractive text summarizer using Hugging Face Transformers."""

    def __init__(self, model_name: str = CFG.default_model):
        """
        Initialize the summarizer with a specified model.

        Args:
            model_name: Hugging Face model identifier.

        Raises:
            ValueError: If model_name is not in available_models.
        """
        if model_name not in CFG.available_models:
            raise ValueError(
                f"Model {model_name} not in available models: {CFG.available_models}"
            )

        self.model_name = model_name
        self.device = CFG.device
        print(f"Loading model: {model_name} on device: {self.device}")

        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.model = AutoModelForSeq2SeqLM.from_pretrained(model_name)
        self.model.to(self.device)
        self.model.eval()

    def _clean_text(self, text: str) -> str:
        """
        Clean and normalize input text.

        Args:
            text: Raw input text.

        Returns:
            Cleaned text with normalized whitespace.
        """
        # Remove extra whitespace
        text = re.sub(r"\s+", " ", text)
        # Remove control characters
        text = "".join(ch for ch in text if ord(ch) >= 32 or ch in "\n\t")
        return text.strip()

    def _split_into_sentences(self, text: str) -> list[str]:
        """
        Split text into sentences using NLTK.

        Args:
            text: Input text.

        Returns:
            List of sentences.
        """
        sentences = nltk.sent_tokenize(text)
        return [s.strip() for s in sentences if s.strip()]

    def _chunk_text(self, text: str) -> list[str]:
        """
        Split long text into chunks with overlap for better context.

        Uses sentence-aware chunking to avoid breaking mid-sentence.

        Args:
            text: Input text to chunk.

        Returns:
            List of text chunks.
        """
        sentences = self._split_into_sentences(text)
        if not sentences:
            return []

        chunks = []
        current_chunk = []
        current_tokens = 0

        for sentence in sentences:
            sentence_tokens = len(self.tokenizer.encode(sentence))

            # If adding this sentence exceeds chunk limit, save current chunk
            if current_tokens + sentence_tokens > CFG.chunk_tokens and current_chunk:
                chunk_text = " ".join(current_chunk)
                chunks.append(chunk_text)

                # Implement stride: keep last few sentences for overlap
                stride_tokens = 0
                overlap_sentences = []
                for s in reversed(current_chunk):
                    s_tokens = len(self.tokenizer.encode(s))
                    if stride_tokens + s_tokens <= CFG.stride_tokens:
                        overlap_sentences.insert(0, s)
                        stride_tokens += s_tokens
                    else:
                        break

                current_chunk = overlap_sentences
                current_tokens = stride_tokens

            current_chunk.append(sentence)
            current_tokens += sentence_tokens

        # Add final chunk
        if current_chunk:
            chunks.append(" ".join(current_chunk))

        return chunks

    def _summarize_chunk(
        self,
        text: str,
        max_length: int = 150,
        min_length: int = 30,
        num_beams: int = 4,
        temperature: float = 1.0,
        top_p: float = 0.95,
        do_sample: bool = False,
    ) -> str:
        """
        Summarize a single text chunk.

        Args:
            text: Input text chunk.
            max_length: Maximum summary length in tokens.
            min_length: Minimum summary length in tokens.
            num_beams: Number of beams for beam search.
            temperature: Sampling temperature (only used if do_sample=True).
            top_p: Nucleus sampling parameter.
            do_sample: Whether to use sampling instead of beam search.

        Returns:
            Summary text.
        """
        inputs = self.tokenizer.encode(text, return_tensors="pt", max_length=1024, truncation=True)
        inputs = inputs.to(self.device)

        with torch.no_grad():
            summary_ids = self.model.generate(
                inputs,
                max_length=max_length,
                min_length=min_length,
                num_beams=num_beams,
                temperature=temperature,
                top_p=top_p,
                do_sample=do_sample,
                early_stopping=True,
            )

        summary = self.tokenizer.decode(summary_ids[0], skip_special_tokens=True)
        return summary

    def summarize(
        self,
        text: str,
        max_length: int = 150,
        min_length: int = 30,
        num_beams: int = 4,
        temperature: float = 1.0,
        top_p: float = 0.95,
        do_sample: bool = False,
    ) -> str:
        """
        Summarize input text, handling long texts via chunking.

        Args:
            text: Input text to summarize.
            max_length: Maximum summary length per chunk.
            min_length: Minimum summary length per chunk.
            num_beams: Number of beams for beam search.
            temperature: Sampling temperature.
            top_p: Nucleus sampling parameter.
            do_sample: Whether to use sampling.

        Returns:
            Final summary combining all chunks.

        Raises:
            ValueError: If text is empty or exceeds max_input_chars.
        """
        text = self._clean_text(text)

        if not text:
            raise ValueError("Input text is empty after cleaning.")

        if len(text) > CFG.max_input_chars:
            raise ValueError(
                f"Input text exceeds {CFG.max_input_chars} characters. "
                f"Got {len(text)} characters."
            )

        # For short texts, summarize directly
        if len(self.tokenizer.encode(text)) <= CFG.chunk_tokens:
            return self._summarize_chunk(
                text,
                max_length=max_length,
                min_length=min_length,
                num_beams=num_beams,
                temperature=temperature,
                top_p=top_p,
                do_sample=do_sample,
            )

        # For long texts, chunk and summarize each chunk
        chunks = self._chunk_text(text)
        chunk_summaries = []

        for i, chunk in enumerate(chunks):
            print(f"Summarizing chunk {i + 1}/{len(chunks)}...")
            summary = self._summarize_chunk(
                chunk,
                max_length=max_length,
                min_length=min_length,
                num_beams=num_beams,
                temperature=temperature,
                top_p=top_p,
                do_sample=do_sample,
            )
            chunk_summaries.append(summary)

        # Combine chunk summaries and summarize again
        combined = " ".join(chunk_summaries)
        final_summary = self._summarize_chunk(
            combined,
            max_length=max_length * 2,
            min_length=min_length,
            num_beams=num_beams,
            temperature=temperature,
            top_p=top_p,
            do_sample=do_sample,
        )

        return final_summary


def extract_text_from_file(file_path: str) -> str:
    """
    Extract text from .txt or .pdf files.

    Args:
        file_path: Path to input file.

    Returns:
        Extracted text.

    Raises:
        ValueError: If file format is not supported.
    """
    file_path = Path(file_path)

    if file_path.suffix.lower() == ".txt":
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()

    elif file_path.suffix.lower() == ".pdf":
        try:
            import fitz  # PyMuPDF

            doc = fitz.open(file_path)
            text = ""
            for page in doc:
                text += page.get_text()
            return text
        except ImportError:
            # Fallback to pdfplumber
            try:
                import pdfplumber

                with pdfplumber.open(file_path) as pdf:
                    text = ""
                    for page in pdf.pages:
                        text += page.extract_text() or ""
                    return text
            except ImportError:
                raise ImportError("Please install pymupdf or pdfplumber to process PDFs.")

    else:
        raise ValueError(f"Unsupported file format: {file_path.suffix}")

