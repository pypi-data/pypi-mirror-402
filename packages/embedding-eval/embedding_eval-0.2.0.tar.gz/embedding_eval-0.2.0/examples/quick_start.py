#!/usr/bin/env python3
"""
Quick Start Example for embedding-eval

This example demonstrates fair comparison of embedding models
with independent parameter optimization.
"""

from embedding_eval import run_fair_comparison

# Example document content
DOCUMENT = """
# Company Overview

Acme Corporation was founded in 1995 by John Smith and Jane Doe.
The company is headquartered in San Francisco, California.

## Products

Our flagship product is the Widget Pro, launched in 2020.
The Widget Pro has a battery life of 48 hours and weighs 250 grams.

## Financial Performance

In fiscal year 2023, Acme Corporation reported revenue of $50 million.
The gross margin was 65% and operating income was $12 million.

## Leadership

The current CEO is Sarah Johnson, who joined in 2018.
The CTO is Michael Chen, responsible for all technology initiatives.
"""

# Q&A pairs where answers appear VERBATIM in the document
QA_PAIRS = [
    {
        "question": "When was Acme Corporation founded?",
        "answer": "1995",
        "category": "exact",
    },
    {
        "question": "Who are the founders of Acme Corporation?",
        "answer": "John Smith and Jane Doe",
        "category": "exact",
    },
    {
        "question": "Where is the company headquartered?",
        "answer": "San Francisco, California",
        "category": "exact",
    },
    {
        "question": "What is the battery life of Widget Pro?",
        "answer": "48 hours",
        "category": "fine_detail",
    },
    {
        "question": "How much does Widget Pro weigh?",
        "answer": "250 grams",
        "category": "fine_detail",
    },
    {
        "question": "What was Acme's revenue in 2023?",
        "answer": "$50 million",
        "category": "exact",
    },
    {
        "question": "What is the company's gross margin?",
        "answer": "65%",
        "category": "fine_detail",
    },
    {
        "question": "Who is the CEO of Acme Corporation?",
        "answer": "Sarah Johnson",
        "category": "exact",
    },
    {
        "question": "When did Sarah Johnson join the company?",
        "answer": "2018",
        "category": "exact",
    },
    {
        "question": "What is Michael Chen's role?",
        "answer": "CTO",
        "category": "exact",
    },
]


def main():
    """Run fair comparison example."""
    print("=" * 60)
    print("embedding-eval: Fair Comparison Example")
    print("=" * 60)
    print(f"\nDocument length: {len(DOCUMENT)} chars")
    print(f"Q&A pairs: {len(QA_PAIRS)}")
    print("\nNote: For statistically meaningful results, use 80+ questions.")
    print("This example uses 10 questions for demonstration.\n")

    # Compare models with independent optimization
    # Using smaller grid for demo speed
    results = run_fair_comparison(
        models=["st:minilm", "st:bge-base"],  # Free, local models
        doc_content=DOCUMENT,
        qa_pairs=QA_PAIRS,
        chunk_sizes=[256, 512],  # Smaller grid for demo
        overlaps=[25, 50],
        top_ks=[5, 10],
        verbose=True,
    )

    # Show detailed results
    print("\n" + "=" * 60)
    print("DETAILED RESULTS")
    print("=" * 60)
    for r in results:
        print(f"\n{r.model_name}:")
        print(f"  Dimensions: {r.dimensions}")
        print(f"  Baseline: {r.baseline_accuracy:.1f}% ({r.baseline_passed}/{r.total_questions})")
        print(f"  Optimized: {r.best_accuracy:.1f}% ({r.best_passed}/{r.total_questions})")
        print(f"  Improvement: {r.improvement_pct:+.1f}pp")
        print(f"  95% CI: [{r.ci_lower:.1f}%, {r.ci_upper:.1f}%]")
        print(f"  Best params: {r.best_params}")
        print(f"  Configs tested: {r.configurations_tested}")
        print(f"  Time: {r.optimization_time_seconds:.1f}s")


if __name__ == "__main__":
    main()
