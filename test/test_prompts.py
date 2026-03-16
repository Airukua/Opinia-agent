import json
import unittest

import test._bootstrap  # noqa: F401

from agents.topic import topic_agent
from pipeline import evidence_merger


class PromptContractTests(unittest.TestCase):
    def test_topic_prompt_indonesian_and_generalization(self) -> None:
        prompt = topic_agent._build_system_prompt()
        self.assertIn("Jangan gunakan judul/deskripsi video sama sekali", prompt)
        self.assertIn("Utamakan generalisasi topik", prompt)
        self.assertIn("Rationale wajib merujuk ke komentar/keyword", prompt)

    def test_topic_payload_excludes_video_context(self) -> None:
        cfg = topic_agent.TopicAgentConfig()
        cluster_data = {
            "cluster_label": 1,
            "cluster_size": 3,
            "lda_keywords": ["alhamdulillah", "mantap"],
            "top_comments": [{"text": "Alhamdulillah", "like_count": 2}],
        }
        payload_str = topic_agent._prepare_llm_payload(cluster_data, cfg=cfg)
        payload = json.loads(payload_str)
        self.assertNotIn("video_context", payload)
        self.assertIn("top_comments", payload)
        self.assertIn("lda_keywords", payload)

    def test_llm_insights_system_prompt_indonesian(self) -> None:
        prompt = evidence_merger._build_system_prompt()
        self.assertIn("Bahasa Indonesia", prompt)
        self.assertIn("JSON yang valid", prompt)


if __name__ == "__main__":
    unittest.main()
