# embedding-eval

Fair embedding model evaluation with independent parameter optimization.

## Why This Package?

Most embedding comparisons are unfair because they use the same parameters for all models. This package implements a fair comparison methodology:

| Approach | Description | Fair? |
|----------|-------------|-------|
| **Unfair** | Optimize parameters for Model A, apply to all models | ❌ |
| **Fair** | Each model gets its own optimized parameters | ✅ |

## Key Features

- **Independent Optimization**: Each model gets its own best `chunk_size`, `overlap`, and `top_k`
- **Binary Evaluation**: Simple substring matching, no LLM cost, reproducible
- **Confidence Intervals**: Reports 95% CI using Wilson score
- **Minimal Dependencies**: Core functionality requires only `sentence-transformers` and `tiktoken`
- **No External Services**: InMemoryVectorStore requires no database setup

## Installation

```bash
pip install embedding-eval

# For OpenAI models
pip install embedding-eval[openai]
```

## Quick Start

```python
from embedding_eval import run_fair_comparison

# Your document content
doc_content = open("document.txt").read()

# Q&A pairs where answers appear VERBATIM in the document
qa_pairs = [
    {"question": "What is the capital of France?", "answer": "Paris"},
    {"question": "When was the company founded?", "answer": "1995"},
    # ... more pairs (recommend 80+ for statistical power)
]

# Compare models with independent optimization
results = run_fair_comparison(
    models=["st:bge-base", "st:minilm"],
    doc_content=doc_content,
    qa_pairs=qa_pairs,
)

# Results include baseline + optimized + confidence intervals
for r in results:
    print(f"{r.model_name}:")
    print(f"  Baseline: {r.baseline_accuracy:.1f}%")
    print(f"  Optimized: {r.best_accuracy:.1f}% (95% CI: [{r.ci_lower:.1f}%, {r.ci_upper:.1f}%])")
    print(f"  Best params: {r.best_params}")
```

## Methodology

### Fair Comparison = Independent Optimization

```
┌────────────────────────────────────────────────────────────────┐
│  FAIR COMPARISON METHODOLOGY                                   │
│                                                                │
│  For each model:                                               │
│    1. Grid search over chunk_size × overlap × top_k            │
│    2. Find best parameters for THIS model                      │
│    3. Report: baseline + optimized + 95% CI                    │
│                                                                │
│  Compare models using their respective best configurations     │
└────────────────────────────────────────────────────────────────┘
```

### Binary Evaluation

We use substring matching to check if the expected answer appears in retrieved chunks:

```python
from embedding_eval import BinaryEvaluator

evaluator = BinaryEvaluator()
score = evaluator.evaluate(
    question="What is the capital?",
    expected_answer="Paris",
    retrieved_chunks=["France is a country. Paris is its capital."]
)
print(score.score)  # 1.0 (answer found)
```

**Why binary evaluation?**
- Simple and reproducible
- No LLM cost ($0 vs ~$0.03/question for LLM evaluation)
- Proven effective for parameter optimization (see EDD-005)
- RAGAS and LLM evaluation add cost without improving decisions

### Statistical Requirements

| Sample Size | 95% CI Width | Can Detect |
|-------------|--------------|------------|
| 50 | ±11% | >22% differences |
| 80 | ±9% | >18% differences |
| 100 | ±8% | >16% differences |

**Recommendation**: Use 80+ questions with 20%+ multi-hop for meaningful comparisons.

## Q&A Fixture Format

```json
[
  {
    "question": "What does BATNA stand for?",
    "answer": "Best Alternative To a Negotiated Agreement",
    "category": "exact",
    "difficulty": "medium"
  }
]
```

**Important**: Answers must appear **verbatim** in the document.

### Question Categories

| Category | Description | Example |
|----------|-------------|---------|
| `exact` | Answer appears verbatim in document | "What year was the company founded?" → "1995" |
| `reformulated` | Question rephrased, same verbatim answer | "When did the company start?" → "1995" |
| `multi_hop` | Requires connecting multiple facts | "What is the phone number of the org that teaches X?" |
| `fine_detail` | Specific numbers, dates, codes | "What is the gross margin percentage?" → "65%" |
| `implicit` | Requires inference from document content | "Is the company profitable?" (inferred from financials) |
| `negation` | Asks what is NOT something | "Which technique is NOT used for divergence?" |

### Difficulty Levels

| Difficulty | Description | Typical Accuracy |
|------------|-------------|------------------|
| `easy` | Direct lookup, common terms | 95-100% |
| `medium` | Some vocabulary variation | 80-95% |
| `hard` | Multi-hop, specific details, vocabulary gaps | 60-85% |

### Fixture Guidelines

For statistically meaningful comparisons:

| Requirement | Minimum | Recommended |
|-------------|---------|-------------|
| Total questions | 50 | 80+ |
| Multi-hop questions | 10% | 20%+ |
| Hard questions | 30% | 40%+ |

**Why multi-hop matters**: Multi-hop questions are the primary differentiator between retrieval strategies. Simple exact-match questions often hit ceiling effects (100% accuracy across all strategies).

For detailed guidance, see [Creating Q&A Fixtures](docs/creating_fixtures.md).

## Model Specifications

| Format | Example | Description |
|--------|---------|-------------|
| `st:<model>` | `st:bge-base` | SentenceTransformers (free, local) |
| `openai:<model>` | `openai:text-embedding-3-small` | OpenAI API (requires key) |

### Recommended Models

| Use Case | Model | Accuracy | Cost |
|----------|-------|----------|------|
| **Best value** | `st:bge-base` | 94.4% | Free |
| Quality-first | `openai:text-embedding-3-small` | 97.3% | ~$0.02/1M tokens |
| Fast prototyping | `st:minilm` | 89.7% | Free |

## API Reference

### Core Functions

```python
# Compare multiple models
from embedding_eval import run_fair_comparison
results = run_fair_comparison(
    models=["st:bge-base", "st:minilm"],
    doc_content=text,
    qa_pairs=pairs,
    chunk_sizes=[256, 384, 512],  # optional
    overlaps=[25, 50, 100],       # optional
    top_ks=[5, 10, 15],           # optional
)

# Optimize single model
from embedding_eval import optimize_model
result = optimize_model(
    model_spec="st:bge-base",
    doc_content=text,
    qa_pairs=pairs,
)
```

### Components

```python
# Chunking
from embedding_eval.chunking import FixedSizeChunker
chunker = FixedSizeChunker(chunk_size=512, overlap=50)
chunks = chunker.chunk(document)

# Embedding
from embedding_eval.adapters.embedding import SentenceTransformerEmbedding
embedding = SentenceTransformerEmbedding(model="bge-base")
vectors = embedding.embed_documents(texts)

# Vector Store (no external deps)
from embedding_eval.adapters.vector import InMemoryVectorStore
store = InMemoryVectorStore()
store.connect()
store.create_collection("test", dimensions=768)
store.upsert("test", ids, embeddings, texts=texts)
results = store.search("test", query_embedding, top_k=10)

# Evaluation
from embedding_eval import BinaryEvaluator
evaluator = BinaryEvaluator()
score = evaluator.evaluate(question, answer, chunks)

# Fixture Validation
from embedding_eval import validate_fixture

result = validate_fixture(qa_pairs, doc_content)
print(result.summary)

if not result.is_valid:
    for issue in result.answer_issues:
        print(f"  {issue.answer}: {issue.issue_type}")
```

## CLI Usage

### Validate Fixtures

Validate your Q&A fixture before running evaluations:

```bash
# Basic validation (checks structure, distribution, thresholds)
embedding-eval validate --qa fixture.json

# With answer verification against document
embedding-eval validate --qa fixture.json --doc document.txt

# JSON output for programmatic use
embedding-eval validate --qa fixture.json --json

# Custom thresholds
embedding-eval validate --qa fixture.json \
    --min-questions 30 \
    --min-multihop 5 \
    --min-hard 20
```

Example output:
```
==================================================
FIXTURE VALIDATION REPORT
==================================================

Total questions: 80
Answers verified: 80/80
  ✓ All answers found verbatim
  ✓ No duplicate questions

Category Distribution:
  exact: 50.0% (40)
  multi_hop: 25.0% (20)
  fine_detail: 15.0% (12)
  reformulated: 10.0% (8)

Difficulty Distribution:
  easy: 15.0% (12)
  medium: 45.0% (36)
  hard: 40.0% (32)

Threshold Checks:
  ✓ Questions: 80 (≥80 recommended)
  ✓ Multi-hop: 25.0% (≥20% recommended)
  ✓ Hard: 40.0% (≥40% recommended)

==================================================
STATUS: ✓ VALID (meets minimum requirements)
==================================================
```

### Compare Models

Run fair comparison from the command line:

```bash
embedding-eval compare \
    --doc document.txt \
    --qa fixture.json \
    --models st:bge-base st:minilm \
    --output results.json
```

## Key Research Findings

Based on comprehensive evaluation (712 questions across 5 document types):

1. **Chunking matters most**: Section-aware chunking improved Q33 from rank 66 → rank 2 (more impact than any algorithm change)

2. **Recommended configuration**:
   ```python
   config = {
       "chunk_size": 512,
       "overlap": 50,
       "top_k": 10,
   }
   # Accuracy: 94.0% with BGE-base
   ```

3. **What NOT to do**:
   - Graph retrieval causes -4.6% to -4.9% regression on most documents
   - Small chunks (128 tokens) generalize poorly
   - Query expansion helps vocabulary mismatch but can hurt precision

## License

MIT

## Contributing

Contributions welcome! Please open an issue first to discuss proposed changes.
