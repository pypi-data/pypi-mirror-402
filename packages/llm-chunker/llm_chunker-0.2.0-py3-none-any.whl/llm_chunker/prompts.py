from typing import Callable

def get_default_prompt(segment: str) -> str:
    """
    Default prompt for detecting semantic changes or "turning points" in text.
    """
    return f"""
You must analyze the following text segment and identify points where the topic, mood, or narrative focus changes significantly.

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
""".strip()

def get_legal_prompt(segment: str) -> str:
    """
    Prompt specialized for legal document chunking.
    """
    return f"""
You are a 'Legislative Structuring Expert'. 
Your task is to segment the following legal text into semantic chunks that are optimal for a RAG (Retrieval-Augmented Generation) system. Analyze the following text and identify points where the legal topic, clause type, or subject usage changes significantly.

TEXT SEGMENT:
{segment}

Return a SINGLE JSON object in the following format (no markdown):
{{
  "transition_points": [
    {{
      "start_text": "Text snippet where the change begins (must match exactly)",
      "topic_before": "Legal context/article BEFORE this point",
      "topic_after": "Legal context/article AFTER this point",
      "significance": <1-10 integer>,
      "explanation": "Why this constitutes a legal section boundary"
    }}
  ]
}}

SIGNIFICANCE SCORING GUIDE:
- 1-3: Minor clause variations
- 4-6: Section transitions within same topic
- 7-10: Major legal topic changes (new article, different legal domain)

If no significant transitions are found, return {{ "transition_points": [] }}.
""".strip()
