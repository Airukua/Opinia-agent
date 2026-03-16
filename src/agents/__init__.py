"""Multi-agent modules for comment analysis pipeline."""

__all__ = []

try:
    from agents.EDA import EDAConfig, run_eda, run_eda_from_csv

    __all__.extend(["EDAConfig", "run_eda", "run_eda_from_csv"])
except Exception:  # pragma: no cover - optional dependency boundary
    pass

try:
    from agents.topic import TopicAgentConfig, run_topic_agent, run_topic_agent_from_csv

    __all__.extend(["TopicAgentConfig", "run_topic_agent", "run_topic_agent_from_csv"])
except Exception:  # pragma: no cover - optional dependency boundary
    pass

try:
    from agents.spam import SpamAgentConfig, run_spam_agent, run_spam_agent_from_csv

    __all__.extend(["SpamAgentConfig", "run_spam_agent", "run_spam_agent_from_csv"])
except Exception:  # pragma: no cover - optional dependency boundary
    pass

try:
    from agents.sentiment import (
        SentimentAgentConfig,
        run_sentiment_agent,
        run_sentiment_agent_from_csv,
    )

    __all__.extend(
        ["SentimentAgentConfig", "run_sentiment_agent", "run_sentiment_agent_from_csv"]
    )
except Exception:  # pragma: no cover - optional dependency boundary
    pass

try:
    from agents.toxicity import ToxicAgentConfig, run_toxic_agent, run_toxic_agent_from_csv

    __all__.extend(["ToxicAgentConfig", "run_toxic_agent", "run_toxic_agent_from_csv"])
except Exception:  # pragma: no cover - optional dependency boundary
    pass
