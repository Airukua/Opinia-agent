import unittest

import test._bootstrap  # noqa: F401

from pipeline.evidence_merger import (
    EvidenceMergeConfig,
    build_comment_records,
    build_evidence_snapshot,
    merge_evidence_and_insights,
)


class EvidenceMergerTests(unittest.TestCase):
    def test_build_comment_records_merges_signals(self) -> None:
        comments = [
            {"comment_id": "c1", "text": "hello", "author": "a", "published_at": None, "like_count": 1},
            {"comment_id": "c2", "text": "spam link", "author": "b", "published_at": None, "like_count": 0},
        ]
        spam = {"results": [{"comment_id": "c2", "label": "spam", "spam_score": 0.9, "reason": "link"}]}
        sentiment = {"comment_level": [{"comment_id": "c1", "sentiment": "positive", "confidence": 0.7}]}
        toxic = {"comment_level": [{"comment_id": "c2", "toxicity_label": "toxic", "toxicity_score": 0.8, "flag": "toxic"}]}

        merged = build_comment_records(comments, spam, sentiment, toxic, limit=10)
        self.assertEqual(len(merged), 2)
        self.assertEqual(merged[0]["sentiment"]["label"], "positive")
        self.assertEqual(merged[1]["spam"]["label"], "spam")
        self.assertEqual(merged[1]["toxicity"]["label"], "toxic")

    def test_build_evidence_snapshot_structure(self) -> None:
        snapshot = build_evidence_snapshot(
            video={"video_id": "v1"},
            comments_total=2,
            eda_result={"total_comments": 2},
            spam_result={"results": [], "spam_comments": 0, "spam_ratio": 0.0, "total_comments": 2},
            sentiment_result={"total_comments": 2, "distribution": {}, "highlights": {}},
            toxic_result={"summary": {"toxic_comments": 0}, "top_toxic_comments": []},
            topic_result={"cluster_summary": {}, "clusters": []},
            config=EvidenceMergeConfig(),
        )
        self.assertIn("video", snapshot)
        self.assertIn("comment_totals", snapshot)
        self.assertIn("topics", snapshot)

    def test_merge_evidence_llm_disabled(self) -> None:
        payload = merge_evidence_and_insights(
            video={"video_id": "v1"},
            comments=[],
            eda_result={},
            spam_result={"results": []},
            sentiment_result={"highlights": {}},
            toxic_result={"summary": {}, "top_toxic_comments": []},
            topic_result={"cluster_summary": {}, "clusters": []},
            config=EvidenceMergeConfig(llm_enabled=False),
        )
        self.assertEqual(payload["llm_insights"]["available"], False)


if __name__ == "__main__":
    unittest.main()
