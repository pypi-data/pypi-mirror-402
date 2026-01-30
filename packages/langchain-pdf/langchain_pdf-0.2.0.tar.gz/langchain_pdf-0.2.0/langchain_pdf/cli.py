"""
cli.py
------

Command Line Interface for langchain-pdf.

Provides a simple way to generate PDFs from:
- text files
- AI-generated content (via LangChain)
"""

import argparse
import sys
from pathlib import Path

from dotenv import load_dotenv

from langchain_pdf.exporter import export_pdf


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="langchain-pdf",
        description="Generate clean, readable PDFs from text or AI output."
    )

    # Input modes
    parser.add_argument(
        "input",
        nargs="?",
        help="Path to input text file"
    )

    parser.add_argument(
        "output",
        nargs="?",
        help="Path to output PDF file"
    )

    parser.add_argument(
        "--topic",
        help="Generate content using LangChain for the given topic"
    )

    parser.add_argument(
        "--out",
        help="Output PDF file (used with --topic)"
    )

    parser.add_argument(
        "--title",
        help="Optional document title"
    )

    return parser


def main() -> None:
    load_dotenv()  # load .env if present

    parser = build_parser()
    args = parser.parse_args()

    # -------- Mode 1: File → PDF --------
    if args.input and args.output:
        input_path = Path(args.input)
        output_path = Path(args.output)

        if not input_path.exists():
            print(f"❌ Input file not found: {input_path}")
            sys.exit(1)

        text = input_path.read_text(encoding="utf-8")

        export_pdf(
            text=text,
            output_path=output_path,
            title=args.title
        )

        print(f"✅ PDF generated: {output_path}")
        return

    # -------- Mode 2: Topic → AI → PDF --------
    if args.topic and args.out:
        from langchain_pdf.llm_factory import get_llm # lazy import
        from langchain_core.prompts import PromptTemplate

        PROMPT = """
                You are an expert technical educator.

                Write a structured, professional document on the topic below.

                Rules:
                - Use clear section headings
                - Use bullet points where appropriate
                - Avoid emojis
                - Avoid code blocks
                - Avoid markdown formatting symbols

                Topic:
                {topic}
                """

        llm = get_llm()

        prompt = PromptTemplate(
            input_variables=["topic"],
            template=PROMPT
        )

        chain = prompt | llm
        response = chain.invoke({"topic": args.topic})

        export_pdf(
            text=response.content,
            output_path=args.out,
            title=args.title or args.topic
        )

        print(f"✅ PDF generated: {args.out}")
        return

    # -------- Invalid usage --------
    parser.print_help()
    sys.exit(1)


if __name__ == "__main__":
    main()
