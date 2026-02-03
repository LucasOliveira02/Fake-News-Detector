def calculate_ai_confidence(score, source_type, details):
    """
    Calculates the algorithm's confidence in its AI detection decision.
    score: 0-100 (probability of AI)
    source_type: 'text', 'image', 'video', 'file'
    details: dictionary containing metadata like word_count, frames_analyzed, is_mock, etc.
    """
    
    # If using mock logic (Dev Mode / No API Key), confidence is extremely low
    if details.get("is_mock"):
        return 10

    confidence = 50 # Base confidence

    # 1. Extremity Boost / Uncertainty Penalty
    # If the model is "very sure" (near 0 or 100), boost confidence.
    # If it's near 50%, it's uncertain.
    if score > 90 or score < 10:
        confidence += 30
    elif 40 <= score <= 60:
        confidence -= 20

    # 2. Source-Specific Logic
    if source_type == "text":
        word_count = details.get("word_count", 0)
        if word_count > 150:
            confidence += 15
        elif word_count < 30:
            confidence -= 15

    elif source_type == "video" or source_type == "file":
        signals = details.get("signals", []) # Individual scores for frames/pages
        if len(signals) > 1:
            # Check for consistency
            is_consistent = all(s > 70 for s in signals) or all(s < 30 for s in signals)
            if is_consistent:
                confidence += 20
            else:
                # Conflicting signals across frames/pages
                confidence -= 25

    # 3. Image Logic
    if source_type == "image":
        # Image models can be brittle, but if high resolution or clear signals, we are confident.
        # Just use the extremities for now.
        pass

    # Ensure range 1-100
    return min(max(confidence, 1), 100)
