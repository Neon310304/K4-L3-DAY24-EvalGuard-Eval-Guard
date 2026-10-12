"""RAGAS 0.1.x adapter: four real metrics and explicit evaluator provenance."""
from __future__ import annotations

from types import SimpleNamespace
import math

from config import (API_TIMEOUT_SECONDS, EVALUATOR_EMBEDDING_MODEL, EVALUATOR_MODEL,
                    OPENAI_API_KEY, OPENAI_BASE_URL)


def evaluate_ragas(questions, answers, contexts, ground_truths):
    if not questions or len({len(questions), len(answers), len(contexts), len(ground_truths)}) != 1:
        raise ValueError("RAGAS requires four nonempty aligned lists.")
    if not OPENAI_API_KEY:
        raise ValueError("Configure the provider API key in .env before evaluating.")
    from datasets import Dataset
    from langchain_openai import ChatOpenAI, OpenAIEmbeddings
    from ragas import evaluate
    from ragas.metrics import answer_relevancy, context_precision, context_recall, faithfulness
    from ragas.run_config import RunConfig

    llm = ChatOpenAI(model=EVALUATOR_MODEL, temperature=0, api_key=OPENAI_API_KEY,
                     base_url=OPENAI_BASE_URL, timeout=API_TIMEOUT_SECONDS)
    embeddings = OpenAIEmbeddings(model=EVALUATOR_EMBEDDING_MODEL, api_key=OPENAI_API_KEY,
                                  base_url=OPENAI_BASE_URL, request_timeout=API_TIMEOUT_SECONDS,
                                  check_embedding_ctx_length=False)
    dataset = Dataset.from_dict({"question": questions, "answer": answers,
                                 "contexts": contexts, "ground_truth": ground_truths})
    result = evaluate(dataset, metrics=[faithfulness, answer_relevancy, context_precision, context_recall],
                      llm=llm, embeddings=embeddings, raise_exceptions=True,
                      run_config=RunConfig(timeout=int(API_TIMEOUT_SECONDS), max_workers=4, max_retries=2))
    names = ("faithfulness", "answer_relevancy", "context_precision", "context_recall")
    rows = []
    for record in result.to_pandas().to_dict(orient="records"):
        values = {name: float(record[name]) for name in names}
        if any(not math.isfinite(v) or not 0 <= v <= 1 for v in values.values()):
            raise ValueError("RAGAS returned invalid metrics; no fabricated replacement is permitted.")
        rows.append(SimpleNamespace(**values))
    return {"per_question": rows, "metadata": {
        "evaluator_models": [EVALUATOR_MODEL, EVALUATOR_EMBEDDING_MODEL],
    }}
