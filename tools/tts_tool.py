# SRE-Optimized Build: TTS Tool Stub
import json

BUILTIN_TTS_PROVIDERS = []

def check_tts_requirements() -> bool:
    return False

def text_to_speech_tool(text: str, **kwargs) -> str:
    return json.dumps({"success": False, "error": "TTS is disabled in SRE build."})

def _strip_markdown_for_tts(text: str) -> str:
    return text
