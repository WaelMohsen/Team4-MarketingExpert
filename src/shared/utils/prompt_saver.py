import os
import json
import re
from typing import List, Dict, Any, Optional

def _format_content(content: str) -> str:
    """
    Format the content string to be more readable in a text file.
    Tries to pretty-print JSON blocks found inside the text.
    """
    if not content:
        return ""

    # Try to find JSON blocks and pretty-print them
    def replace_json(match):
        try:
            obj = json.loads(match.group(0))
            return json.dumps(obj, indent=2, ensure_ascii=False)
        except:
            return match.group(0)

    # Regex to find JSON-like blocks (very basic)
    # This looks for content between { } or [ ]
    # We use a non-greedy match and verify it's valid JSON
    # This is better than nothing
    formatted = re.sub(r'(\{[\s\S]*?\}|\[[\s\S]*?\])', replace_json, content)
    
    return formatted

def save_llm_prompt(
    messages: List[Dict[str, str]],
    output_dir: str,
    filename_prefix: str = "prompt"
) -> Optional[str]:
    """
    Saves the LLM messages to a structured text file for maximum readability.
    
    Args:
        messages: List of message dictionaries sent to the LLM.
        output_dir: Directory where the prompt should be saved.
        filename_prefix: Prefix for the filename (e.g., 'analysis_prompt').
        
    Returns:
        The path to the saved file, or None if saving failed.
    """
    try:
        if not os.path.exists(output_dir):
            os.makedirs(output_dir, exist_ok=True)
            
        filename = f"{filename_prefix}.txt"
        file_path = os.path.join(output_dir, filename)
        
        counter = 1
        while os.path.exists(file_path):
            file_path = os.path.join(output_dir, f"{filename_prefix}_{counter}.txt")
            counter += 1

        with open(file_path, "w", encoding="utf-8") as f:
            for i, msg in enumerate(messages):
                role = msg.get("role", "unknown").upper()
                content = msg.get("content", "")
                
                f.write(f"{'='*20} {role} MESSAGE {'='*20}\n")
                f.write(_format_content(content))
                f.write("\n\n")
                
            f.write(f"{'='*57}\n")
            
        return file_path
    except Exception as e:
        import logging
        logging.getLogger(__name__).warning(f"Failed to save LLM prompt: {e}")
        return None
