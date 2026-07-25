from __future__ import annotations

import importlib.util
import json
import re
import time
from http import HTTPStatus
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import urlparse


BASE_DIR = Path(__file__).resolve().parent.parent
WEB_DIR = BASE_DIR / "web"
DIST_DIR = WEB_DIR / "dist"
MAX_BODY_BYTES = 2 * 1024 * 1024 + 16 * 1024
MAX_SENTENCES = 20
SENTENCE_MARKER_PATTERN = re.compile(r"(?m)^【(\d+)】[ \t]*\r?$")


def load_script_module(module_name: str, file_name: str):
    path = BASE_DIR / "scripts" / file_name
    spec = importlib.util.spec_from_file_location(module_name, path)

    if spec is None or spec.loader is None:
        raise RuntimeError(f"無法載入：{path}")

    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


splitter = load_script_module("jra_splitter", "01_split_paragraphs.py")


def parse_limit(value: Any) -> int:
    try:
        limit = int(value)
    except (TypeError, ValueError):
        limit = MAX_SENTENCES
    return max(1, min(limit, MAX_SENTENCES))


def parse_offset(value: Any) -> int:
    try:
        offset = int(value)
    except (TypeError, ValueError):
        offset = 0
    return max(0, offset)


def extract_preview(text: str, limit: int, offset: int = 0) -> tuple[list[str], int]:
    cleaned = splitter.preprocess_text(text)
    sentences = splitter.extract_sentences(cleaned)
    return sentences[offset:offset + limit], len(sentences)


def number_sentences(sentences: list[str], start_number: int = 1) -> str:
    lines: list[str] = []
    for index, sentence in enumerate(sentences, start=start_number):
        lines.extend((f"【{index}】", sentence, ""))
    return "\n".join(lines).strip()


def parse_breakdown_line(line: str) -> dict[str, str] | None:
    match = re.fullmatch(r"\s*(.*?)\s*（\s*(.*?)\s*/\s*(.*?)\s*）\s*", line)
    if not match:
        return None
    return {
        "word": match.group(1).strip(),
        "kana": match.group(2).strip(),
        "meaning": match.group(3).strip(),
    }


def serialize_result(api_module, result_text: str) -> list[dict[str, Any]]:
    sentences: list[dict[str, Any]] = []

    for block in api_module.iter_sentence_blocks(result_text):
        breakdown = []
        for _, line in block["breakdown_lines"]:
            item = parse_breakdown_line(line)
            if item:
                breakdown.append(item)

        translation = " ".join(
            line.strip()
            for _, line in block["translation_lines"]
            if line.strip()
        )

        sentences.append(
            {
                "number": block["number"],
                "original": block["original"] or "",
                "breakdown": breakdown,
                "translation": translation,
            }
        )

    return sentences


def format_result(sentences: list[dict[str, Any]]) -> str:
    sections: list[str] = []

    for sentence in sentences:
        lines = [
            f"【{sentence['number']}】",
            "",
            sentence["original"],
        ]

        for item in sentence["breakdown"]:
            lines.extend(
                (
                    "",
                    f"{item['word']} （{item['kana']} / {item['meaning']}）",
                )
            )

        lines.extend(
            (
                "",
                f"中文翻譯： {sentence['translation']}",
            )
        )
        sections.append("\n".join(lines))

    return "\n\n\n".join(sections).strip()


def extract_ready_sentence_blocks(
    text: str,
    include_last: bool = False,
) -> list[tuple[int, str]]:
    matches = list(SENTENCE_MARKER_PATTERN.finditer(text))
    ready_count = len(matches) if include_last else max(0, len(matches) - 1)
    blocks: list[tuple[int, str]] = []

    for index in range(ready_count):
        start = matches[index].start()
        end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        blocks.append((int(matches[index].group(1)), text[start:end].strip()))

    return blocks


def get_api_error_code(exc: Exception) -> str:
    code = getattr(exc, "code", None)
    if code:
        return str(code)

    body = getattr(exc, "body", None)
    if not isinstance(body, dict):
        return ""

    nested_error = body.get("error")
    if isinstance(nested_error, dict):
        code = nested_error.get("code") or nested_error.get("type")
    else:
        code = body.get("code") or body.get("type")

    return str(code or "")


def describe_processing_error(exc: Exception) -> str:
    error_name = type(exc).__name__.lower()
    status_code = getattr(exc, "status_code", None)
    error_code = get_api_error_code(exc).lower()

    if status_code == 401 or "authentication" in error_name:
        return "API Key 無效或已失效，請重新建立並輸入金鑰。"

    if error_code == "insufficient_quota":
        return "OpenAI API 額度不足或尚未啟用付費，請先確認 Billing 與可用額度。"

    if status_code == 429 or "ratelimit" in error_name:
        return "OpenAI API 暫時達到速率限制，請稍候一分鐘再重試。"

    if status_code == 403 or "permission" in error_code:
        return "這個 API Key 沒有使用目前模型的權限，請確認專案與模型權限。"

    if status_code == 404 or error_code == "model_not_found":
        return "目前設定的 OpenAI 模型無法使用，請確認 OPENAI_MODEL 設定與帳號權限。"

    if "timeout" in error_name:
        return "OpenAI 回應逾時，請把每批句數改成 10 句後再試。"

    if "connection" in error_name:
        return "本機無法連上 OpenAI API，請檢查網路、VPN 或防火牆。"

    if status_code == 400 or "badrequest" in error_name:
        return "OpenAI 拒絕這次請求，請把每批句數改成 10 句後再試。"

    return "處理失敗；本機服務已記錄安全的錯誤類型，請重新嘗試或查看終端狀態。"


class AppHandler(SimpleHTTPRequestHandler):
    server_version = "JapaneseReadingAssistant/0.1"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(DIST_DIR), **kwargs)

    def log_message(self, format_string: str, *args) -> None:
        safe_args = tuple("<redacted>" if "sk-" in str(arg) else arg for arg in args)
        super().log_message(format_string, *safe_args)

    def end_headers(self) -> None:
        self.send_header("Cache-Control", "no-store, no-cache, must-revalidate")
        self.send_header("Pragma", "no-cache")
        self.send_header("Expires", "0")
        super().end_headers()

    def send_json(self, payload: dict[str, Any], status: HTTPStatus = HTTPStatus.OK) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def start_ndjson_stream(self) -> None:
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", "application/x-ndjson; charset=utf-8")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.end_headers()

    def send_stream_event(self, payload: dict[str, Any]) -> bool:
        try:
            body = (json.dumps(payload, ensure_ascii=False) + "\n").encode("utf-8")
            self.wfile.write(body)
            self.wfile.flush()
            return True
        except (BrokenPipeError, ConnectionResetError, OSError):
            self.close_connection = True
            return False

    def read_json(self) -> dict[str, Any]:
        content_length = int(self.headers.get("Content-Length", "0"))
        if content_length <= 0 or content_length > MAX_BODY_BYTES:
            raise ValueError("請選擇小於 2 MB 的 TXT 檔案。")

        raw = self.rfile.read(content_length)
        payload = json.loads(raw.decode("utf-8"))
        if not isinstance(payload, dict):
            raise ValueError("請求格式不正確。")
        return payload

    def do_GET(self) -> None:
        path = urlparse(self.path).path

        if path == "/api/health":
            self.send_json({"status": "ok", "service": "Japanese Reading Assistant"})
            return

        if not DIST_DIR.exists():
            self.send_json(
                {"error": "前端尚未建置，請先在 web 資料夾執行 pnpm build。"},
                HTTPStatus.SERVICE_UNAVAILABLE,
            )
            return

        if path != "/" and not (DIST_DIR / path.lstrip("/")).exists():
            self.path = "/"
        super().do_GET()

    def do_POST(self) -> None:
        path = urlparse(self.path).path

        try:
            payload = self.read_json()
            text = str(payload.get("text", "")).strip()
            limit = parse_limit(payload.get("limit"))
            offset = parse_offset(payload.get("offset"))

            if not text:
                raise ValueError("TXT 內容是空的。")

            if path == "/api/preview":
                sentences, total = extract_preview(text, limit, offset)
                batch_end = offset + len(sentences)
                self.send_json(
                    {
                        "total": total,
                        "offset": offset,
                        "start": offset + 1 if sentences else 0,
                        "end": batch_end,
                        "nextOffset": batch_end,
                        "hasMore": batch_end < total,
                        "sentences": [
                            {"number": index, "text": sentence}
                            for index, sentence in enumerate(
                                sentences,
                                start=offset + 1,
                            )
                        ],
                    }
                )
                return

            if path == "/api/process":
                self.process_text(payload, text, limit, offset)
                return

            if path == "/api/process-stream":
                self.process_text_stream(payload, text, limit, offset)
                return

            self.send_json({"error": "找不到這個功能。"}, HTTPStatus.NOT_FOUND)
        except (UnicodeDecodeError, json.JSONDecodeError):
            self.send_json({"error": "無法讀取請求內容。"}, HTTPStatus.BAD_REQUEST)
        except ValueError as exc:
            self.send_json({"error": str(exc)}, HTTPStatus.BAD_REQUEST)
        except Exception as exc:
            message = describe_processing_error(exc)
            safe_error_name = type(exc).__name__
            safe_status = getattr(exc, "status_code", None)
            safe_code = get_api_error_code(exc) or None
            print(
                "API processing error:",
                {
                    "type": safe_error_name,
                    "status": safe_status,
                    "code": safe_code,
                },
            )
            self.send_json({"error": message}, HTTPStatus.INTERNAL_SERVER_ERROR)

    def process_text(
        self,
        payload: dict[str, Any],
        text: str,
        limit: int,
        offset: int,
    ) -> None:
        api_key = str(payload.get("apiKey", "")).strip()
        if not api_key:
            raise ValueError("請輸入 OpenAI API Key。")
        if len(api_key) < 20:
            raise ValueError("API Key 格式似乎不完整。")

        from openai import OpenAI

        api_module = load_script_module("jra_api_runtime", "03_run_api.py")
        sentences, total = extract_preview(text, limit, offset)
        if not sentences:
            if offset >= total and total > 0:
                raise ValueError("這份文字已經處理完畢。")
            raise ValueError("沒有辨識到可處理的日文句子。")

        batch_start = offset + 1
        batch_end = offset + len(sentences)
        content = number_sentences(sentences, start_number=batch_start)
        number_range = f"{batch_start}-{batch_end}"
        started_at = time.perf_counter()

        client = OpenAI(api_key=api_key)
        raw_result = api_module.translate_block(
            file_no=1,
            number_range=number_range,
            content=content,
            retry_index=1,
            api_client=client,
        )
        processed_result = api_module.postprocess_result(raw_result)
        warnings, critical_warnings = api_module.validate_result(
            file_no=1,
            number_range=number_range,
            result=processed_result,
        )

        serialized_sentences = serialize_result(api_module, processed_result)

        self.send_json(
            {
                "source": {
                    "totalSentences": total,
                    "processedSentences": len(sentences),
                    "batchStart": batch_start,
                    "batchEnd": batch_end,
                    "nextOffset": batch_end,
                    "hasMore": batch_end < total,
                },
                "model": api_module.MODEL,
                "elapsedSeconds": round(time.perf_counter() - started_at, 1),
                "sentences": serialized_sentences,
                "formattedText": format_result(serialized_sentences),
                "quality": {
                    "warnings": warnings,
                    "criticalWarnings": critical_warnings,
                    "passed": not critical_warnings,
                },
            }
        )

    def process_text_stream(
        self,
        payload: dict[str, Any],
        text: str,
        limit: int,
        offset: int,
    ) -> None:
        api_key = str(payload.get("apiKey", "")).strip()
        if not api_key:
            raise ValueError("請輸入 OpenAI API Key。")
        if len(api_key) < 20:
            raise ValueError("API Key 格式似乎不完整。")

        from openai import OpenAI

        api_module = load_script_module("jra_api_stream_runtime", "03_run_api.py")
        sentences, total = extract_preview(text, limit, offset)
        if not sentences:
            if offset >= total and total > 0:
                raise ValueError("這份文字已經處理完畢。")
            raise ValueError("沒有辨識到可處理的日文句子。")

        batch_start = offset + 1
        batch_end = offset + len(sentences)
        content = number_sentences(sentences, start_number=batch_start)
        number_range = f"{batch_start}-{batch_end}"
        started_at = time.perf_counter()

        self.start_ndjson_stream()
        if not self.send_stream_event(
            {
                "type": "start",
                "model": api_module.MODEL,
                "source": {
                    "totalSentences": total,
                    "processedSentences": 0,
                    "batchStart": batch_start,
                    "batchEnd": batch_end,
                    "nextOffset": offset,
                    "hasMore": offset < total,
                },
                "batchTotal": len(sentences),
            }
        ):
            return

        stream = None
        raw_result = ""
        emitted_count = 0

        try:
            client = OpenAI(api_key=api_key)
            stream = api_module.translate_block_stream(
                file_no=1,
                number_range=number_range,
                content=content,
                retry_index=1,
                api_client=client,
            )

            for event in stream:
                if getattr(event, "type", "") != "response.output_text.delta":
                    continue

                raw_result += getattr(event, "delta", "")
                ready_blocks = extract_ready_sentence_blocks(raw_result)

                while emitted_count < len(ready_blocks):
                    number, fragment = ready_blocks[emitted_count]
                    processed_fragment = api_module.postprocess_result(fragment)
                    warnings, critical_warnings = api_module.validate_result(
                        file_no=1,
                        number_range=f"{number}-{number}",
                        result=processed_fragment,
                    )
                    serialized = serialize_result(api_module, processed_fragment)
                    emitted_count += 1

                    if not self.send_stream_event(
                        {
                            "type": "sentence",
                            "completed": emitted_count,
                            "batchTotal": len(sentences),
                            "sentence": serialized[0] if serialized else None,
                            "formattedText": (
                                format_result(serialized)
                                if serialized
                                else processed_fragment
                            ),
                            "quality": {
                                "warnings": warnings,
                                "criticalWarnings": critical_warnings,
                                "passed": not critical_warnings,
                            },
                        }
                    ):
                        return

            processed_result = api_module.postprocess_result(raw_result)
            warnings, critical_warnings = api_module.validate_result(
                file_no=1,
                number_range=number_range,
                result=processed_result,
            )
            serialized_sentences = serialize_result(api_module, processed_result)

            while emitted_count < len(serialized_sentences):
                sentence = serialized_sentences[emitted_count]
                emitted_count += 1
                if not self.send_stream_event(
                    {
                        "type": "sentence",
                        "completed": emitted_count,
                        "batchTotal": len(sentences),
                        "sentence": sentence,
                        "formattedText": format_result([sentence]),
                        "quality": {
                            "warnings": [],
                            "criticalWarnings": [],
                            "passed": True,
                        },
                    }
                ):
                    return

            self.send_stream_event(
                {
                    "type": "result",
                    "source": {
                        "totalSentences": total,
                        "processedSentences": len(sentences),
                        "batchStart": batch_start,
                        "batchEnd": batch_end,
                        "nextOffset": batch_end,
                        "hasMore": batch_end < total,
                    },
                    "model": api_module.MODEL,
                    "elapsedSeconds": round(time.perf_counter() - started_at, 1),
                    "sentences": serialized_sentences,
                    "formattedText": format_result(serialized_sentences),
                    "quality": {
                        "warnings": warnings,
                        "criticalWarnings": critical_warnings,
                        "passed": not critical_warnings,
                    },
                }
            )
        except Exception as exc:
            self.send_stream_event(
                {
                    "type": "error",
                    "error": describe_processing_error(exc),
                }
            )
        finally:
            close_stream = getattr(stream, "close", None)
            if callable(close_stream):
                close_stream()


def main() -> None:
    host = "127.0.0.1"
    port = 8000
    server = ThreadingHTTPServer((host, port), AppHandler)

    print(f"Japanese Reading Assistant 已啟動：http://{host}:{port}")
    print("按 Ctrl+C 可停止服務。")

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
