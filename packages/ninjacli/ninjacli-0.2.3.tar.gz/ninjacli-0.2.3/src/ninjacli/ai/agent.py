import re
from openai import OpenAI
from dotenv import load_dotenv
from ninjacli.utils.validators import OutputFormat
from ninjacli.core.message_history import message_history
from pydantic import ValidationError

load_dotenv()

def extract_json(text: str) -> str | None:
    """
    Extracts the first complete JSON object and sanitizes raw newlines 
    and unescaped quotes inside strings to prevent validation errors.
    """
    text = re.sub(r"```json|```", "", text, flags=re.IGNORECASE).strip()

    start_index = text.find('{')
    if start_index == -1:
        return None

    depth = 0
    in_string = False
    escape = False
    sanitized_chars = []

    for i in range(start_index, len(text)):
        char = text[i]
        
        if char == '"' and not escape:
            in_string = not in_string
        
        if char == '\\':
            escape = not escape
        else:
            escape = False

        if in_string:
            if char == '\n':
                sanitized_chars.append('\\n')
            elif char == '\r':
                continue
            else:
                sanitized_chars.append(char)
        else:
            sanitized_chars.append(char)

        if not in_string:
            if char == '{':
                depth += 1
            elif char == '}':
                depth -= 1
                if depth == 0:
                    return "".join(sanitized_chars)
    
    return None


def agent(ai_option: str, messages: list):
    """
    Main AI agent loop.
    Yields OutputFormat objects for Ninja CLI to process each step.
    """
    model = None
    api_base_url = None

    if ai_option == "openai":
        model = "gpt-4o"
    elif ai_option == "gemini":
        model = "gemini-3-flash-preview"
        api_base_url = "https://generativelanguage.googleapis.com/v1beta/openai/"
    elif ai_option == "openrouter":
        model = "xiaomi/mimo-v2-flash:free"
        api_base_url = "https://openrouter.ai/api/v1"

    client = OpenAI(base_url=api_base_url)

    response = client.chat.completions.create(
        model=model,
        messages=messages
    )

    raw = response.choices[0].message.content
    json_text = extract_json(raw)

    try:
        if json_text:
            parsed = OutputFormat.model_validate_json(json_text)
        else:
            parsed = OutputFormat(step="OUTPUT", content=raw)
    except ValidationError:
        try:
            fixed_json = re.sub(r'(?<=: ")(.*?)(?=", ")|(?<=: ")(.*?)(?="}$)', 
                                lambda m: m.group(0).replace('"', '\\"'), json_text, flags=re.DOTALL)
            fixed_json = re.sub(r'(?<=: ")(.*?)(?=", ")|(?<=: ")(.*?)(?="}$)', 
                                lambda m: m.group(0).replace('"', '\\"'), json_text, flags=re.DOTALL)
            parsed = OutputFormat.model_validate_json(fixed_json)
        except:
            parsed = OutputFormat(
                step="ERROR",
                content=f"Invalid JSON from AI.\nRaw output:\n{raw}"
            )

    yield parsed