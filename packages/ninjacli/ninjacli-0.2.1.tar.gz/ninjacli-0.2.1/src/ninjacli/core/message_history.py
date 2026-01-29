from ninjacli.ai.prompts import INTRO_PROMPT, AVAILABLE_TOOLS_PROMPT, EXAMPLES_PROMPT, INTRO_PROMPT

message_history = [
    {
        "role": "system", "content": INTRO_PROMPT
    },
    {
        "role": "system", "content": AVAILABLE_TOOLS_PROMPT
    },
    {
        "role": "system", "content": EXAMPLES_PROMPT
    },
    {
        "role": "system", "content": INTRO_PROMPT
    },
]