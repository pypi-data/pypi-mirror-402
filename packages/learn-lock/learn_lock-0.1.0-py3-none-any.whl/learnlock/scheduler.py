"""SM-2 Spaced Repetition Scheduler."""

from datetime import datetime, timezone, timedelta

from . import config
from . import storage


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def update_after_review(concept_id: int, score: int) -> dict:
    """Update progress after a review based on score.
    
    SM-2 Algorithm:
    - score >= SCORE_PASS_THRESHOLD: Pass, increase interval
    - score < SCORE_PASS_THRESHOLD: Fail, reset interval
    
    Args:
        concept_id: The concept that was reviewed
        score: Score from SCORE_MIN to SCORE_MAX
        
    Returns:
        Updated progress info dict
    """
    progress = storage.get_progress(concept_id)
    if not progress:
        raise ValueError(f"No progress found for concept {concept_id}")
    
    # Clamp score to valid range
    score = max(config.SCORE_MIN, min(config.SCORE_MAX, score))
    
    ease = progress["ease_factor"]
    interval = progress["interval_days"]
    review_count = progress["review_count"]
    
    if score >= config.SCORE_PASS_THRESHOLD:
        # Passed - increase interval using SM-2
        if review_count == 0:
            interval = config.SM2_INITIAL_INTERVAL
        elif review_count == 1:
            interval = 6.0
        else:
            interval = interval * ease
        
        # Update ease factor based on score
        # SM-2 formula: EF' = EF + (0.1 - (5-q) * (0.08 + (5-q) * 0.02))
        ease = ease + (0.1 - (config.SCORE_MAX - score) * (0.08 + (config.SCORE_MAX - score) * 0.02))
        ease = max(config.SM2_MIN_EASE, ease)
        review_count += 1
    else:
        # Failed - reset
        review_count = 0
        interval = config.SM2_INITIAL_INTERVAL
        ease = max(config.SM2_MIN_EASE, ease - 0.2)
    
    # Cap interval
    interval = min(config.SM2_MAX_INTERVAL, max(config.SM2_INITIAL_INTERVAL, interval))
    
    due_date = _utcnow() + timedelta(days=interval)
    
    storage.update_progress(
        concept_id=concept_id,
        ease_factor=ease,
        interval_days=interval,
        due_date=due_date,
        review_count=review_count,
        last_score=score
    )
    
    return {
        "ease_factor": round(ease, 2),
        "interval_days": round(interval, 1),
        "due_date": due_date.isoformat(),
        "review_count": review_count,
        "next_review": _format_interval(interval),
        "passed": score >= config.SCORE_PASS_THRESHOLD
    }


def _format_interval(days: float) -> str:
    """Format interval as human-readable string."""
    if days < 1:
        return "today"
    elif days == 1:
        return "tomorrow"
    elif days < 7:
        return f"in {int(days)} days"
    elif days < 30:
        weeks = int(days / 7)
        return f"in {weeks} week{'s' if weeks > 1 else ''}"
    elif days < 365:
        months = int(days / 30)
        return f"in {months} month{'s' if months > 1 else ''}"
    else:
        return f"in {int(days)} days"


def get_next_due():
    """Get the next concept due for review.
    
    Returns:
        Concept dict with progress info, or None if nothing due
    """
    due = storage.get_due_concepts(limit=1)
    return due[0] if due else None


def get_all_due() -> list[dict]:
    """Get all concepts due for review."""
    return storage.get_due_concepts()


def get_study_summary() -> dict:
    """Get summary of study status."""
    stats = storage.get_stats()
    
    return {
        "due_now": stats["due_now"],
        "total_concepts": stats["total_concepts"],
        "total_reviews": stats["total_reviews"],
        "mastered": stats["mastered"],
        "avg_score": stats["avg_score"],
        "skipped": stats["skipped_concepts"],
    }
