import unittest

import test._bootstrap  # noqa: F401

from agents.sentiment import sentiment_agent
from agents.toxicity import toxic_agent
from agents.spam import spam_agent
from agents.topic import topic_agent


class AgentFallbackTests(unittest.TestCase):
    def test_sentiment_fallback(self) -> None:
        scores = sentiment_agent._fallback_lexical_sentiment("bagus sekali")
        self.assertIn("positive", scores)
        label = sentiment_agent._label_from_scores(scores)
        self.assertIn(label, {"positive", "neutral", "negative"})

    def test_toxicity_fallback(self) -> None:
        scores = toxic_agent._fallback_lexical_scores("kamu bodoh")
        self.assertIn("toxic", scores)
        self.assertGreaterEqual(scores["toxic"], 0.0)

    def test_spam_pattern_signals(self) -> None:
        cfg = spam_agent.SpamAgentConfig()
        df = spam_agent.pd.DataFrame(
            [{"text": "cek http://spam.com http://spam.com", "author": "a"}]
        )
        df = spam_agent._ensure_schema(df, cfg)
        scores, reasons, _ = spam_agent._compute_pattern_signals(df, cfg)
        self.assertEqual(len(scores), 1)
        self.assertTrue(any("multiple_urls" in r for r in reasons))

    def test_topic_prompt_language(self) -> None:
        prompt = topic_agent._build_system_prompt()
        self.assertIn("Jangan gunakan judul/deskripsi video sama sekali", prompt)


if __name__ == "__main__":
    unittest.main()
