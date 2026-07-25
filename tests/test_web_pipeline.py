import importlib.util
import sys
import unittest
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent


def load_module(module_name: str, path: Path):
    spec = importlib.util.spec_from_file_location(module_name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


web_server = load_module("jra_web_server_test", BASE_DIR / "web" / "server.py")
api_pipeline = load_module("jra_api_pipeline_test", BASE_DIR / "scripts" / "03_run_api.py")


class FakeResponse:
    output_text = """【1】

朝の教室には、まだ誰もいなかった。

朝 （あさ / 早晨）

の （の / 的）

教室 （きょうしつ / 教室）

中文翻譯：
早晨的教室裡，還沒有人。
"""


class FakeResponses:
    def create(self, **_kwargs):
        return FakeResponse()


class FakeClient:
    responses = FakeResponses()


INLINE_TRANSLATION_EXAMPLE = """【1】

振り向くと、彼が眠そうな顔で立っていた。

振り向く （ふりむく / 回頭）

と （と / 一...就...；一...便...）

彼 （ かれ / 他）

が （ が / 主語標記）

眠そうな （ねむそうな / 看起來很想睡的）

顔 （かお / 表情；臉）

で （で / 以；帶著）

立っていた （たっていた / 站著）

中文翻譯： 一回頭，就看見他帶著一副像是很想睡的表情站著。"""


class WebPipelineTests(unittest.TestCase):
    def test_preview_reuses_existing_sentence_splitter(self):
        sentences, total = web_server.extract_preview(
            "朝です。今日は晴れです！「出かけますか？」",
            limit=2,
        )

        self.assertEqual(total, 3)
        self.assertEqual(sentences, ["朝です。", "今日は晴れです！"])

    def test_preview_preserves_001_and_supports_batch_offset(self):
        text = "００１\n\n朝です。昼です。夜です。"

        first_batch, total = web_server.extract_preview(text, limit=2, offset=0)
        second_batch, second_total = web_server.extract_preview(
            text,
            limit=2,
            offset=2,
        )

        self.assertEqual(total, 4)
        self.assertEqual(second_total, 4)
        self.assertEqual(first_batch, ["００１", "朝です。"])
        self.assertEqual(second_batch, ["昼です。", "夜です。"])

    def test_numbered_batch_keeps_global_sentence_numbers(self):
        numbered = web_server.number_sentences(
            ["昼です。", "夜です。"],
            start_number=21,
        )

        self.assertIn("【21】\n昼です。", numbered)
        self.assertIn("【22】\n夜です。", numbered)
        self.assertNotIn("【1】", numbered)

    def test_batch_size_is_capped_at_twenty_sentences(self):
        self.assertEqual(web_server.parse_limit(50), 20)
        self.assertEqual(web_server.parse_limit("10"), 10)
        self.assertEqual(web_server.parse_offset(-5), 0)

    def test_stream_progress_counts_only_complete_sentence_blocks(self):
        streamed_text = "\n\n".join(
            f"【{number}】\n原句{number}。\n\n中文翻譯：翻譯{number}。"
            for number in range(1, 10)
        )

        ready = web_server.extract_ready_sentence_blocks(streamed_text)
        all_blocks = web_server.extract_ready_sentence_blocks(
            streamed_text,
            include_last=True,
        )

        self.assertEqual(len(ready), 8)
        self.assertEqual(ready[-1][0], 8)
        self.assertEqual(len(all_blocks), 9)

    def test_resumed_batch_stops_at_original_batch_end(self):
        text = "".join(f"第{number}句です。" for number in range(1, 101))

        remaining, total = web_server.extract_preview(
            text,
            limit=16,
            offset=64,
        )

        self.assertEqual(total, 100)
        self.assertEqual(len(remaining), 16)
        self.assertEqual(remaining[0], "第65句です。")
        self.assertEqual(remaining[-1], "第80句です。")

    def test_api_errors_are_converted_to_safe_actionable_messages(self):
        class FakeQuotaError(Exception):
            status_code = 429
            body = {"error": {"code": "insufficient_quota"}}

        class FakeAuthenticationError(Exception):
            status_code = 401

        quota_message = web_server.describe_processing_error(FakeQuotaError())
        auth_message = web_server.describe_processing_error(
            FakeAuthenticationError()
        )

        self.assertIn("額度不足", quota_message)
        self.assertIn("API Key 無效", auth_message)
        self.assertNotIn("sk-", quota_message)
        self.assertNotIn("sk-", auth_message)

    def test_numeric_section_marker_is_kept_without_word_breakdown(self):
        raw_result = """【1】

００１

００１ （００１ / 001）

中文翻譯： 001
"""

        processed = api_pipeline.postprocess_result(raw_result)
        warnings, critical = api_pipeline.validate_result(
            file_no=1,
            number_range="1-1",
            result=processed,
        )
        serialized = web_server.serialize_result(api_pipeline, processed)
        formatted = web_server.format_result(serialized)

        self.assertFalse(critical, warnings)
        self.assertEqual(serialized[0]["original"], "００１")
        self.assertEqual(serialized[0]["breakdown"], [])
        self.assertIn("００１", formatted)
        self.assertIn("中文翻譯： 001", formatted)
        self.assertNotIn("００１ （００１ / 001）", formatted)

    def test_api_module_can_load_without_environment_key(self):
        result = api_pipeline.translate_block(
            file_no=1,
            number_range="1-1",
            content="【1】\n朝の教室には、まだ誰もいなかった。",
            api_client=FakeClient(),
        )

        self.assertIn("朝の教室", result)

    def test_quality_checker_detects_missing_number(self):
        warnings, critical = api_pipeline.validate_result(
            file_no=1,
            number_range="1-2",
            result=FakeResponse.output_text,
        )

        self.assertTrue(any("缺少編號" in warning for warning in warnings))
        self.assertTrue(critical)

    def test_result_is_serialized_for_vue(self):
        serialized = web_server.serialize_result(api_pipeline, FakeResponse.output_text)

        self.assertEqual(serialized[0]["number"], 1)
        self.assertEqual(serialized[0]["breakdown"][0]["word"], "朝")
        self.assertEqual(serialized[0]["breakdown"][0]["kana"], "あさ")
        self.assertEqual(serialized[0]["translation"], "早晨的教室裡，還沒有人。")

    def test_requested_output_format_is_preserved(self):
        warnings, critical = api_pipeline.validate_result(
            file_no=1,
            number_range="1-1",
            result=INLINE_TRANSLATION_EXAMPLE,
        )
        serialized = web_server.serialize_result(
            api_pipeline,
            INLINE_TRANSLATION_EXAMPLE,
        )
        formatted = web_server.format_result(serialized)

        self.assertFalse(critical, warnings)
        self.assertIn("彼 （かれ / 他）", formatted)
        self.assertIn(
            "中文翻譯： 一回頭，就看見他帶著一副像是很想睡的表情站著。",
            formatted,
        )
        self.assertNotIn("中文翻譯：\n", formatted)


if __name__ == "__main__":
    unittest.main()
