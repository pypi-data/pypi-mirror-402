import nltk
from typing import Generator, Tuple

# Ensure NLTK punkt tokenizer is available
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt', quiet=True)
try:
    nltk.data.find('tokenizers/punkt_tab')
except LookupError:
    nltk.download('punkt_tab', quiet=True)

def split_text_into_processing_segments(
    text: str, 
    max_segment_size: int = 5000,
    overlap_size: int = 400
) -> Generator[Tuple[str, int], None, None]:
    """
    Splits text into processing segments while respecting sentence boundaries.
    
    Args:
        text: The full text to split.
        max_segment_size: Maximum characters per segment (default: 2600 for optimal LLM context).
        overlap_size: Number of characters to overlap between segments (default: 200).
        
    Yields:
        Tuple of (segment_text, start_index)
    """
    n = len(text)
    if n <= max_segment_size:
        yield text, 0
        return

    start = 0
    while start < n:
        end = min(start + max_segment_size, n)
        
        # Adjust end to avoid cutting sentences in the middle
        if end < n:
            # Search in the last 20% of the segment
            search_start = max(start + int(max_segment_size * 0.8), start)
            # Look a bit beyond 'end' to find sentence completion if possible
            search_limit = min(end + 200, n)
            search_text = text[search_start:search_limit]
            
            try:
                sentences = nltk.sent_tokenize(search_text)
                if sentences:
                    best_end = end
                    # Find the last complete sentence that fits within the limit
                    cumulative_len = 0
                    last_valid_end = None
                    for sentence in sentences:
                        # Find this sentence's position in search_text
                        sent_start = search_text.find(sentence, cumulative_len)
                        if sent_start == -1:
                            continue
                        sent_end = sent_start + len(sentence)
                        abs_end = search_start + sent_end
                        # Check if this sentence ending is within valid range
                        if start < abs_end <= start + max_segment_size + 200:
                            last_valid_end = abs_end
                        cumulative_len = sent_end
                    if last_valid_end:
                        best_end = last_valid_end
                    end = best_end
            except Exception:
                # Fallback to hard cut if tokenization fails
                pass

        yield text[start:end], start
        
        if end == n:
            break
            
        # Determine next start position with overlap
        # Prioritize overlap_size, but ensure minimum progress to avoid infinite loop
        next_start = end - overlap_size
        min_progress = max(overlap_size, 100)  # At least move by overlap_size or 100 chars
        start = max(start + min_progress, next_start)
