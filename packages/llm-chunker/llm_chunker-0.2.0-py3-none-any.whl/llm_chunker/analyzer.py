import json
import time
import os
import logging
from typing import Dict, Any, Callable, Optional
from llm_chunker.prompts import get_default_prompt

# Try to import json_repair for robust JSON parsing
try:
    import json_repair
    HAS_JSON_REPAIR = True
except ImportError:
    HAS_JSON_REPAIR = False

# ── Logger Setup ──
logger = logging.getLogger("llm_chunker")

try:
    from openai import OpenAI
    HAS_OPENAI = True
except ImportError:
    HAS_OPENAI = False


def create_openai_caller(model: str = "gpt-5-nano") -> Callable[[str], str]:
    """
    Factory function to create an OpenAI LLM caller with a specific model.
    
    Args:
        model: The OpenAI model to use (e.g., "gpt-4o", "gpt-5-nano", "gpt-3.5-turbo")
    
    Returns:
        Callable[[str], str]: A function that takes a prompt and returns the LLM response.
    
    Example:
        >>> analyzer = TransitionAnalyzer(
        ...     prompt_generator=get_default_prompt,
        ...     llm_caller=create_openai_caller("gpt-5-nano")
        ... )
    """
    def caller(prompt: str) -> str:
        if not HAS_OPENAI:
            raise ImportError("OpenAI library is not installed. Please run 'pip install openai'.")

        api_key = os.environ.get("OPENAI_API_KEY")
        if not api_key:
            raise ValueError(
                "OPENAI_API_KEY environment variable is not set.\n"
                "Set it via: export OPENAI_API_KEY='your-key'\n"
            )

        client = OpenAI(api_key=api_key)

        try:
            logger.debug(f"  LLM 요청 중... (모델: {model})")

            if model.startswith("gpt-5"):
                response = client.chat.completions.create(
                    model=model,
                    messages=[{"role": "user", "content": prompt}]
                )
            else:
                response = client.chat.completions.create(
                    model=model,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.0
                )

            content = response.choices[0].message.content
            logger.debug(f"  LLM 응답 수신 ({len(content):,} 글자)")
            return content
        except Exception as e:
            logger.error(f"  LLM API 오류: {e}")
            raise RuntimeError(f"OpenAI API Call Failed: {e}")

    return caller


# ── Legacy functions for backward compatibility ──
def openai_llm_caller(prompt: str) -> str:
    """
    Default OpenAI caller using env var OPENAI_MODEL or 'gpt-4o'.
    For custom models, use create_openai_caller(model_name) instead.
    """
    model_name = os.environ.get("OPENAI_MODEL", "gpt-4o")
    return create_openai_caller(model_name)(prompt)


# ──────────────────────────────────────────────────────────────
# [Configuration]
# ──────────────────────────────────────────────────────────────
DEFAULT_LLM_CALLER = openai_llm_caller 


def sanitize_json_output(raw_text: str) -> str:
    """
    Cleans up potential markdown formatting from LLM output.
    """
    text = raw_text.strip()
    if text.startswith("```"):
        # Remove first line (```json or ```)
        parts = text.split("\n", 1)
        if len(parts) > 1:
            text = parts[1]
        # Remove last line (```)
        if text.endswith("```"):
            text = text.rsplit("\n", 1)[0]
    return text.strip()


def _extract_transition_points(data: Dict[str, Any]) -> Dict[str, Any]:
    """Extract transition points from LLM response."""
    return {"transition_points": data.get("transition_points", [])}


class TransitionAnalyzer:
    def __init__(self,
                 prompt_generator: Optional[Callable[[str], str]] = None,
                 model: Optional[str] = None):
        """
        Initialize the TransitionAnalyzer.

        Args:
            prompt_generator: Function that generates the prompt for a text segment.
                              If None, uses get_default_prompt.
            model: OpenAI model name (e.g., "gpt-4o", "gpt-5-nano").
                   If None, uses env var OPENAI_MODEL or defaults to "gpt-4o".

        Examples:
            # Simplest usage (env var OPENAI_MODEL or gpt-4o)
            >>> analyzer = TransitionAnalyzer()

            # Specifying model directly
            >>> analyzer = TransitionAnalyzer(model="gpt-4o")

            # Using custom prompt
            >>> analyzer = TransitionAnalyzer(
            ...     prompt_generator=get_legal_prompt,
            ...     model="gpt-4o"
            ... )
        """
        self.prompt_generator = prompt_generator or get_default_prompt

        if model:
            self.llm_caller = create_openai_caller(model=model)
        else:
            self.llm_caller = DEFAULT_LLM_CALLER

    def analyze_segment(self, segment: str) -> Dict[str, Any]:
        prompt = self.prompt_generator(segment)

        for attempt in range(3):
            try:
                raw_response = self.llm_caller(prompt)
                cleaned_json = sanitize_json_output(raw_response)

                try:
                    if HAS_JSON_REPAIR:
                        data = json_repair.loads(cleaned_json)
                    else:
                        data = json.loads(cleaned_json)
                    result = _extract_transition_points(data)

                    tp_count = len(result['transition_points'])
                    logger.info(f"  → LLM 응답: {tp_count}개 전환점 발견")

                    for i, tp in enumerate(result['transition_points']):
                        logger.debug(f"    [{i+1}] sig={tp.get('significance', '?')} | '{tp.get('start_text', '')[:25]}...'")

                    return result

                except (json.JSONDecodeError, Exception) as e:
                    logger.warning(f"  JSON 파싱 오류 (시도 {attempt+1}/3): {e}")

            except Exception as e:
                logger.error(f"  LLM 오류 (시도 {attempt+1}/3): {e}")

            time.sleep(1)

        logger.warning("  모든 시도 실패, 빈 결과 반환")
        return {"transition_points": []}
