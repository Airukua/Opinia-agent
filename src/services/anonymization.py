import pandas as pd
from typing import List, Dict
from src.utils.logger import get_logger

logger = get_logger(__name__)


def build_global_author_mapping(file_paths: List[str]) -> Dict[str, str]:
    """Builds a deterministic global anonymization map for authors.

    Args:
        file_paths: CSV paths that contain an ``author`` column.

    Returns:
        Mapping of original author names to anonymized labels
        in the format ``user_<index>``.

    Example usage:
        >>> author_map = build_global_author_mapping(
        ...     ["scrapper/video_a.csv", "scrapper/video_b.csv"]
        ... )
        >>> isinstance(author_map, dict)
        True
    """
    logger.info("Building global author mapping from %d files", len(file_paths))
    unique_authors = set()

    for path in file_paths:
        df = pd.read_csv(path)
        authors = df["author"].dropna().unique()
        unique_authors.update(authors)
        logger.debug("Collected authors from %s current_unique=%d", path, len(unique_authors))

    mapping = {author: f"user_{i + 1}" for i, author in enumerate(sorted(unique_authors))}
    logger.info("Global author mapping created with %d unique authors", len(mapping))
    return mapping


def apply_anonymization(file_path: str, author_map: Dict[str, str]) -> None:
    """Replaces author names in one CSV file with anonymized labels.

    Args:
        file_path: Path to target CSV file.
        author_map: Mapping produced by ``build_global_author_mapping``.

    Example usage:
        >>> mapping = {"Alice": "user_1", "Bob": "user_2"}
        >>> apply_anonymization("scrapper/video_a.csv", mapping)
    """
    logger.info("Applying anonymization to %s", file_path)
    df = pd.read_csv(file_path)
    df["author"] = df["author"].map(author_map)
    df.to_csv(file_path, index=False)
    logger.info("Anonymized file saved: %s", file_path)


def anonymize_authors_globally(file_paths: List[str]) -> Dict[str, str]:
    """Applies one global anonymization mapping across multiple CSV files.

    Args:
        file_paths: CSV paths to anonymize.

    Returns:
        The global mapping used for anonymization.

    Example usage:
        >>> files = ["scrapper/video_a.csv", "scrapper/video_b.csv"]
        >>> mapping = anonymize_authors_globally(files)
        >>> len(mapping) >= 0
        True
    """
    logger.info("Starting global anonymization")
    author_map = build_global_author_mapping(file_paths)

    for path in file_paths:
        apply_anonymization(path, author_map)

    logger.info("Completed global anonymization for %d files", len(file_paths))
    return author_map
