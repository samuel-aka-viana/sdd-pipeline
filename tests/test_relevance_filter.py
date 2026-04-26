import numpy as np

from sdd.relevance_filter import RelevanceFilterSkill, ScoredUrl


def test_cosine_similarity_accepts_numpy_arrays():
    skill = RelevanceFilterSkill(memory=None)
    a = np.array([1.0, 2.0, 3.0], dtype=float)
    b = np.array([1.0, 2.0, 3.0], dtype=float)

    sim = skill._cosine_similarity(a, b)

    assert sim == 1.0


def test_apply_semantic_rerank_with_numpy_vectors():
    def embedding_fn(_texts):
        return [
            np.array([1.0, 0.0, 0.0], dtype=float),  # query
            np.array([1.0, 0.0, 0.0], dtype=float),  # doc 1
            np.array([0.0, 1.0, 0.0], dtype=float),  # doc 2
        ]

    skill = RelevanceFilterSkill(memory=None, embedding_fn=embedding_fn)
    scored = [
        ScoredUrl(url="https://docs.example/a", category="docs", rank=0),
        ScoredUrl(url="https://docs.example/b", category="docs", rank=0),
    ]

    reranked = skill.apply_semantic_rerank(scored, query="test")

    assert len(reranked) == 2
    assert reranked[0].similarity == 1.0
    assert reranked[1].similarity == 0.0
