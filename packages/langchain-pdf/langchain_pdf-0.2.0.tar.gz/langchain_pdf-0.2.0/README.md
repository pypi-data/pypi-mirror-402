# langchain-pdf

Generate clean, readable, professional PDFs from raw text or Large Language Model (LLM) output.

`langchain-pdf` is designed for developers who want **deterministic, well-formatted documents** instead of messy markdown or broken PDFs.

---
![GitHub stars](https://img.shields.io/github/stars/DevDoshi19/langchain-pdf?style=flat-square)
![License](https://img.shields.io/github/license/DevDoshi19/langchain-pdf?style=flat-square)
![Python](https://img.shields.io/badge/python-3.9%2B-blue?style=flat-square)
![Status](https://img.shields.io/badge/status-active-success?style=flat-square)

## ✨ Why langchain-pdf?

Large Language Models often generate:
- markdown artifacts (`**bold**`, `---`, `1.` lists)
- inconsistent spacing
- duplicated headings
- orphan bullets
- blank pages in PDFs

**langchain-pdf fixes all of that.**

It introduces a proper document pipeline:

```

LLM Output → Normalize → Parse → Render → PDF

````

---

## 🚀 Features

- 🧠 Robust text normalization (handles messy LLM output)
- 📚 Structured document parsing (headings, paragraphs, bullets)
- 🖨️ Professional PDF rendering
- 🛑 No blank pages or orphan content
- 🔗 LangChain integration (Gemini ,OpenAI , Anthropic supported)
- 💻 CLI support (no Python code required)
- 🧪 Windows-tested (PowerShell friendly)
- 📦 Open-source & extensible

---
## 📄 Sample Outputs

Want to see what the generated PDFs look like?

👉 Check out the sample outputs here:  
[`docs/outputs/`](https://github.com/DevDoshi19/langchain-pdf/tree/main/doc/output)

## 📦 Installation

### Clone the repository

```bash
git clone https://github.com/your-username/langchain-pdf.git
cd langchain-pdf
````

### Create and activate a virtual environment

```bash
python -m venv venv
```

**Windows**

```powershell
venv\Scripts\activate
```

**macOS / Linux**

```bash
source venv/bin/activate
```

### Install dependencies

```bash
pip install -r requirements.txt
pip install -e .
```

---

Set ONE of the following environment variables:

- `OPENAI_API_KEY` (OpenAI)
- `GOOGLE_API_KEY` or `GEMINI_API_KEY` (Google Gemini)
- `ANTHROPIC_API_KEY` (Anthropic)

## 🔐 Environment Setup (for AI generation)

Create a `.env` file in the project root:

```env
GOOGLE_API_KEY=your_gemini_api_key_here
OPENAI_API_KEY=your_gemini_api_key_here
ANTHROPIC_API_KEY=your_gemini_api_key_here
```
### Optional LLM Providers

OpenAI:
```bash
pip install langchain-openai
```

Google Gemini:
```bash
pip install langchain-google-genai
```

Anthropic:
```bash
pip install langchain-anthropic
```

> `.env` is ignored by Git and should never be committed.

---

## 🖥️ CLI Usage

### 1️⃣ Convert a text file to PDF

```bash
python -m langchain_pdf.cli input.txt output.pdf
```

Optional title:

```bash
python -m langchain_pdf.cli input.txt output.pdf --title "My Document"
```

---

### 2️⃣ Generate a PDF using LangChain (Gemini)

```bash
python -m langchain_pdf.cli \
  --topic "Generative AI with LangChain" \
  --out reports/course.pdf
```

This will:

* generate content using Gemini
* normalize messy output
* create a clean PDF automatically

---

### 3️⃣ Help

```bash
python -m langchain_pdf.cli --help
```

---

## 🧠 How It Works (Architecture)

```
┌──────────────┐
│  LLM / Text  │
└──────┬───────┘
       ↓
┌──────────────┐
│ Normalizer   │  ← removes markdown, noise, duplicates
└──────┬───────┘
       ↓
┌──────────────┐
│ Parser       │  ← converts text → document blocks
└──────┬───────┘
       ↓
┌──────────────┐
│ Renderer     │  ← layout-safe PDF rendering
└──────┬───────┘
       ↓
┌──────────────┐
│   PDF File   │
└──────────────┘
```

---

## 📁 Project Structure

```
docs/
├── outputs/
│   ├── course_overview_sample.pdf
│   ├── resume_sample.pdf
│   └── README.md
langchain-pdf/
│
├── langchain_pdf/ # Core library
|   ├──assets/
|      ├──fonts/
|        ├── DejaVuSans.ttf
|        ├── DejaVuSans-Bold.ttf
|        ├── LICENSE.txt
│   ├── __init__.py
│   ├── exporter.py
│   ├── normalizer.py
│   ├── parser.py
│   ├── renderer.py
│   ├── templates.py
│   └── cli.py
│
├── examples/             # Usage examples (not packaged)
│   ├── llm_factory.py
│   └── langchain_example.py
│
├── tests/                # Tests (optional)
│
├── README.md
├── requirements.txt
├── pyproject.toml
└── .env.example
```

---

## 🧪 Example Use Cases

* Generate course PDFs from LLMs
* Convert AI-generated reports into readable documents
* Create resumes, study material, or technical notes
* Build SaaS features that export PDFs
* Automate documentation pipelines

---

## 🤔 Is this made with AI?

Yes — **and engineered by a human.**

AI helps generate content.
`langchain-pdf` ensures that content is **structured, readable, and professional**.

The value is not generation — it’s **control**.

---

## 🛠️ Extending the Project

Planned / easy extensions:

* Support for local LLMs (Ollama)
* Batch PDF generation
* Themes (fonts, spacing)
* DOCX export
* Stream / stdin input

---

## 🤝 Contributing

Contributions are welcome.

If you:

* improve normalization
* add render themes
* support new LLMs

feel free to open a PR.

---

## 📜 License

MIT License — free to use, modify, and distribute.

---

## ⭐ Final Note

If you are tired of broken PDFs from AI output,
**langchain-pdf is built for you.**

## 🔤 Fonts & Attribution

This project bundles the **Inter** font for consistent, readable PDF output.

Inter is licensed under the **SIL Open Font License (OFL 1.1)**  
Font copyright © The Inter Project Authors.

The font license is included in:
`langchain_pdf/assets/fonts/LICENSE.txt`



