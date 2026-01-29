"""Universal LLM evaluation for ingested content.

Provides content quality assessment on every ingest operation.
Two evaluation modes based on whether topic is provided:

Mode A (topic provided):
    - quality_score, quality_summary (always)
    - topic_relevance_score, topic_relevance_summary, topic_provided

Mode B (no topic):
    - quality_score, quality_summary only
    - topic_relevance_* fields are NULL (never inferred)

Design principle: Evaluation is advisory metadata only, never blocks ingestion.
"""

import json
import logging
import os
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from openai import OpenAI

from src.core.config_loader import get_instance_config

logger = logging.getLogger(__name__)


@dataclass
class EvaluationResult:
    """Result of LLM content evaluation."""

    # Always populated
    quality_score: float  # 0.0-1.0
    quality_summary: str

    # Only when topic provided (None otherwise)
    topic_relevance_score: Optional[float]
    topic_relevance_summary: Optional[str]
    topic_provided: Optional[str]  # The topic caller provided for evaluation

    # Metadata
    model: str
    timestamp: datetime


async def evaluate_content(
    content: str,
    collection_name: str,
    collection_description: str,
    topic: str = None,
    max_preview_chars: int = 4000,
) -> EvaluationResult:
    """
    Evaluate content quality using LLM. Advisory only, never blocks ingestion.

    Mode A (topic provided):
        - Assesses quality AND topic relevance
        - Returns topic_relevance_score, topic_relevance_summary, topic_provided

    Mode B (no topic):
        - Assesses quality only
        - topic_relevance_* fields are NULL
        - Does NOT infer a topic from content or collection

    Args:
        content: The text content to evaluate
        collection_name: Name of the target collection
        collection_description: Description of the collection's purpose
        topic: Optional topic for relevance scoring (Mode A vs Mode B)
        max_preview_chars: Max chars of content to send to LLM

    Returns:
        EvaluationResult with quality and optional topic relevance scores

    Note:
        Called for EVERY ingest operation (dry run and real).
        Evaluation NEVER blocks ingestion - it's advisory metadata only.
    """
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        # Return neutral evaluation if no API key (shouldn't happen in prod)
        logger.warning("OPENAI_API_KEY not found for content evaluation")
        return EvaluationResult(
            quality_score=0.5,
            quality_summary="Evaluation skipped: API key not configured",
            topic_relevance_score=0.5 if topic else None,
            topic_relevance_summary="Evaluation skipped" if topic else None,
            topic_provided=topic,
            model="none",
            timestamp=datetime.utcnow(),
        )

    # Load evaluation configuration with fallbacks
    try:
        config = get_instance_config()
        eval_model = config.get("eval_model", config.get("dry_run_model", "gpt-4o-mini"))
        eval_temperature = float(config.get("eval_temperature", config.get("dry_run_temperature", 0.1)))
        eval_max_tokens = int(config.get("eval_max_tokens", 1000))
    except Exception:
        eval_model = "gpt-4o-mini"
        eval_temperature = 0.1
        eval_max_tokens = 1000

    client = OpenAI(api_key=api_key)

    # Truncate content for evaluation
    content_preview = content[:max_preview_chars]
    if len(content) > max_preview_chars:
        content_preview += "\n\n[Content truncated for evaluation...]"

    # Build prompt based on mode
    if topic:
        # Mode A: Quality + Topic Relevance
        system_prompt = """You are evaluating content for ingestion into a knowledge base.
You will assess QUALITY and TOPIC RELEVANCE.

QUALITY SCORING (0.0-1.0):
Assess the content's overall quality based on:
- Clarity: Is it well-written and easy to understand?
- Structure: Is it well-organized with logical flow?
- Informativeness: Does it provide useful, substantive information?
- Completeness: Does it cover its subject adequately?

Score ranges:
- 0.80-1.00: Excellent - clear, well-structured, highly informative
- 0.60-0.79: Good - solid content with minor issues
- 0.40-0.59: Moderate - usable but has notable gaps or clarity issues
- 0.20-0.39: Poor - significant quality issues
- 0.00-0.19: Very poor - nearly unusable

TOPIC RELEVANCE SCORING (0.0-1.0):
Assess how relevant the content is to the specified topic:
- 0.80-1.00: Highly relevant - topic is the main focus
- 0.60-0.79: Relevant - topic is covered substantially
- 0.40-0.59: Moderately relevant - topic is addressed but not primary focus
- 0.20-0.39: Marginally relevant - topic mentioned briefly or tangentially
- 0.00-0.19: Not relevant - topic not meaningfully covered

Output ONLY valid JSON:
{
    "quality_score": float,
    "quality_summary": "1-2 sentence explanation of quality assessment",
    "topic_relevance_score": float,
    "topic_relevance_summary": "1-2 sentence explanation of topic relevance"
}"""

        user_prompt = f"""Collection: {collection_name}
Collection purpose: {collection_description}
Evaluation topic: {topic}

Content to evaluate:
{content_preview}

Evaluate the content's quality and relevance to the topic."""

    else:
        # Mode B: Quality only (no topic inference)
        system_prompt = """You are evaluating content for ingestion into a knowledge base.
You will assess QUALITY ONLY. Do NOT evaluate topic relevance.

QUALITY SCORING (0.0-1.0):
Assess the content's overall quality based on:
- Clarity: Is it well-written and easy to understand?
- Structure: Is it well-organized with logical flow?
- Informativeness: Does it provide useful, substantive information?
- Completeness: Does it cover its subject adequately?

Score ranges:
- 0.80-1.00: Excellent - clear, well-structured, highly informative
- 0.60-0.79: Good - solid content with minor issues
- 0.40-0.59: Moderate - usable but has notable gaps or clarity issues
- 0.20-0.39: Poor - significant quality issues
- 0.00-0.19: Very poor - nearly unusable

Output ONLY valid JSON:
{
    "quality_score": float,
    "quality_summary": "1-2 sentence explanation of quality assessment"
}"""

        user_prompt = f"""Collection: {collection_name}
Collection purpose: {collection_description}

Content to evaluate:
{content_preview}

Evaluate the content's quality."""

    try:
        response = client.chat.completions.create(
            model=eval_model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=eval_temperature,
            max_completion_tokens=eval_max_tokens,
        )

        # Parse response
        response_text = response.choices[0].message.content.strip()

        # Handle potential markdown code blocks
        if response_text.startswith("```"):
            lines = response_text.split("\n")
            response_text = "\n".join(lines[1:-1])

        eval_data = json.loads(response_text)

        # Build result
        quality_score = float(eval_data.get("quality_score", 0.5))
        quality_summary = eval_data.get("quality_summary", "No summary provided")

        # Topic relevance only if topic was provided
        if topic:
            topic_relevance_score = float(eval_data.get("topic_relevance_score", 0.5))
            topic_relevance_summary = eval_data.get("topic_relevance_summary", "No summary provided")
        else:
            topic_relevance_score = None
            topic_relevance_summary = None

        logger.info(
            f"Content evaluation complete: quality={quality_score:.2f}"
            + (f", topic_relevance={topic_relevance_score:.2f}" if topic else "")
        )

        return EvaluationResult(
            quality_score=quality_score,
            quality_summary=quality_summary,
            topic_relevance_score=topic_relevance_score,
            topic_relevance_summary=topic_relevance_summary,
            topic_provided=topic,
            model=eval_model,
            timestamp=datetime.utcnow(),
        )

    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse evaluation response: {e}")
        return EvaluationResult(
            quality_score=0.5,
            quality_summary="Evaluation response could not be parsed",
            topic_relevance_score=0.5 if topic else None,
            topic_relevance_summary="Evaluation response could not be parsed" if topic else None,
            topic_provided=topic,
            model=eval_model,
            timestamp=datetime.utcnow(),
        )

    except Exception as e:
        logger.error(f"Content evaluation failed: {e}")
        return EvaluationResult(
            quality_score=0.5,
            quality_summary=f"Evaluation failed: {str(e)[:100]}",
            topic_relevance_score=0.5 if topic else None,
            topic_relevance_summary=f"Evaluation failed: {str(e)[:100]}" if topic else None,
            topic_provided=topic,
            model=eval_model,
            timestamp=datetime.utcnow(),
        )
