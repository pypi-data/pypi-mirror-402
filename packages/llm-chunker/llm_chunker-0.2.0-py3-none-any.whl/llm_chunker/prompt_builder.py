"""
프롬프트 빌더 - 커스텀 프롬프트를 생성하는 유틸리티
"""
from typing import Callable, Optional


class PromptBuilder:
    """
    커스텀 프롬프트를 생성하는 빌더 클래스.

    Examples:
        >>> prompt = PromptBuilder.create(
        ...     domain="legal document",
        ...     find="clause changes"
        ... )
    """
    @classmethod
    def create(
        cls,
        domain: str = "text",
        find: str = "semantic changes",
        custom_instruction: Optional[str] = None
    ) -> Callable[[str], str]:

        def prompt_generator(segment: str) -> str:
            prompt = f"""
You must analyze the following {domain} and identify points where {find}.

TEXT SEGMENT:
{segment}

Return a SINGLE JSON object in the following format (no markdown):
{{
  "transition_points": [
    {{
      "start_text": "Text snippet where the change begins (exact quote from the text)",
      "topic_before": "Summary of the topic/mood BEFORE this point",
      "topic_after": "Summary of the topic/mood AFTER this point",
      "significance": <1-10 integer>,
      "explanation": "Brief explanation of why this is a transition point"
    }}
  ]
}}

SIGNIFICANCE SCORING GUIDE:
- 1-3: Minor shifts (subtle mood change, small topic drift)
- 4-6: Moderate transitions (clear topic change, notable mood shift)
- 7-10: Major turning points (dramatic reversal, critical plot point, complete tone change)

If no significant transitions are found, return {{ "transition_points": [] }}.
"""
            if custom_instruction:
                prompt = prompt.rstrip() + f"\n\nADDITIONAL INSTRUCTION: {custom_instruction}\n"

            return prompt.strip()

        return prompt_generator
