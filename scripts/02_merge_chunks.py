from pathlib import Path
import re

# =========================
# 基本設定
# =========================

# 專案根目錄
BASE_DIR = Path(__file__).resolve().parent.parent

# 輸入資料夾：由 split_paragraphs.py 產生
INPUT_FOLDER = BASE_DIR / "sample" / "chunks"

# 輸出檔案：合併後的 chunk 檔
OUTPUT_FILE = BASE_DIR / "sample" / "merged_chunks.txt"


# =========================
# 取得編號範圍
# =========================

def get_number_range(text: str) -> str:
    """
    Get the first and last sentence number in a chunk.

    Example:
    【1】
    ...
    【8】

    return: 1-8
    """

    numbers = re.findall(r"【(\d+)】", text)

    if not numbers:
        return "NO-NUM"

    return f"{numbers[0]}-{numbers[-1]}"


# =========================
# 合併 chunk 檔案
# =========================

def merge_chunk_files(input_folder: Path, output_file: Path) -> int:
    """
    Merge all txt files in the input folder into one file.

    Each file is wrapped with markers so that the source chunk can be traced.
    """

    if not input_folder.exists():
        raise FileNotFoundError(f"Input folder not found: {input_folder}")

    files = sorted(input_folder.glob("*.txt"))

    if not files:
        raise FileNotFoundError(f"No txt files found in: {input_folder}")

    output_lines = []

    for file in files:
        text = file.read_text(encoding="utf-8").strip()
        number_range = get_number_range(text)

        output_lines.append("")
        output_lines.append("")
        output_lines.append(f"<<<FILE {file.stem} | {number_range}>>>")
        output_lines.append("")
        output_lines.append(text)
        output_lines.append("")
        output_lines.append(f"<<<END FILE {file.stem}>>>")

    output_file.write_text("\n".join(output_lines).strip() + "\n", encoding="utf-8")

    return len(files)


# =========================
# 主程式
# =========================

def main() -> None:
    file_count = merge_chunk_files(
        input_folder=INPUT_FOLDER,
        output_file=OUTPUT_FILE,
    )

    print("合併完成！")
    print(f"合併檔案數：{file_count}")
    print(f"輸出檔案：{OUTPUT_FILE}")


if __name__ == "__main__":
    main()