import os, json
from dotenv import load_dotenv
from ninjacli.ai.agent import agent
from ninjacli.ui.intro import (
    header_display, prompt_display, api_option_display, 
    display_plan, display_tool_call, display_tool_result, 
    display_output, ask_restriction_confirmation
)
from ninjacli.cli.tools import available_tools, file_exists
from ninjacli.core.message_history import message_history
from ninjacli.utils.api_management import is_api_saved
from ninjacli.cli.commands import EXIT_COMMANDS

load_dotenv()

ALWAYS_ALLOW = False

def main():
    global ALWAYS_ALLOW
    header_display()
    
    if not file_exists("../.env"):
        user_option, api_key = api_option_display()
        if not is_api_saved(user_option, api_key):
            print("API_NOT_SAVED")
            return
        saved_ai_option = user_option
    else:
        saved_ai_option = os.getenv("API_OPTION")

    while True:
        user_input = prompt_display()

        if user_input.strip().lower() in EXIT_COMMANDS or user_input.strip().lower() in ["bye", "exit"]:
            print("👋 Exiting Ninja CLI... Sending CTRL+C (2x)")
            break

        message_history.append({"role": "user", "content": user_input})
        
        task_in_progress = True
        while task_in_progress:
            with display_tool_call("AI Brain", "Thinking..."):
                try:
                    steps = list(agent(saved_ai_option, message_history))
                except Exception as e:
                    display_output(f"Critical Agent Error: {str(e)}")
                    break

            for step in steps:
                message_history.append({"role": "assistant", "content": json.dumps(step.model_dump())})
                
                if step.step == "PLAN":
                    display_plan(step.content)

                elif step.step == "TOOL":
                    tool_name = step.tool
                    tool_input = step.input
                    
                    is_restricted = any(kw in tool_input for kw in ["rm -rf", "/", "sudo", "del "])
                    if is_restricted and not ALWAYS_ALLOW:
                        choice = ask_restriction_confirmation(tool_input)
                        if choice == "always":
                            ALWAYS_ALLOW = True
                        elif choice == "n":
                            display_output("Command skipped by user.")
                            task_in_progress = False
                            break

                    if tool_name in available_tools:
                        with display_tool_call(tool_name, tool_input):
                            try:
                                result = available_tools[tool_name](tool_input)
                                display_tool_result(tool_name, result)
                            except Exception as e:
                                result = f"Tool Execution Error: {str(e)}"
                                display_output(f"[bold red]Error:[/bold red] {result}")
                        
                        message_history.append({
                            "role": "assistant",
                            "content": json.dumps({
                                "step": "OBSERVE", "tool": tool_name,
                                "input": tool_input, "output": result
                            })
                        })
                    else:
                        error_msg = f"Error: Tool '{tool_name}' not found."
                        display_output(error_msg)
                        task_in_progress = False

                elif step.step == "ERROR":
                    display_output(f"[bold red]Error:[/bold red] {step.content}")
                    task_in_progress = False

                elif step.step == "OUTPUT":
                    display_output(step.content)
                    task_in_progress = False

if __name__ == "__main__":
    main()