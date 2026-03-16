import json
import tempfile
import unittest
from unittest.mock import patch

import test._bootstrap  # noqa: F401

from pipeline import orchestrator


class OrchestratorE2ETests(unittest.TestCase):
    def test_orchestrator_runs_with_mocks(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch("pipeline.orchestrator.fetch_video_metadata") as mock_meta, \
                 patch("pipeline.orchestrator.fetch_youtube_comments") as mock_comments, \
                 patch("pipeline.orchestrator.run_eda") as mock_eda, \
                 patch("pipeline.orchestrator.run_spam_agent") as mock_spam, \
                 patch("pipeline.orchestrator.run_sentiment_agent") as mock_sentiment, \
                 patch("pipeline.orchestrator.run_toxic_agent") as mock_toxic, \
                 patch("pipeline.orchestrator.run_topic_agent") as mock_topic, \
                 patch("pipeline.orchestrator.merge_evidence_and_insights") as mock_merge:

                mock_meta.return_value = {"video_title": "T", "video_description": "D"}
                mock_comments.return_value = [
                    {"author": "a", "text": "hello", "published_at": None, "like_count": 1}
                ]
                mock_eda.return_value = {"total_comments": 1}
                mock_spam.return_value = {"results": [], "spam_comments": 0, "spam_ratio": 0.0}
                mock_sentiment.return_value = {"comment_level": [], "highlights": {}, "distribution": {}}
                mock_toxic.return_value = {"comment_level": [], "summary": {}, "top_toxic_comments": []}
                mock_topic.return_value = {"clusters": [], "cluster_summary": {}}
                mock_merge.return_value = {"evidence_snapshot": {}, "llm_insights": {"available": False}}

                result = orchestrator.run_orchestrator(
                    video_input="https://www.youtube.com/watch?v=YCLJz0TANaA",
                    api_key="key",
                    output_dir=tmpdir,
                )

                self.assertIn("video", result)
                self.assertIn("comments", result)
                self.assertIn("llm_insights", result)

                out_file = f"{tmpdir}/orchestrator_YCLJz0TANaA.json"
                with open(out_file, "r", encoding="utf-8") as f:
                    payload = json.load(f)
                self.assertEqual(payload["video"]["video_id"], "YCLJz0TANaA")


if __name__ == "__main__":
    unittest.main()
