import os
import re
import unicodedata
from pathlib import Path
from openai import OpenAI

# =========================
# 基本設定
# =========================

# 專案根目錄：japanese-reading-assistant/
BASE_DIR = Path(__file__).resolve().parent.parent

# 由 scripts/02_merge_chunks.py 產生的合併檔
MERGED_FILE = BASE_DIR / "sample" / "merged_chunks.txt"

# API 輸出資料夾
OUTPUT_DIR = BASE_DIR / "sample" / "api_outputs"

# 進度檔
PROGRESS_FILE = OUTPUT_DIR / "progress.txt"

# 警告輸出
WARNING_OUTPUT = OUTPUT_DIR / "warnings.txt"

# 處理 FILE 範圍
START_FILE = 1
END_FILE = 9999

# 使用模型
MODEL = os.getenv("OPENAI_MODEL", "gpt-5.4-mini")

# 逐字拆解括號對齊位置
ALIGN_TARGET_COL = 16

# API 最大重試次數
MAX_RETRIES = 3

client = OpenAI()

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


# =========================
# Prompt
# =========================

SYSTEM_PROMPT = """
你是日文逐字拆解助手。

請嚴格依照以下格式輸出：

【編號】

日文原句

單詞 （假名 / 中文）

單詞 （假名 / 中文）


中文翻譯：
中文翻譯內容


絕對規則：

1. 每個【編號】後面必須完整保留日文原句。
2. 不可以省略任何【編號】。
3. 不可以省略任何日文原句。
4. 每一句都必須有「中文翻譯：」。
5. 每一句都必須有逐字拆解。
6. 每個詞語獨立一行。
7. 每個詞語之間空一行。
8. 詞語格式固定為：
   單詞 （假名 / 中文）
9. 括號格式固定為：
   （假名 / 中文）
10. 不要拆解標點符號。
11. 不要輸出單獨的標點符號行。
12. 不可以把後半句原樣丟進逐字拆解區。
13. 逐字拆解區不能出現沒有括號的長日文句。
14. 中文解釋只能使用繁體中文、必要英文或數字。
15. 中文解釋中禁止混入其他外語文字，例如 Hindi、韓文、阿拉伯文、泰文、西里爾字母、喬治亞字母。
16. 不可以省略句尾表現，例如：
    んです
    なんです
    なんですよ
    ですよ
    ですね
    でしょう
    だろう
    じゃないですか
    じゃないですかね
    からね
    よね
17. 不要把助詞黏在前一個詞後面。
    例如：
    藤原君は 這種不可以。
    必須拆成：
    藤原君 （ふじわらくん / 藤原君）

    は （は / 主題標記）
18. 常見助詞請分開拆：
    は、が、を、に、の、と、で、も、から、まで、って、か、よ、ね
19. 遇到章節符號「＊」或「◇」時可輸出：
    ＊ （＊ / 章節標記）
    ◇ （◇ / 場景切換標記）
20. 如果原句本身只有標點符號，例如「!」「?」「?!」「「？」」，可以保留原句並給簡單中文翻譯，不需要硬拆成單詞。
21. 短反應句也要拆解，例如：
    はあ （はあ / 唉；嘆氣聲）
    え （え / 咦）
    うん （うん / 嗯）
    …… （…… / 沉默）
22. 不要加入額外說明、總結或評論。
"""


# =========================
# 讀取 FILE 區塊
# =========================

def load_blocks():
    text = MERGED_FILE.read_text(encoding="utf-8")

    pattern = re.compile(
        r"<<<FILE\s+(\d+)\s+\|\s+([\d\-]+)>>>\s*(.*?)\s*<<<END FILE\s+\1>>>",
        re.DOTALL
    )

    blocks = {}

    for match in pattern.finditer(text):
        file_no = int(match.group(1))
        number_range = match.group(2)
        content = match.group(3).strip()

        blocks[file_no] = {
            "range": number_range,
            "content": content,
        }

    return blocks


def parse_number_range(number_range: str):
    m = re.fullmatch(r"(\d+)-(\d+)", number_range.strip())
    if not m:
        raise ValueError(f"無法解析句子範圍：{number_range}")

    start = int(m.group(1))
    end = int(m.group(2))
    return start, end


# =========================
# API 呼叫
# =========================

def translate_block(file_no: int, number_range: str, content: str, retry_index: int = 1) -> str:
    file_label = f"{file_no:03d}"

    user_prompt = f"""檔案編號：{file_label}
句子範圍：{number_range}
目前嘗試次數：{retry_index}

請照指定格式逐字拆解以下內容。

非常重要：
1. 句子範圍是 {number_range}，這個範圍內每一個【編號】都必須輸出。
2. 不可以漏掉任何編號。
3. 每個【編號】後面都必須先輸出原本的日文原句。
4. 每一句都必須有逐字拆解。
5. 每一句都必須有「中文翻譯：」。
6. 逐字拆解區每一行都必須是「單詞 （假名 / 中文）」。
7. 不可以把原句整句複製到逐字拆解區。
8. 中文解釋不要混入 Hindi、韓文、阿拉伯文、泰文、西里爾字母、喬治亞字母等外語文字。
9. 不要拆解標點符號，不要把「、」「。」「？」「！」「」」「――」當成單詞拆出來。
10. 如果某個【編號】的原句本身只有標點，例如「!」「?」「?!」「「？」」，可以只保留原句與中文翻譯，不必硬拆。
11. 短反應句也必須拆解，例如「はあ」「え」「うん」「……」。

以下是要處理的內容：

{content}
"""

    response = client.responses.create(
        model=MODEL,
        input=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
    )

    return response.output_text


# =========================
# 後處理：括號對齊
# =========================

def visual_width(text: str) -> int:
    width = 0

    for ch in text:
        if unicodedata.east_asian_width(ch) in ("F", "W"):
            width += 2
        else:
            width += 1

    return width


def is_word_line(line: str) -> bool:
    stripped = line.strip()

    if not stripped:
        return False

    if stripped.startswith("【"):
        return False

    if stripped.startswith("中文翻譯"):
        return False

    if stripped.startswith("====="):
        return False

    if stripped.startswith("FILE "):
        return False

    if "（" in stripped and "）" in stripped and "/" in stripped:
        return True

    return False


def align_word_lines(text: str, target_col: int = 16) -> str:
    lines = text.splitlines()
    new_lines = []

    for line in lines:
        stripped = line.strip()

        if not is_word_line(stripped):
            new_lines.append(line.rstrip())
            continue

        word, rest = stripped.split("（", 1)
        word = word.rstrip()
        rest = "（" + rest

        width = visual_width(word)
        spaces_needed = max(1, target_col - width)

        new_line = word + (" " * spaces_needed) + rest
        new_lines.append(new_line)

    return "\n".join(new_lines)


# =========================
# 標點判斷
# =========================

def is_punctuation_only_sentence(text: str) -> bool:
    if text is None:
        return False

    s = text.strip()

    if not s:
        return False

    allowed_chars = set(
        "!?？！"
        "「」『』“”〝〟"
        "（）()［］[]【】"
        "、。，．・：:；;"
        "…‥―—─-ー"
        "＊*◇◆"
        "　 \t\r\n"
    )

    return all(ch in allowed_chars for ch in s)


# =========================
# 短反應句自動補拆解
# =========================

SHORT_INTERJECTION_MAP = {
    "はあ": "はあ （はあ / 唉；嘆氣聲）",
    "はぁ": "はぁ （はぁ / 唉；嘆氣聲）",
    "え": "え （え / 咦）",
    "ええ": "ええ （ええ / 嗯；是的）",
    "あ": "あ （あ / 啊）",
    "ああ": "ああ （ああ / 啊啊；原來如此）",
    "はい": "はい （はい / 是；好的）",
    "ん": "ん （ん / 嗯；疑問聲）",
    "うん": "うん （うん / 嗯）",
    "いや": "いや （いや / 不；不是）",
    "へえ": "へえ （へえ / 哦；原來如此）",
    "ほう": "ほう （ほう / 哦；原來如此）",
    "うぇ": "うぇ （うぇ / 呃；驚訝聲）",
    "うぇっ": "うぇっ （うぇっ / 呃；驚訝聲）",
    "えっ": "えっ （えっ / 咦；驚訝聲）",
    "あっ": "あっ （あっ / 啊；突然察覺聲）",
    "おっと": "おっと （おっと / 哎呀；糟了）",
    "…………": "………… （………… / 沉默）",
    "……": "…… （…… / 沉默）",
    "………": "……… （……… / 沉默）",
}


def clean_original_for_short_interjection(original: str) -> str:
    if original is None:
        return ""

    s = original.strip()
    s = s.strip("「」『』“”〝〟")

    return s.strip()


def add_missing_short_interjection_breakdown(text: str) -> str:
    lines = text.splitlines()
    new_lines = []

    i = 0
    while i < len(lines):
        line = lines[i]

        if not re.fullmatch(r"【\d+】", line.strip()):
            new_lines.append(line)
            i += 1
            continue

        block_lines = [line]
        i += 1

        while i < len(lines) and not re.fullmatch(r"【\d+】", lines[i].strip()):
            block_lines.append(lines[i])
            i += 1

        original = None

        for idx, bline in enumerate(block_lines):
            stripped = bline.strip()
            if idx == 0:
                continue
            if stripped:
                original = stripped
                break

        if original:
            clean_original = clean_original_for_short_interjection(original)

            has_translation_marker = any(b.strip() == "中文翻譯：" for b in block_lines)
            has_word_line = any(is_word_line(b.strip()) for b in block_lines)

            if clean_original in SHORT_INTERJECTION_MAP and has_translation_marker and not has_word_line:
                insert_line = SHORT_INTERJECTION_MAP[clean_original]

                new_block = []
                inserted = False

                for bline in block_lines:
                    if bline.strip() == "中文翻譯：" and not inserted:
                        while new_block and new_block[-1].strip() == "":
                            new_block.pop()

                        new_block.append("")
                        new_block.append(insert_line)
                        new_block.append("")
                        new_block.append("")
                        new_block.append("中文翻譯：")
                        inserted = True
                    else:
                        new_block.append(bline)

                block_lines = new_block

        new_lines.extend(block_lines)

    return "\n".join(new_lines)


# =========================
# 後處理：清理標點
# =========================

def remove_standalone_punctuation_lines(text: str) -> str:
    lines = text.splitlines()
    new_lines = []

    state = "outside"

    for line in lines:
        stripped = line.strip()

        if re.fullmatch(r"【\d+】", stripped):
            state = "after_number"
            new_lines.append(line.rstrip())
            continue

        if stripped == "":
            new_lines.append(line.rstrip())
            continue

        if state == "after_number":
            new_lines.append(line.rstrip())
            state = "breakdown"
            continue

        if stripped == "中文翻譯：":
            new_lines.append(line.rstrip())
            state = "translation"
            continue

        if state == "breakdown" and is_punctuation_only_sentence(stripped):
            continue

        new_lines.append(line.rstrip())

    return "\n".join(new_lines)


def remove_punctuation_word_lines(text: str) -> str:
    punctuation_words = {
        "、", "。", "？", "?", "！", "!",
        "「", "」", "『", "』",
        "“", "”", "〝", "〟",
        "――", "―", "…", "……",
        "・"
    }

    keep_words = {"＊", "*", "◇", "◆"}

    lines = text.splitlines()
    new_lines = []

    for line in lines:
        stripped = line.strip()

        if is_word_line(stripped):
            word = stripped.split("（", 1)[0].strip()

            if word in keep_words:
                new_lines.append(line.rstrip())
                continue

            if word in punctuation_words:
                continue

            if word and all(ch in punctuation_words for ch in word):
                continue

        new_lines.append(line.rstrip())

    return "\n".join(new_lines)


def remove_trailing_punctuation_after_word_line(text: str) -> str:
    lines = text.splitlines()
    new_lines = []

    for line in lines:
        stripped = line.strip()

        if is_word_line(stripped):
            line = re.sub(r"(）)[。！？!?、]+$", r"\1", line.rstrip())

        new_lines.append(line.rstrip())

    return "\n".join(new_lines)


# =========================
# 後處理：控制空行
# =========================

def normalize_blank_lines(text: str) -> str:
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"\n{4,}", "\n\n\n", text)

    lines = text.split("\n")
    new_lines = []

    i = 0
    while i < len(lines):
        line = lines[i].rstrip()

        if re.fullmatch(r"【\d+】", line.strip()):
            new_lines.append(line.strip())

            i += 1
            while i < len(lines) and lines[i].strip() == "":
                i += 1

            new_lines.append("")

            if i < len(lines):
                original_sentence = lines[i].rstrip()
                new_lines.append(original_sentence)
                new_lines.append("")

            i += 1
            continue

        if line.strip() == "中文翻譯：":
            while new_lines and new_lines[-1] == "":
                new_lines.pop()

            new_lines.append("")
            new_lines.append("")
            new_lines.append("中文翻譯：")
            i += 1
            continue

        new_lines.append(line)
        i += 1

    text = "\n".join(new_lines)
    text = re.sub(r"\n{1,}(?=【\d+】)", "\n\n\n", text)
    text = re.sub(r"\n{4,}", "\n\n\n", text)

    return text.strip()


def postprocess_result(text: str) -> str:
    text = remove_standalone_punctuation_lines(text)
    text = remove_punctuation_word_lines(text)
    text = remove_trailing_punctuation_after_word_line(text)
    text = add_missing_short_interjection_breakdown(text)
    text = align_word_lines(text, target_col=ALIGN_TARGET_COL)
    text = normalize_blank_lines(text)
    return text


# =========================
# 檢查器
# =========================

def contains_forbidden_foreign_script(text: str) -> bool:
    forbidden_ranges = [
        ("\u0900", "\u097F"),  # Devanagari / Hindi
        ("\uAC00", "\uD7AF"),  # Hangul syllables
        ("\u1100", "\u11FF"),  # Hangul jamo
        ("\u0600", "\u06FF"),  # Arabic
        ("\u0E00", "\u0E7F"),  # Thai
        ("\u0400", "\u04FF"),  # Cyrillic
        ("\u10A0", "\u10FF"),  # Georgian
        ("\u0530", "\u058F"),  # Armenian
        ("\u1200", "\u137F"),  # Ethiopic
    ]

    for ch in text:
        for start, end in forbidden_ranges:
            if start <= ch <= end:
                return True

    return False


def looks_like_long_japanese_without_parentheses(line: str) -> bool:
    stripped = line.strip()

    if not stripped:
        return False

    if "（" in stripped and "）" in stripped:
        return False

    if stripped in {"＊", "◇", "◆"}:
        return False

    if is_punctuation_only_sentence(stripped):
        return False

    if len(stripped) < 12:
        return False

    japanese_chars = re.findall(r"[\u3040-\u30ff\u3400-\u9fff]", stripped)

    if len(japanese_chars) >= 6:
        return True

    return False


def looks_like_broken_masu_split(line: str) -> bool:
    stripped = line.strip()

    suspicious_patterns = [
        r"いま\s*（",
        r"りま\s*（",
        r"きま\s*（",
        r"しりま\s*（",
        r"すか\s*（",
    ]

    for pat in suspicious_patterns:
        if re.search(pat, stripped):
            return True

    return False


def iter_sentence_blocks(result: str):
    lines = result.splitlines()
    blocks = []

    current = None

    for idx, line in enumerate(lines, start=1):
        stripped = line.strip()

        m = re.fullmatch(r"【(\d+)】", stripped)
        if m:
            if current:
                blocks.append(current)

            current = {
                "number": int(m.group(1)),
                "start_line": idx,
                "original": None,
                "original_line": None,
                "breakdown_lines": [],
                "translation_lines": [],
                "state": "after_number",
            }
            continue

        if current is None:
            continue

        if stripped == "":
            continue

        if current["state"] == "after_number":
            current["original"] = stripped
            current["original_line"] = idx
            current["state"] = "breakdown"
            continue

        if stripped == "中文翻譯：":
            current["state"] = "translation"
            continue

        if current["state"] == "breakdown":
            current["breakdown_lines"].append((idx, line))
            continue

        if current["state"] == "translation":
            current["translation_lines"].append((idx, line))
            continue

    if current:
        blocks.append(current)

    return blocks


def validate_result(file_no: int, number_range: str, result: str):
    warnings = []
    critical_warnings = []

    expected_start, expected_end = parse_number_range(number_range)
    expected_numbers = list(range(expected_start, expected_end + 1))

    blocks = iter_sentence_blocks(result)
    actual_numbers = [block["number"] for block in blocks]

    missing_numbers = [n for n in expected_numbers if n not in actual_numbers]
    extra_numbers = [n for n in actual_numbers if n < expected_start or n > expected_end]
    duplicated_numbers = sorted({n for n in actual_numbers if actual_numbers.count(n) > 1})

    if missing_numbers:
        msg = f"FILE {file_no:03d} | {number_range} | 缺少編號：{missing_numbers}"
        warnings.append(msg)
        critical_warnings.append(msg)

    if extra_numbers:
        msg = f"FILE {file_no:03d} | {number_range} | 出現範圍外編號：{extra_numbers}"
        warnings.append(msg)
        critical_warnings.append(msg)

    if duplicated_numbers:
        msg = f"FILE {file_no:03d} | {number_range} | 編號重複：{duplicated_numbers}"
        warnings.append(msg)
        critical_warnings.append(msg)

    for block in blocks:
        number = block["number"]
        original = block["original"]

        original_is_punctuation_only = is_punctuation_only_sentence(original) if original else False
        original_is_symbol_only = original in {"＊", "◇", "◆"} if original else False

        if not original:
            msg = f"FILE {file_no:03d} | {number_range} | 【{number}】缺少日文原句"
            warnings.append(msg)
            critical_warnings.append(msg)

        if not block["breakdown_lines"] and not original_is_symbol_only and not original_is_punctuation_only:
            msg = f"FILE {file_no:03d} | {number_range} | 【{number}】缺少逐字拆解"
            warnings.append(msg)
            critical_warnings.append(msg)

        if not block["translation_lines"] and not original_is_punctuation_only:
            msg = f"FILE {file_no:03d} | {number_range} | 【{number}】缺少中文翻譯"
            warnings.append(msg)
            critical_warnings.append(msg)

        for idx, line in block["breakdown_lines"]:
            stripped = line.strip()

            if not stripped:
                continue

            if stripped.startswith("===== FILE"):
                msg = f"FILE {file_no:03d} | {number_range} | line {idx} | 【{number}】逐字拆解區混入 FILE 標題：{stripped}"
                warnings.append(msg)
                critical_warnings.append(msg)

            if contains_forbidden_foreign_script(stripped):
                msg = f"FILE {file_no:03d} | {number_range} | line {idx} | 【{number}】疑似混入外語文字：{stripped}"
                warnings.append(msg)
                critical_warnings.append(msg)

            if looks_like_long_japanese_without_parentheses(stripped):
                msg = f"FILE {file_no:03d} | {number_range} | line {idx} | 【{number}】逐字拆解區疑似混入未拆長句：{stripped}"
                warnings.append(msg)
                critical_warnings.append(msg)

            if looks_like_broken_masu_split(stripped):
                msg = f"FILE {file_no:03d} | {number_range} | line {idx} | 【{number}】疑似ます形錯切：{stripped}"
                warnings.append(msg)

            if "（" in stripped and "）" in stripped and "/" not in stripped:
                msg = f"FILE {file_no:03d} | {number_range} | line {idx} | 【{number}】括號格式疑似不完整：{stripped}"
                warnings.append(msg)
                critical_warnings.append(msg)

            if "（" not in stripped and "）" not in stripped:
                if stripped not in {"＊", "◇", "◆"} and not is_punctuation_only_sentence(stripped) and len(stripped) >= 4:
                    msg = f"FILE {file_no:03d} | {number_range} | line {idx} | 【{number}】逐字拆解行沒有括號：{stripped}"
                    warnings.append(msg)
                    critical_warnings.append(msg)

            if original and stripped == original.strip() and not original_is_punctuation_only:
                msg = f"FILE {file_no:03d} | {number_range} | line {idx} | 【{number}】日文原句被重複放進逐字拆解區：{stripped}"
                warnings.append(msg)
                critical_warnings.append(msg)

    return warnings, critical_warnings


def append_warnings(
    file_no: int,
    number_range: str,
    retry_index: int,
    warnings: list[str],
    critical_warnings: list[str],
):
    if not warnings:
        return

    with open(WARNING_OUTPUT, "a", encoding="utf-8") as f:
        f.write(f"\n===== WARNING FILE {file_no:03d} | {number_range} | TRY {retry_index} =====\n")

        if critical_warnings:
            f.write("【嚴重警告：需要重試】\n")
            for warning in critical_warnings:
                f.write(warning + "\n")

        normal_warnings = [w for w in warnings if w not in critical_warnings]
        if normal_warnings:
            f.write("【一般警告】\n")
            for warning in normal_warnings:
                f.write(warning + "\n")


# =========================
# 輸出與進度
# =========================

def save_progress(next_file_no: int):
    PROGRESS_FILE.write_text(str(next_file_no), encoding="utf-8")


def load_progress():
    if PROGRESS_FILE.exists():
        text = PROGRESS_FILE.read_text(encoding="utf-8").strip()

        if text.isdigit():
            return int(text)

    return START_FILE


def save_failed_output(file_no: int, number_range: str, result: str):
    file_label = f"{file_no:03d}"
    failed_file = OUTPUT_DIR / f"{file_label}_{number_range}_翻譯_有問題.txt"
    failed_file.write_text(result, encoding="utf-8")
    return failed_file


# =========================
# 主程式
# =========================

def main():
    if not MERGED_FILE.exists():
        raise FileNotFoundError(f"找不到合併檔：{MERGED_FILE}")

    blocks = load_blocks()

    print(f"讀到 FILE 區塊數：{len(blocks)}")
    print(f"輸入檔案：{MERGED_FILE}")
    print(f"輸出資料夾：{OUTPUT_DIR}")
    print(f"模型：{MODEL}")
    print(f"處理範圍：FILE {START_FILE:03d} ～ FILE {END_FILE:03d}")
    print(f"警告輸出：{WARNING_OUTPUT}")
    print(f"最大重試次數：{MAX_RETRIES}")

    current = load_progress()

    if current < START_FILE:
        current = START_FILE

    available_file_numbers = sorted(
        file_no for file_no in blocks.keys()
        if START_FILE <= file_no <= END_FILE
    )

    for file_no in available_file_numbers:
        if file_no < current:
            continue

        block = blocks[file_no]
        number_range = block["range"]
        content = block["content"]

        file_label = f"{file_no:03d}"
        output_file = OUTPUT_DIR / f"{file_label}_{number_range}_翻譯.txt"

        if output_file.exists():
            print(f"已存在，跳過：{output_file.name}")
            save_progress(file_no + 1)
            continue

        print(f"\n處理中：FILE {file_label} | {number_range}")

        final_result = None
        final_warnings = []
        final_critical_warnings = []

        for retry_index in range(1, MAX_RETRIES + 1):
            try:
                print(f"  嘗試 {retry_index}/{MAX_RETRIES}")

                result = translate_block(file_no, number_range, content, retry_index=retry_index)
                result = postprocess_result(result)

                warnings, critical_warnings = validate_result(file_no, number_range, result)

                append_warnings(file_no, number_range, retry_index, warnings, critical_warnings)

                final_result = result
                final_warnings = warnings
                final_critical_warnings = critical_warnings

                if not critical_warnings:
                    break

                print(f"  發現 {len(critical_warnings)} 個嚴重問題，準備重試")

            except Exception as e:
                print(f"  API 或處理錯誤：{e}")
                if retry_index == MAX_RETRIES:
                    raise

        if final_result is None:
            print(f"FILE {file_label} 沒有產生結果，程式停止。")
            break

        if final_critical_warnings:
            failed_file = save_failed_output(file_no, number_range, final_result)
            print(f"FILE {file_label} 重試 {MAX_RETRIES} 次後仍有嚴重問題。")
            print(f"問題輸出已保存：{failed_file}")
            print("程式停止，避免錯誤內容寫進合併檔。")
            break

        output_file.write_text(final_result, encoding="utf-8")

        if final_warnings:
            print(f"完成：{output_file.name}，但有 {len(final_warnings)} 個一般警告")
        else:
            print(f"完成：{output_file.name}")

        save_progress(file_no + 1)

    print("\n處理結束。")
    print(f"單檔輸出資料夾：{OUTPUT_DIR}")
    print(f"警告輸出：{WARNING_OUTPUT}")
    print("如需產生 final_output.md，請執行：python scripts/04_merge_outputs.py")


if __name__ == "__main__":
    main()