import os
import re
from pathlib import Path

# =========================
# 基本設定
# =========================

# 專案根目錄
BASE_DIR = Path(__file__).resolve().parent.parent

# 輸入檔案
INPUT_FILE = BASE_DIR / "sample" / "input_sample.txt"

# 輸出資料夾
OUTPUT_FOLDER = BASE_DIR / "sample" / "chunks"

# 每個 txt 放幾句
SENTENCES_PER_FILE = 8

# 起始編號
START_NUMBER = 1


# =========================
# 前處理
# =========================

def preprocess_text(text: str) -> str:
    """
    Normalize line breaks and separate adjacent Japanese dialogue quotes.
    """

    # 統一換行格式
    text = text.replace("\r\n", "\n").replace("\r", "\n")

    # 把過多空行壓成兩行
    text = re.sub(r"\n{3,}", "\n\n", text)

    # 避免兩句對話黏在一起，例如：
    # 「奈良の高校だよ」「奈良ですか？」
    # 變成：
    # 「奈良の高校だよ」
    # 「奈良ですか？」
    text = text.replace("」「", "」\n「")
    text = text.replace("』「", "』\n「")
    text = text.replace("」『", "」\n『")
    text = text.replace("』『", "』\n『")

    return text


# =========================
# 切句函式
# =========================

def split_japanese_sentences(paragraph: str) -> list[str]:
    """
    Split Japanese text by sentence-ending marks.

    The function keeps closing quotes together with the sentence.
    Example:
    です？」 will be treated as one sentence ending.
    """

    paragraph = paragraph.strip()

    if not paragraph:
        return []

    lines = [line.strip() for line in paragraph.split("\n") if line.strip()]

    results = []

    end_marks = "。！？!?"
    closing_quotes = "」』）】"

    for line in lines:
        buffer = ""
        i = 0

        while i < len(line):
            ch = line[i]
            buffer += ch

            if ch in end_marks:
                j = i + 1

                # 把句尾後面的閉引號一起放進來
                while j < len(line) and line[j] in closing_quotes:
                    buffer += line[j]
                    j += 1

                if buffer.strip():
                    results.append(buffer.strip())

                buffer = ""
                i = j
                continue

            i += 1

        # 剩下沒有句號的部分也保留
        if buffer.strip():
            results.append(buffer.strip())

    return results


# =========================
# 段落 → 句子
# =========================

def extract_sentences(text: str) -> list[str]:
    """
    Split cleaned text into paragraphs first, then split paragraphs into sentences.
    Short headings are preserved as independent items.
    """

    paragraphs = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]

    sentences = []

    for paragraph in paragraphs:
        paragraph = paragraph.strip()

        # 短標題直接保留，例如：
        # はじめに
        # 第一章
        if len(paragraph) < 30 and not re.search(r"[。！？!?]", paragraph):
            sentences.append(paragraph)
        else:
            sentences.extend(split_japanese_sentences(paragraph))

    return sentences


# =========================
# 輸出成多個 txt
# =========================

def write_chunks(
    sentences: list[str],
    output_folder: Path,
    sentences_per_file: int,
    start_number: int,
) -> int:
    """
    Write numbered sentences into multiple txt files.
    """

    output_folder.mkdir(parents=True, exist_ok=True)

    global_index = start_number
    file_index = 1

    for i in range(0, len(sentences), sentences_per_file):
        chunk = sentences[i:i + sentences_per_file]

        output_lines = []

        for sentence in chunk:
            output_lines.append(f"【{global_index}】")
            output_lines.append(sentence)
            output_lines.append("")
            global_index += 1

        output_path = output_folder / f"{file_index:03d}.txt"
        output_path.write_text("\n".join(output_lines), encoding="utf-8")

        file_index += 1

    return file_index - 1


# =========================
# 主程式
# =========================

def main() -> None:
    if not INPUT_FILE.exists():
        raise FileNotFoundError(f"Input file not found: {INPUT_FILE}")

    text = INPUT_FILE.read_text(encoding="utf-8")
    text = preprocess_text(text)

    sentences = extract_sentences(text)

    file_count = write_chunks(
        sentences=sentences,
        output_folder=OUTPUT_FOLDER,
        sentences_per_file=SENTENCES_PER_FILE,
        start_number=START_NUMBER,
    )

    print("切分完成！")
    print(f"總句數：{len(sentences)}")
    print(f"輸出檔案數：{file_count}")
    print(f"輸出資料夾：{OUTPUT_FOLDER}")


if __name__ == "__main__":
    main()