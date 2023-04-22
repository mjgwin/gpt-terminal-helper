import os
import sys
import re
import subprocess
import platform

from io import StringIO
from contextlib import redirect_stdout
from pathlib import Path

from dotenv import load_dotenv
from termcolor import colored
import openai
from duckduckgo_search import ddg
from spinner import Spinner
import colorama
import memory

colorama.init()

def term_print(input, color):
    print(colored(f"terminal-helper > {input}", color))

operating_system = platform.platform()

load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

SYSTEM_MESSAGE = f"You are an autonomous terminal agent running on {operating_system}."
ALLOWED_COMMANDS = ["run_python", "run_shell", "message_user"]
COMMAND_FORMAT = {"command": "command_name", "arguments": {"argument_key": "argument_value"}}
ALLOWED_ARGUMENTS_MAP = {
    "run_python": ["body"],
    "run_shell": ["body"],
    "message_user": ["body"]
}
RESPONSE_FORMAT = {
    "commands": [
        {"command": "run_python", "arguments": {"body": "print('Hello World')"}},
        {"command": "run_shell", "arguments": {"body": "mkdir test && touch test/main.py"}},
        {"command": "message_user", "arguments": {"body": "The answer to your question is: [response]"}}
    ]
}
INSTRUCTIONS = f"""
Carefully think about which of the following commands will help the user accomplish their objective.
Your currently supported and allowed commands are: {str(ALLOWED_COMMANDS)}. \n
The command format is: {str(COMMAND_FORMAT)}. \n
You will provide a list of commands in your response to complete the objective.
Each command will have the needed arguments with additional information for the objective.
The allowed arguments for each command are mapped below:
{str(ALLOWED_ARGUMENTS_MAP)}
The mandatory response format must be valid JSON with no other text allowed. It must be formatted like below: \n
{str(RESPONSE_FORMAT)} \n
DO NOT INCLUDE EXTRA TEXT BEFORE OR AFTER THE RESPONSE.
"""

if __name__ == "__main__":
    
    running = True
    
    work_dir = os.getenv("WORK_DIR")

    if work_dir is None or not work_dir:
        work_dir = os.path.join(Path.home(), "terminal-helper")
        if not os.path.exists(work_dir):
            os.makedirs(work_dir)

    term_print(f"Working directory is {work_dir}", "cyan")
    
    try:
        os.chdir(work_dir)
    except FileNotFoundError:
        term_print("Directory doesn't exist. Set WORK_DIR to an existing directory or leave it blank.", "red")
        sys.exit(0)
    
    while running:
        
        objective = input(colored("terminal-helper > Enter objective, help for more commands: ", "cyan"))
        
        if objective == "quit":
            break
        
        with Spinner():
            try:
                response = openai.ChatCompletion.create(
                    model="gpt-3.5-turbo",
                    messages = [
                        {"role": "system", "content": SYSTEM_MESSAGE},
                        {"role": "user", "content": f"OBJECTIVE:{objective}"},
                        {"role": "user", "content": f"CONTEXT:\n{memory.get_recent_conversations()}"},
                        {"role": "user", "content": f"INSTRUCTIONS:\n{INSTRUCTIONS}"},
                    ])
            except Exception as e:
                term_print("Error accessing the OpenAI API: " + str(e), "red")
                sys.exit(0)
        

        term_print("Thanks for using terminal-helper!", "cyan")
