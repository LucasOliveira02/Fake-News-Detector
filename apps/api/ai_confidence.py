def calculate_ai_confidence(score, source_type, details):
    """
    Calculates- [/] Debug static confidence score issue <!-- id: 27 -->
- [ ] Verify frontend state updates for confidence <!-- id: 28 -->
- [ ] Add backend response logging <!-- id: 29 -->source_type: 'text', 'image', 'video', 'file'
    details: dictionary containing metadata like word_count, frames_analyzed, is_mock, etc.
    """
    
    print(f"--- CONFIDENCE CALCULATION START ---")
    print(f"Inputs: score={score}, source_type={source_type}, details={details}")
    
    confidence = 50 # Base confidence

    if details.get("is_mock"):
        print("Detail: is_mock is TRUE, setting base to 25")
        confidence = 25 
    
    # 1. Extremity Boost / Uncertainty Penalty
    if score > 90 or score < 10:
        print(f"Boost: Score extremity ({score}) +30")
        confidence += 30
    elif 40 <= score <= 60:
        print(f"Penalty: Score uncertainty ({score}) -20")
        confidence -= 20

    # 2. Source-Specific Logic
    if source_type == "text":
        word_count = details.get("word_count", 0)
        print(f"Source: text, word_count={word_count}")
        if word_count > 150:
            print("Boost: word_count > 150 (+15)")
            confidence += 15
        elif word_count < 30:
            print("Penalty: word_count < 30 (-15)")
            confidence -= 15

    # ... other logic ...

    final_conf = min(max(confidence, 1), 100)
    print(f"FINAL CONFIDENCE: {final_conf}")
    print(f"--- CONFIDENCE CALCULATION END ---")
    return final_conf
