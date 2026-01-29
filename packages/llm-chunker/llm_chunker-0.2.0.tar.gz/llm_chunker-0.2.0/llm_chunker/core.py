import logging
from typing import List, Tuple, Dict, Any, Optional
from tqdm import tqdm
from .text_utils import split_text_into_processing_segments
from .analyzer import TransitionAnalyzer
from .fuzzy_match import find_best_match

# ── Logger Setup ──
logger = logging.getLogger("llm_chunker")

# ── Default Constants (can be overridden in __init__) ──
DEFAULT_SIGNIFICANCE_THRESHOLD = 7
DEFAULT_MIN_CHUNK_GAP = 200
DEFAULT_FUZZY_MATCH_THRESHOLD = 0.8
DEFAULT_MAX_SEGMENT_SIZE = 5000  # Maximum characters per segment for LLM processing
DEFAULT_OVERLAP_SIZE = 400  # Characters to overlap between segments


class GenericChunker:
    def __init__(self,
                 analyzer: Optional[TransitionAnalyzer] = None,
                 model: Optional[str] = None,
                 significance_threshold: int = DEFAULT_SIGNIFICANCE_THRESHOLD,
                 min_chunk_gap: int = DEFAULT_MIN_CHUNK_GAP,
                 fuzzy_match_threshold: float = DEFAULT_FUZZY_MATCH_THRESHOLD,
                 max_segment_size: int = DEFAULT_MAX_SEGMENT_SIZE,
                 overlap_size: int = DEFAULT_OVERLAP_SIZE,
                 verbose: bool = False,
                 show_progress: bool = False):
        """
        Initialize the GenericChunker with configurable parameters.

        Args:
            analyzer: Instance of TransitionAnalyzer. If provided, 'model' is ignored.
            model: OpenAI model name (e.g., "gpt-4o"). Shortcut to create default analyzer.
            significance_threshold: Minimum significance score (1-10) for a transition point.
            min_chunk_gap: Minimum characters between chunk boundaries.
            fuzzy_match_threshold: Minimum similarity ratio for fuzzy text matching.
            max_segment_size: Maximum characters per segment for LLM processing.
            overlap_size: Characters to overlap between segments to catch boundary transitions.
            verbose: If True, enables INFO level logging. If False, only WARNING+.
            show_progress: If True, shows tqdm progress bar during processing.
        """
        # Configure logging based on verbose flag
        if verbose:
            logger.setLevel(logging.DEBUG)
            # Add handler if none exists
            if not logger.handlers:
                handler = logging.StreamHandler()
                handler.setFormatter(logging.Formatter('%(asctime)s [%(levelname)s] %(message)s', datefmt='%H:%M:%S'))
                logger.addHandler(handler)
        else:
            logger.setLevel(logging.WARNING)
        
        if analyzer is not None:
            self.analyzer = analyzer
        elif model is not None:
            self.analyzer = TransitionAnalyzer(model=model)
        else:
            self.analyzer = TransitionAnalyzer()
        
        self.significance_threshold = significance_threshold
        self.min_chunk_gap = min_chunk_gap
        self.fuzzy_match_threshold = fuzzy_match_threshold
        self.max_segment_size = max_segment_size
        self.overlap_size = overlap_size
        self.show_progress = show_progress

        logger.info(f"\n{'─'*50}")
        logger.info(f"GenericChunker 초기화")
        logger.info(f"  significance_threshold: {significance_threshold}")
        logger.info(f"  min_chunk_gap: {min_chunk_gap}")
        logger.info(f"  max_segment_size: {max_segment_size}")
        logger.info(f"  overlap_size: {overlap_size}")
        logger.info(f"{'─'*50}")

    def split_text(self, text: str) -> List[str]:
        """
        Splits the text into chunks based on the configured transition logic.
        
        Returns:
            List[str]: A list of text chunks.
        """
        if not text:
            logger.warning("[Chunker] Empty text provided")
            return []
        
        logger.info(f"\n{'═'*50}")
        logger.info(f"텍스트 처리 시작 ({len(text):,} 글자)")
        logger.info(f"{'═'*50}")
            
        # 1. Find all transition points
        all_points = self._find_transition_points(text)
        
        # 2. Handle no transition points case
        if not all_points:
            logger.warning("[Chunker] 전환점을 찾지 못했습니다")
            return [text]
        
        # 3. Slice the text based on these points
        chunks = []
        last_pos = 0
        
        for i, p in enumerate(all_points):
            pos = p["position_in_full_text"]
            if pos > last_pos:
                chunk = text[last_pos:pos].strip()
                if chunk:
                    chunks.append(chunk)
                last_pos = pos

        # Last chunk
        final_chunk = text[last_pos:].strip()
        if final_chunk:
            chunks.append(final_chunk)

        # Log chunk summary
        logger.info(f"\n{'═'*50}")
        logger.info(f"청크 생성 완료: {len(chunks)}개")
        logger.info(f"{'═'*50}")
        for i, c in enumerate(chunks):
            logger.info(f"  청크 {i+1}: {len(c):,} 글자")

        # Print chunk summary if show_progress is enabled
        if self.show_progress:
            self._print_chunks(chunks)

        return chunks

    def _print_chunks(self, chunks: List[str]) -> None:
        """Print chunk summary for user visibility."""
        print(f"\n총 {len(chunks)}개의 청크로 분할됨\n")

        for i, chunk in enumerate(chunks):
            print(f"\n{'='*50}")
            print(f"[청크 {i+1}] 길이: {len(chunk)} 글자")
            print(f"{'='*50}")
            if len(chunk) > 500:
                print(f"시작: {chunk[:300]}...")
                print(f"\n...끝: {chunk[-200:]}")
            else:
                print(chunk)

        # Statistics
        chunk_lengths = [len(c) for c in chunks]
        print(f"\n{'='*50}")
        print(f"청크 통계:")
        print(f"- 총 청크 수: {len(chunks)}")
        print(f"- 평균 길이: {sum(chunk_lengths) / len(chunk_lengths):.0f} 글자")
        print(f"- 최소 길이: {min(chunk_lengths)} 글자")
        print(f"- 최대 길이: {max(chunk_lengths)} 글자")

    def _find_transition_points(self, text: str) -> List[Dict[str, Any]]:
        """
        Internal method to detect turning points with improved filtering.
        """
        points = []
        seg_idx = 0
        
        # Get all segments first for progress bar
        segments = list(split_text_into_processing_segments(
            text,
            max_segment_size=self.max_segment_size,
            overlap_size=self.overlap_size
        ))
        
        # Iterate over segments with optional progress bar
        segment_iter = tqdm(segments, desc="🔍 Analyzing segments", disable=not self.show_progress)
        
        for seg, seg_start in segment_iter:
            seg_idx += 1
            logger.info(f"\n[세그먼트 {seg_idx}/{len(segments)}] {len(seg):,} 글자 (시작: {seg_start:,})")
            
            # Analyze segment with LLM
            analysis = self.analyzer.analyze_segment(seg)
            
            # Map relative positions to absolute positions
            for p in analysis.get("transition_points", []):
                snippet = p.get("start_text", "")[:50]
                if not snippet:
                    continue

                # Use fuzzy matching to handle LLM hallucination
                rel_pos = find_best_match(seg, snippet, self.fuzzy_match_threshold)
                if rel_pos == -1:
                    logger.debug(f"  ⚠ 텍스트 못찾음: '{snippet[:25]}...'")
                    continue

                abs_pos = seg_start + rel_pos

                # Duplicate check: skip if similar position already exists
                duplicate_threshold = max(100, self.overlap_size // 2)
                if any(abs(existing["position_in_full_text"] - abs_pos) < duplicate_threshold for existing in points):
                    logger.debug(f"  ⚠ 중복 스킵: pos={abs_pos:,}")
                    continue

                p["position_in_full_text"] = abs_pos
                points.append(p)
                logger.debug(f"  ✓ 전환점 추가: pos={abs_pos:,} | sig={p.get('significance', '?')}")

        # ── Filtering Pipeline ──
        logger.info(f"\n{'─'*50}")
        logger.info(f"필터링 시작 (원본: {len(points)}개)")

        # 1. Sort by position
        points.sort(key=lambda x: x["position_in_full_text"])

        # 2. Filter by significance
        high_sig_points = [p for p in points if p.get("significance", 0) >= self.significance_threshold]
        filtered_out = [p for p in points if p.get("significance", 0) < self.significance_threshold]

        if filtered_out:
            logger.debug(f"  중요도 미달로 제거:")
            for p in filtered_out:
                logger.debug(f"    ✗ sig={p.get('significance', 0)}: '{p.get('start_text', '')[:25]}...'")

        logger.info(f"  → 중요도 필터 ({self.significance_threshold}+): {len(high_sig_points)}개")

        # 3. Filter by minimum gap
        filtered = []
        last_pos = -float("inf")
        gap_removed = []

        for p in high_sig_points:
            pos = p["position_in_full_text"]
            if pos - last_pos >= self.min_chunk_gap:
                filtered.append(p)
                last_pos = pos
            else:
                gap_removed.append((pos, pos - last_pos))

        if gap_removed:
            logger.debug(f"  간격 미달로 제거:")
            for pos, gap in gap_removed:
                logger.debug(f"    ✗ pos={pos:,} (간격: {gap})")

        logger.info(f"  → 간격 필터 ({self.min_chunk_gap}+): {len(filtered)}개")
        logger.info(f"{'─'*50}")

        # Final summary
        logger.info(f"\n최종 전환점 {len(filtered)}개:")
        for i, p in enumerate(filtered):
            logger.info(f"  [{i+1}] pos={p['position_in_full_text']:,} | sig={p.get('significance', '?')} | '{p.get('start_text', '')[:30]}...'")
        
        if self.show_progress:
            print(f"✅ Found {len(filtered)} transition points")
        
        return filtered
