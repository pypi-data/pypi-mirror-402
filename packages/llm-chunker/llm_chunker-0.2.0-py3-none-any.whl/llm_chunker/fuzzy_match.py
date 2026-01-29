"""
Fuzzy matching utilities using rapidfuzz for high-performance text matching.
Falls back to difflib if rapidfuzz is not installed.
"""

# Try to import rapidfuzz for high-performance matching
try:
    from rapidfuzz import fuzz
    HAS_RAPIDFUZZ = True
except ImportError:
    from difflib import SequenceMatcher
    HAS_RAPIDFUZZ = False


def find_best_match(text: str, target: str, threshold: float = 0.8) -> int:
    """
    Find the best matching position for target in text using fuzzy matching.
    Falls back to fuzzy matching when exact match is not found (LLM hallucination tolerance).
    
    Uses rapidfuzz if available (100x faster), otherwise falls back to difflib.
    
    Args:
        text: The text to search in
        target: The string to search for
        threshold: Minimum similarity ratio (0.0 ~ 1.0)
    
    Returns:
        int: Position of best match, or -1 if not found
    """
    if not target:
        return -1
    
    # Edge case: target longer than text
    if len(target) > len(text):
        return -1
    
    # 1. Try exact match first (fastest)
    exact_pos = text.find(target)
    if exact_pos != -1:
        return exact_pos
    
    # 2. Try case-insensitive exact match
    lower_text = text.lower()
    lower_target = target.lower()
    case_insensitive_pos = lower_text.find(lower_target)
    if case_insensitive_pos != -1:
        return case_insensitive_pos
    
    # 3. Fuzzy matching
    if HAS_RAPIDFUZZ:
        return _rapidfuzz_match(text, target, threshold)
    else:
        return _difflib_match(text, target, threshold)


def _rapidfuzz_match(text: str, target: str, threshold: float) -> int:
    """
    High-performance fuzzy matching using rapidfuzz.
    Uses partial_ratio_alignment for substring matching.
    """
    target_len = len(target)
    threshold_score = threshold * 100  # rapidfuzz uses 0-100 scale
    
    best_pos = -1
    best_score = 0
    
    # Slide window with step optimization
    step = max(1, target_len // 10)  # Adaptive step size
    extra_window = max(5, target_len // 5)  # Adaptive extra window size

    for i in range(0, len(text) - target_len + 1, step):
        window = text[i:i + target_len + extra_window]  # Slightly larger window
        score = fuzz.partial_ratio(target, window)
        
        if score > best_score and score >= threshold_score:
            best_score = score
            best_pos = i
    
    # Fine-tune around best position
    if best_pos != -1:
        search_start = max(0, best_pos - step)
        search_end = min(len(text) - target_len + 1, best_pos + step)
        
        for i in range(search_start, search_end):
            window = text[i:i + target_len]
            score = fuzz.ratio(target, window)
            
            if score > best_score and score >= threshold_score:
                best_score = score
                best_pos = i
    
    return best_pos


def _difflib_match(text: str, target: str, threshold: float) -> int:
    """
    Fallback fuzzy matching using difflib (slower but always available).
    """
    target_len = len(target)
    
    if target_len < 5:
        # For very short targets, do simple sliding window
        return _sliding_window_match(text, target, threshold)
    
    # Use prefix filtering to narrow down candidates
    prefix_len = min(8, target_len // 2)
    prefix = target[:prefix_len].lower()
    
    candidates = []
    for i in range(len(text) - target_len + 1):
        window_prefix = text[i:i + prefix_len].lower()
        if _char_diff(window_prefix, prefix) <= 1:
            candidates.append(i)
    
    # If no candidates from prefix, fall back to sparse sampling
    if not candidates:
        candidates = list(range(0, len(text) - target_len + 1, 10))
    
    # Compare only at candidate positions
    best_pos, best_ratio = -1, 0
    for i in candidates:
        window = text[i:i + target_len]
        ratio = SequenceMatcher(None, window, target).ratio()
        if ratio > best_ratio and ratio >= threshold:
            best_ratio = ratio
            best_pos = i
    
    return best_pos


def _char_diff(s1: str, s2: str) -> int:
    """Count character differences between two strings of same length."""
    return sum(1 for a, b in zip(s1, s2) if a != b)


def _sliding_window_match(text: str, target: str, threshold: float) -> int:
    """Simple sliding window for short targets."""
    target_len = len(target)
    best_pos, best_ratio = -1, 0
    
    for i in range(len(text) - target_len + 1):
        window = text[i:i + target_len]
        ratio = SequenceMatcher(None, window, target).ratio()
        if ratio > best_ratio and ratio >= threshold:
            best_ratio = ratio
            best_pos = i
    
    return best_pos
