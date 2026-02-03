import re

def extract_ai_markers(text: str) -> list:
    """
    Identifies common linguistic markers and tropes found in AI-generated text.
    """
    markers = []
    lower_text = text.lower()
    
    # 1. AI Tropes / Over-used Words
    tropes = [
        "delve", "pivotal", "meticulous", "comprehensive", 
        "unveil", "vibrant", "tapestry", "ever-evolving",
        "bustling", "plethora", "not only, but also"
    ]
    for trope in tropes:
        if trope in lower_text:
            markers.append(f"AI Trope: '{trope}'")
            
    # 2. AI Templates / Disclaimers
    templates = [
        "as an ai", "as a language model", "it is important to note",
        "in conclusion", "to summarize", "on the other hand",
        "firstly", "secondly", "furthermore"
    ]
    for template in templates:
        if template in lower_text:
            markers.append(f"AI Structure: '{template}'")

    # 3. Formalism / Indirectness
    formal_markers = [
        "could be argued", "it is widely believed", "one might consider"
    ]
    for f in formal_markers:
        if f in lower_text:
            markers.append(f"Formalism: '{f}'")

    # 4. Repetitive sentence starts (Very simple check)
    sentences = re.split(r'[.!?]+', text)
    starts = [s.strip().split()[0].lower() for s in sentences if len(s.strip().split()) > 0]
    if len(starts) > 3:
        from collections import Counter
        counts = Counter(starts)
        for word, count in counts.items():
            if count > 2 and word not in ["the", "a", "an", "this", "it"]:
                markers.append(f"Repetitive start: '{word}'")

    return list(set(markers))[:5] # Return top 5 unique markers
