import argparse
import shutil
import zipfile
from pathlib import Path
from tempfile import mkdtemp
from urllib.parse import unquote

from bs4 import BeautifulSoup


# =========================
# 清理 ruby / furigana
# =========================

def clean_ruby_and_extract_text(soup: BeautifulSoup) -> str:
    """
    Remove ruby annotations and extract readable text from HTML/XHTML.
    """

    # 移除振假名內容，例如 <rt>かのじょ</rt>
    for rt in soup.find_all("rt"):
        rt.decompose()

    # 保留本體文字，移除 ruby / rb 標籤本身
    for tag_name in ["ruby", "rb"]:
        for tag in soup.find_all(tag_name):
            tag.unwrap()

    return soup.get_text()


# =========================
# 找 OPF 路徑
# =========================

def find_opf_path(temp_dir: Path) -> Path:
    """
    Find the OPF file path from META-INF/container.xml.
    """

    container_path = temp_dir / "META-INF" / "container.xml"

    if not container_path.exists():
        raise FileNotFoundError(f"container.xml not found: {container_path}")

    with container_path.open("rb") as f:
        soup = BeautifulSoup(f.read(), "xml")

    rootfile = soup.find("rootfile")

    if rootfile is None or not rootfile.get("full-path"):
        raise ValueError("Cannot find rootfile full-path in container.xml")

    return temp_dir / rootfile["full-path"]


# =========================
# EPUB → TXT
# =========================

def extract_text_from_epub(epub_path: Path, txt_output_path: Path) -> None:
    """
    Extract text from an EPUB file according to OPF spine order.
    Ruby/furigana annotations are removed.
    """

    if not epub_path.exists():
        raise FileNotFoundError(f"EPUB file not found: {epub_path}")

    temp_dir = Path(mkdtemp(prefix="epub_extract_"))

    try:
        with zipfile.ZipFile(epub_path, "r") as zip_ref:
            zip_ref.extractall(temp_dir)

        opf_path = find_opf_path(temp_dir)
        opf_dir = opf_path.parent

        with opf_path.open("rb") as f:
            opf_soup = BeautifulSoup(f.read(), "xml")

        # manifest: id -> href
        manifest = {}

        for item in opf_soup.find_all("item"):
            item_id = item.get("id")
            href = item.get("href")

            if item_id and href:
                manifest[item_id] = href

        full_text = []

        # 依照 spine 順序讀取章節
        for itemref in opf_soup.find_all("itemref"):
            idref = itemref.get("idref")
            href = manifest.get(idref)

            if not href:
                continue

            file_path = opf_dir / unquote(href)
            file_path = file_path.resolve()

            if not str(file_path).lower().endswith((".xhtml", ".html", ".htm")):
                continue

            if not file_path.exists():
                continue

            with file_path.open("rb") as f:
                soup = BeautifulSoup(f.read(), "lxml")

            text = clean_ruby_and_extract_text(soup).strip()

            if text:
                full_text.append(text)

        txt_output_path.parent.mkdir(parents=True, exist_ok=True)
        txt_output_path.write_text("\n\n".join(full_text), encoding="utf-8")

        print("EPUB 文字抽取完成！")
        print(f"輸入 EPUB：{epub_path}")
        print(f"輸出 TXT：{txt_output_path}")

    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


# =========================
# 命令列介面
# =========================

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Extract clean Japanese text from EPUB and remove ruby/furigana annotations."
    )

    parser.add_argument(
        "input_epub",
        type=str,
        help="Path to input EPUB file",
    )

    parser.add_argument(
        "output_txt",
        type=str,
        help="Path to output TXT file",
    )

    args = parser.parse_args()

    extract_text_from_epub(
        epub_path=Path(args.input_epub),
        txt_output_path=Path(args.output_txt),
    )


if __name__ == "__main__":
    main()