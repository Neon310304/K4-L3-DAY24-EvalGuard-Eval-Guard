from __future__ import annotations

"""Phase C: Production Guardrails — Presidio PII + NeMo Guardrails + P95 Latency."""

import asyncio
import json
import os
import statistics
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import (ADVERSARIAL_SET_PATH, GUARDRAILS_CONFIG_DIR, LATENCY_BUDGET_P95_MS,
                    PRESIDIO_LANGUAGE, PRESIDIO_SPACY_MODEL)


# ─── Task 9a: Presidio PII Detection ─────────────────────────────────────────

def setup_presidio():
    """Khởi tạo Presidio engine với custom Vietnamese PII recognizers. (Đã implement sẵn)

    Custom recognizers thêm vào:
        VN_CCCD  — số CCCD 12 chữ số hoặc CMND 9 chữ số
        VN_PHONE — số điện thoại Việt Nam (0[3-9]xxxxxxxx)

    Các recognizers mặc định đã có sẵn: EMAIL, PHONE_NUMBER (international), ...
    """
    from presidio_analyzer import AnalyzerEngine, RecognizerRegistry, Pattern, PatternRecognizer
    from presidio_anonymizer import AnonymizerEngine
    from presidio_analyzer.nlp_engine import NlpEngineProvider

    cccd_recognizer = PatternRecognizer(
        supported_entity="VN_CCCD",
        patterns=[
            Pattern("CCCD 12 digits", r"\b\d{12}\b", 0.9),
            Pattern("CMND 9 digits",  r"\b\d{9}\b",  0.7),
        ],
    )
    phone_recognizer = PatternRecognizer(
        supported_entity="VN_PHONE",
        patterns=[Pattern("VN mobile", r"\b0[3-9]\d{8}\b", 0.9)],
    )

    registry = RecognizerRegistry()
    # Restrict to the identifiers required by the lab. English NER would also
    # block dates/locations in clean Vietnamese policy questions.
    registry.load_predefined_recognizers()
    registry.recognizers = [r for r in registry.recognizers
                            if set(r.supported_entities) & {"EMAIL_ADDRESS", "PHONE_NUMBER"}]
    registry.add_recognizer(cccd_recognizer)
    registry.add_recognizer(phone_recognizer)

    # The registry uses identifier patterns rather than spaCy NER. A small model
    # is sufficient for this guard-only runtime; Docker keeps the large default.
    nlp_engine = NlpEngineProvider(nlp_configuration={
        "nlp_engine_name": "spacy",
        "models": [{"lang_code": PRESIDIO_LANGUAGE, "model_name": PRESIDIO_SPACY_MODEL}],
    }).create_engine()
    analyzer  = AnalyzerEngine(registry=registry, nlp_engine=nlp_engine)
    anonymizer = AnonymizerEngine()
    return analyzer, anonymizer


def pii_scan(text: str, analyzer=None, anonymizer=None) -> dict:
    """Task 9a: Quét PII trong văn bản bằng Presidio.

    Returns:
        {
          "has_pii":    bool,
          "entities":   [{"type": str, "text": str, "score": float, "start": int, "end": int}],
          "anonymized": str,   # text với PII được thay bằng <TYPE>
        }
    """
    if analyzer is None or anonymizer is None:
        analyzer, anonymizer = setup_presidio()
    results = analyzer.analyze(text=text, language=PRESIDIO_LANGUAGE)
    if not results:
        return {"has_pii": False, "entities": [], "anonymized": text}
    entities = [{"type": r.entity_type, "text": text[r.start:r.end],
                 "score": float(r.score), "start": r.start, "end": r.end} for r in results]
    return {"has_pii": True, "entities": entities,
            "anonymized": anonymizer.anonymize(text=text, analyzer_results=results).text}


# ─── Task 9b + 11: NeMo Guardrails ───────────────────────────────────────────

PROVIDER_REFUSAL = "Yêu cầu bị chặn bởi bộ lọc an toàn của nhà cung cấp."

def _provider_filtered(error: Exception) -> bool:
    """Recognize structured provider rejections through NeMo's wrapper.

    Arbitrary error text is not a rail decision. Auth/rate-limit/timeouts remain
    errors; upstream content_filter decisions are recorded separately from rails.
    """
    pending, seen = [error], set()
    while pending:
        current = pending.pop()
        if id(current) in seen:
            continue
        seen.add(id(current))
        body = getattr(current, "body", None)
        if isinstance(body, dict):
            payload = body.get("error", body)
            if isinstance(payload, dict) and payload.get("code") == "content_filter":
                return True
        pending.extend(arg for arg in current.args if isinstance(arg, Exception))
        for cause in (current.__cause__, current.__context__):
            if cause is not None:
                pending.append(cause)
    return False


def setup_nemo_rails():
    """Khởi tạo NeMo Guardrails từ guardrails/config.yml. (Đã implement sẵn)

    Config directory: guardrails/
        config.yml  — model + rails config
        rails.co    — câu từ chối Colang 1.0; built-in self-check flows được bật trong YAML
    """
    from nemoguardrails import RailsConfig, LLMRails
    config = RailsConfig.from_path(GUARDRAILS_CONFIG_DIR)
    from config import GUARD_MODEL, OPENAI_BASE_URL, API_TIMEOUT_SECONDS
    for model in config.models:
        if model.engine == "openai":
            model.model = GUARD_MODEL
            model.parameters.update({"openai_api_base": OPENAI_BASE_URL,
                                     "request_timeout": API_TIMEOUT_SECONDS})
    rails  = LLMRails(config)
    return rails


async def check_input_rail(text: str, rails=None) -> dict:
    """Task 9b: Kiểm tra input qua NeMo input rails (topic guard + jailbreak guard).

    Returns:
        {
          "allowed":        bool,
          "blocked_reason": str | None,
          "response":       str,          # NeMo's raw response
        }
    """
    if rails is None:
        rails = setup_nemo_rails()
    try:
        result = await rails.generate_async(
            messages=[{"role": "user", "content": text}],
            options={"rails": ["input"], "log": {"activated_rails": True}},
        )
    except Exception as error:
        if not _provider_filtered(error):
            raise
        return {"allowed": False, "blocked_reason": "provider_content_filter",
                "response": PROVIDER_REFUSAL, "decision_source": "provider_content_filter"}
    blocked = any(rail.stop for rail in result.log.activated_rails)
    return {"allowed": not blocked, "blocked_reason": "nemo_input_rail" if blocked else None,
            "response": result.response[0]["content"]}


async def check_output_rail(question: str, answer: str, rails=None) -> dict:
    """Task 11: Kiểm tra LLM output qua NeMo output rails trước khi trả về user.

    NeMo output rails hoạt động trong context của cả cuộc hội thoại (input + output).
    Kiểm tra PII và nội dung nhạy cảm. Self-check này không thay RAGAS faithfulness
    hoặc kiểm tra factual accuracy với retrieved contexts.

    Returns:
        {
          "safe":           bool,
          "flagged_reason": str | None,
          "final_answer":   str,          # answer đã qua guard (có thể bị redact)
        }
    """
    if rails is None:
        rails = setup_nemo_rails()
    try:
        result = await rails.generate_async(
            messages=[{"role": "user", "content": question},
                      {"role": "assistant", "content": answer}],
            options={"rails": ["output"], "log": {"activated_rails": True}},
        )
    except Exception as error:
        if not _provider_filtered(error):
            raise
        return {"safe": False, "flagged_reason": "provider_content_filter",
                "final_answer": PROVIDER_REFUSAL, "decision_source": "provider_content_filter"}
    flagged = any(rail.stop for rail in result.log.activated_rails)
    return {"safe": not flagged, "flagged_reason": "nemo_output_rail" if flagged else None,
            "final_answer": result.response[0]["content"] if flagged else answer}


# ─── Task 10: Adversarial Test Suite ─────────────────────────────────────────

def run_adversarial_suite(adversarial_set: list[dict], rails=None,
                           analyzer=None, anonymizer=None) -> list[dict]:
    """Task 10: Chạy list inputs bất kỳ qua hai tầng input, đối chiếu expected.

    Guard stack order:
        1. pii_scan()         → block nếu has_pii, không phụ thuộc category
        2. check_input_rail() → block nếu jailbreak / off-topic / prompt injection

    Expected/category chỉ là metadata để lưu và đối chiếu sau quyết định actual.
    Output rail là Task 11 riêng, không được chạy trong input suite này.

    Returns:
        list of {
          "id": int, "category": str, "input": str,
          "expected": "blocked"|"allowed",
          "actual":   "blocked"|"allowed",
          "blocked_by": str | None,       # "presidio" | "nemo_input" | None
          "passed": bool,
        }
    """
    if not adversarial_set:
        return []
    if analyzer is None or anonymizer is None:
        analyzer, anonymizer = setup_presidio()
    if rails is None:
        rails = setup_nemo_rails()

    async def run_all():
        rows = []
        for item in adversarial_set:
            blocked_by = None
            decision_source = "presidio"
            reason = None
            if pii_scan(item["input"], analyzer, anonymizer)["has_pii"]:
                blocked_by = "presidio"
            else:
                rail = await check_input_rail(item["input"], rails)
                decision_source = rail.get("decision_source", "nemo_rail")
                reason = rail.get("blocked_reason")
                if not rail["allowed"]:
                    blocked_by = "nemo_input"
            actual = "blocked" if blocked_by else "allowed"
            rows.append({"id": item["id"], "category": item["category"],
                         "input": item["input"], "expected": item["expected"],
                         "actual": actual, "blocked_by": blocked_by,
                         "decision_source": decision_source, "blocked_reason": reason,
                         "passed": actual == item["expected"]})
        return rows

    return asyncio.run(run_all())


# ─── Task 12: P95 Latency Measurement ────────────────────────────────────────

def measure_p95_latency(test_inputs: list[str], n_runs: int = 20,
                         rails=None, analyzer=None, anonymizer=None) -> dict:
    """Task 12: measure INPUT layers sequentially, not end-to-end guard/RAG latency.

    Reuse engines. Inside ONE event loop, execute two real warm-up calls per layer,
    excluded from samples. Then collect exactly n_runs timed samples (cycle clean
    inputs), always measuring BOTH PII and NeMo input even if PII blocks.
    Use perf_counter; keep raw milliseconds. summarize_latency() supplies linear
    percentiles at (n - 1) * q. Submission requires n_runs >= 20.
    Short-circuit request timing, RAG and output timing are outside this scope.
    """
    from src.experiment_support import summarize_latency

    if not test_inputs or type(n_runs) is not int or n_runs < 20:
        raise ValueError("Need clean inputs and at least 20 timed samples.")
    if analyzer is None or anonymizer is None:
        analyzer, anonymizer = setup_presidio()
    if rails is None:
        rails = setup_nemo_rails()

    async def measure():
        for i in range(2):
            text = test_inputs[i % len(test_inputs)]
            pii_scan(text, analyzer, anonymizer)
            await check_input_rail(text, rails)
        samples = []
        for i in range(n_runs):
            text = test_inputs[i % len(test_inputs)]
            t0 = time.perf_counter()
            pii_scan(text, analyzer, anonymizer)
            pii_ms = (time.perf_counter() - t0) * 1000
            t1 = time.perf_counter()
            await check_input_rail(text, rails)
            nemo_ms = (time.perf_counter() - t1) * 1000
            samples.append({"presidio_ms": pii_ms, "nemo_input_ms": nemo_ms,
                            "input_guard_ms": pii_ms + nemo_ms})
        return samples

    return summarize_latency(asyncio.run(measure()), warmup_runs=2)


# ─── Main ─────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    from scripts.run_experiments import main
    raise SystemExit(main(["--phase", "c", *sys.argv[1:]]))
