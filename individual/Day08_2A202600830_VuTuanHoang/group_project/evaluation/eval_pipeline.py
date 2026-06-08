"""
RAG Evaluation Pipeline.

Sử dụng DeepEval / RAGAS / TruLens để đánh giá chất lượng RAG pipeline.
Chọn 1 framework và implement đầy đủ.

Yêu cầu:
    1. Load golden_dataset.json (≥15 Q&A pairs)
    2. Chạy RAG pipeline trên từng question
    3. Evaluate với 4 metrics: faithfulness, relevance, context_recall, context_precision
    4. So sánh A/B ít nhất 2 configs
    5. Export results ra results.md
"""

import json
from pathlib import Path

GOLDEN_DATASET_PATH = Path(__file__).parent / "golden_dataset.json"
RESULTS_PATH = Path(__file__).parent / "results.md"


def load_golden_dataset() -> list[dict]:
    """Load golden dataset từ JSON file."""
    with open(GOLDEN_DATASET_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


# =============================================================================
# Option 1: DeepEval
# =============================================================================

def evaluate_with_deepeval(rag_pipeline, golden_dataset: list[dict]) -> dict:
    """
    Evaluate RAG pipeline sử dụng DeepEval.

    pip install deepeval
    """
    # TODO: Implement
    #
    # from deepeval import evaluate
    # from deepeval.metrics import (
    #     FaithfulnessMetric,
    #     AnswerRelevancyMetric,
    #     ContextualRecallMetric,
    #     ContextualPrecisionMetric,
    # )
    # from deepeval.test_case import LLMTestCase
    #
    # test_cases = []
    # for item in golden_dataset:
    #     result = rag_pipeline.generate_with_citation(item["question"])
    #     test_case = LLMTestCase(
    #         input=item["question"],
    #         actual_output=result["answer"],
    #         expected_output=item["expected_answer"],
    #         retrieval_context=[c["content"] for c in result["sources"]],
    #     )
    #     test_cases.append(test_case)
    #
    # metrics = [
    #     FaithfulnessMetric(threshold=0.7),
    #     AnswerRelevancyMetric(threshold=0.7),
    #     ContextualRecallMetric(threshold=0.7),
    #     ContextualPrecisionMetric(threshold=0.7),
    # ]
    #
    # results = evaluate(test_cases, metrics)
    # return results
    raise NotImplementedError("Implement evaluate_with_deepeval")


# =============================================================================
# Option 2: RAGAS
# =============================================================================

def evaluate_with_ragas(rag_pipeline, golden_dataset: list[dict]) -> dict:
    """
    Evaluate RAG pipeline sử dụng RAGAS.

    pip install ragas
    """
    # TODO: Implement
    #
    # from ragas import evaluate
    # from ragas.metrics import (
    #     faithfulness,
    #     answer_relevancy,
    #     context_recall,
    #     context_precision,
    # )
    # from datasets import Dataset
    #
    # eval_data = {"question": [], "answer": [], "contexts": [], "ground_truth": []}
    #
    # for item in golden_dataset:
    #     result = rag_pipeline.generate_with_citation(item["question"])
    #     eval_data["question"].append(item["question"])
    #     eval_data["answer"].append(result["answer"])
    #     eval_data["contexts"].append([c["content"] for c in result["sources"]])
    #     eval_data["ground_truth"].append(item["expected_answer"])
    #
    # dataset = Dataset.from_dict(eval_data)
    # result = evaluate(
    #     dataset,
    #     metrics=[faithfulness, answer_relevancy, context_recall, context_precision],
    # )
    # return result.to_pandas()
    raise NotImplementedError("Implement evaluate_with_ragas")


# =============================================================================
# Option 3: TruLens
# =============================================================================

def evaluate_with_trulens(rag_pipeline, golden_dataset: list[dict]) -> dict:
    """
    Evaluate RAG pipeline sử dụng TruLens.

    pip install trulens
    """
    # TODO: Implement
    #
    # from trulens.apps.custom import TruCustomApp
    # from trulens.core import Feedback
    # from trulens.providers.openai import OpenAI as TruOpenAI
    #
    # provider = TruOpenAI()
    #
    # f_faithfulness = Feedback(provider.groundedness_measure_with_cot_reasons).on_output()
    # f_relevance = Feedback(provider.relevance).on_input_output()
    # f_context_relevance = Feedback(provider.context_relevance).on_input()
    #
    # tru_rag = TruCustomApp(
    #     rag_pipeline,
    #     app_name="DrugLaw_RAG",
    #     feedbacks=[f_faithfulness, f_relevance, f_context_relevance],
    # )
    #
    # with tru_rag as recording:
    #     for item in golden_dataset:
    #         rag_pipeline.generate_with_citation(item["question"])
    #
    # # Dashboard: from trulens.dashboard import run_dashboard; run_dashboard()
    raise NotImplementedError("Implement evaluate_with_trulens")


# =============================================================================
# A/B Comparison
# =============================================================================

def compare_configs(rag_pipeline, golden_dataset: list[dict]):
    """
    So sánh A/B giữa ít nhất 2 configs.

    Gợi ý configs để so sánh:
    - Config A: hybrid search + reranking
    - Config B: dense-only (không reranking)
    - Config C: hybrid search + PageIndex fallback
    """
    # TODO: Implement A/B comparison
    #
    # configs = {
    #     "hybrid_rerank": {"use_reranking": True, "alpha": 0.5},
    #     "dense_only": {"use_reranking": False, "alpha": 1.0},
    # }
    #
    # results = {}
    # for config_name, params in configs.items():
    #     # Run eval with this config
    #     ...
    #     results[config_name] = scores
    #
    # return results
    raise NotImplementedError("Implement compare_configs")


# =============================================================================
# Export Results
# =============================================================================

def export_results(results: dict, comparison: dict):
    """Export evaluation results to results.md"""
    # TODO: Format and write results
    #
    # content = "# RAG Evaluation Results\n\n"
    # content += "## Overall Scores\n\n"
    # content += "| Metric | Score |\n|--------|-------|\n"
    # ...
    # content += "\n## A/B Comparison\n\n"
    # ...
    # content += "\n## Worst Performers\n\n"
    # ...
    # content += "\n## Recommendations\n\n"
    # ...
    #
    # RESULTS_PATH.write_text(content, encoding="utf-8")
    raise NotImplementedError("Implement export_results")


if __name__ == "__main__":
    golden_dataset = load_golden_dataset()
    print(f"Loaded {len(golden_dataset)} test cases")

    # TODO: Import your RAG pipeline
    # from src.task10_generation import generate_with_citation
    #
    # Chọn 1 framework:
    # results = evaluate_with_deepeval(pipeline, golden_dataset)
    # results = evaluate_with_ragas(pipeline, golden_dataset)
    # results = evaluate_with_trulens(pipeline, golden_dataset)
    #
    # comparison = compare_configs(pipeline, golden_dataset)
    # export_results(results, comparison)
    print("⚠ Implement evaluation logic and run again!")
