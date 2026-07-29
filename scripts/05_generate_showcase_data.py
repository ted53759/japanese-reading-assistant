"""Generate verified static showcase data with the project's original pipeline.

This script downloads public-domain texts from Aozora Bunko, extracts the first
20 sentences, and processes them through scripts/03_run_api.py.  The resulting
JSON is used only by the static portfolio showcase; it contains no API key.

Run from the repository root:
    .venv\\Scripts\\python scripts\\05_generate_showcase_data.py
"""

from __future__ import annotations

import importlib.util
import json
import re
import sys
import time
import urllib.request
from pathlib import Path

from bs4 import BeautifulSoup


ROOT = Path(__file__).resolve().parents[1]
OUTPUT_PATH = ROOT / "showcase" / "data" / "generated-results.json"

STORIES = (
    {
        "id": "rashomon",
        "title": "羅生門",
        "author": "芥川龍之介",
        "source": "https://www.aozora.gr.jp/cards/000879/files/127_15260.html",
        "source_label": "青空文庫｜羅生門",
        "remove_heading": False,
    },
    {
        "id": "yumejuya",
        "title": "夢十夜・第一夜",
        "author": "夏目漱石",
        "source": "https://www.aozora.gr.jp/cards/000148/files/799_14972.html",
        "source_label": "青空文庫｜夢十夜",
        "remove_heading": True,
    },
    {
        "id": "restaurant",
        "title": "注文の多い料理店",
        "author": "宮沢賢治",
        "source": "https://www.aozora.gr.jp/cards/000081/files/43754_17659.html",
        "source_label": "青空文庫｜注文の多い料理店",
        "remove_heading": False,
    },
)


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Could not load {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def fetch_main_text(url: str) -> str:
    request = urllib.request.Request(url, headers={"User-Agent": "JapaneseReadingAssistant/1.0"})
    with urllib.request.urlopen(request, timeout=30) as response:
        html = response.read().decode("shift_jis", errors="replace")

    soup = BeautifulSoup(html, "html.parser")
    main = soup.find("div", class_="main_text")
    if main is None:
        raise RuntimeError(f"Could not find main text in {url}")
    for tag in main.find_all(["rt", "rp"]):
        tag.decompose()
    text = main.get_text("")
    text = re.sub(r"［＃.*?］", "", text)
    return re.sub(r"\n[ \t]*\n+", "\n", text).strip()


def first_twenty_sentences(text: str, remove_heading: bool, server_module) -> list[str]:
    if remove_heading:
        text = re.sub(r"^第一夜\s*", "", text)
    prepared = server_module.splitter.preprocess_text(text)
    sentences = server_module.splitter.extract_sentences(prepared)
    if len(sentences) < 20:
        raise RuntimeError(f"Expected at least 20 sentences, got {len(sentences)}")
    return sentences[:20]


def process_story(story: dict, api_module, server_module) -> dict:
    sentences = first_twenty_sentences(
        fetch_main_text(story["source"]), story["remove_heading"], server_module
    )
    numbered = server_module.number_sentences(sentences, 1)
    started = time.perf_counter()

    raw_result = api_module.translate_block(1, "1-20", numbered, 1)
    processed = api_module.postprocess_result(raw_result)
    elapsed_seconds = round(time.perf_counter() - started, 1)
    serialized = server_module.serialize_result(api_module, processed)

    formatted_by_count: dict[str, str] = {}
    quality_by_count: dict[str, dict] = {}
    for count in (3, 5, 10, 20):
        partial = serialized[:count]
        formatted = server_module.format_result(partial)
        warnings, critical = api_module.validate_result(1, f"1-{count}", formatted)
        if critical:
            raise RuntimeError(
                f"Pipeline QA failed for {story['title']} ({count} sentences): {critical}"
            )
        formatted_by_count[str(count)] = formatted
        quality_by_count[str(count)] = {
            "passed": count,
            "warnings": warnings,
            "critical": critical,
        }

    return {
        "id": story["id"],
        "title": story["title"],
        "author": story["author"],
        "source": story["source"],
        "sourceLabel": story["source_label"],
        "totalSentences": len(sentences),
        "preview": sentences,
        "sentences": serialized,
        "formattedByCount": formatted_by_count,
        "qualityByCount": quality_by_count,
        "elapsedSeconds": elapsed_seconds,
    }


def main() -> None:
    server_module = load_module("showcase_server", ROOT / "web" / "server.py")
    api_module = load_module("showcase_api", ROOT / "scripts" / "03_run_api.py")
    results = []

    for story in STORIES:
        print(f"Processing story: {story['id']}")
        results.append(process_story(story, api_module, server_module))

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "generatedWith": {
            "pipeline": "scripts/03_run_api.py",
            "model": api_module.MODEL,
            "source": "公開作品節錄，依原始 pipeline 預先處理",
        },
        "stories": results,
    }
    OUTPUT_PATH.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(f"Wrote verified showcase data to {OUTPUT_PATH.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
