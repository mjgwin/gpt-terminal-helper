import os
import sys
import re
import subprocess
import platform
import json

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

term_debug = True

def term_print(output_text, color):
    print(colored(f"terminal-helper > {output_text}", color))
    
def term_input(input_text, color):
    return input(colored(f"terminal-helper > {input_text}", color))

def is_valid_command(command_info):
    keys = command_info.get("arguments", {}).keys()
    return command_info.get("command", "") != "" and "body" in keys 
    
def run_python(arguments):
    body = arguments.get("body", "")
    if body:
        stdout_new = StringIO()
        with redirect_stdout(stdout_new):
            exec(body)
        term_print(f"Execute python done with response: {stdout_new.getvalue()}", "cyan")
        
def process_message(commands):
    if not commands:
        return
    for command_info in commands:
        if is_valid_command(command_info):
            command = command_info.get("command", "")
            arguments = command_info.get("arguments", {})
            if command == "run_python":
                run_python(arguments)
        else:
            term_print(f"Error, unable to process command: {json.dumps(command_info)}")

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
DO NOT ADD ANY OTHER COMMENTS BESIDES THE COMMANDS SO THE JSON IS ABLE TO BE PARSED
Each command will have the needed arguments with additional information for the objective.
The allowed arguments for each command are mapped below:
{str(ALLOWED_ARGUMENTS_MAP)}
PYTHON CODE MUST HAVE AN OUTPUT TO INFORM THE USER OF ITS RESULT.
The mandatory response format must be valid JSON with no other text allowed. It must be formatted like below: \n
{str(RESPONSE_FORMAT)} \n
DO NOT INCLUDE ANY EXTRA TEXT BEFORE OR AFTER THE RESPONSE.
"""

HELP_MESSAGE = "Commands include: \n > (clear_mem: Clear internal memory) \n > (print_mem: Display internal memory) \n > (quit: Exit application) \n > (write_mem: Write memory to log file)"

if __name__ == "__main__":
    
    running = True
    
    work_dir = os.getenv("WORK_DIR")

    if work_dir is None or not work_dir:
        work_dir = os.path.join(Path.home(), "terminal-helper")
        if not os.path.exists(work_dir):
            os.makedirs(work_dir)

    term_print(f"Working directory is {work_dir}", "cyan")
    
    memory.create_if_empty()
    
    try:
        os.chdir(work_dir)
    except FileNotFoundError:
        term_print("Directory doesn't exist. Set WORK_DIR to an existing directory or leave it blank.", "red")
        sys.exit(0)
    
    while running:
        
        objective = term_input("Enter objective, help for more commands: ", "cyan")
        
        if objective == "quit":
            break
        elif objective == "help":
            term_print(HELP_MESSAGE, "cyan")
            continue
        elif objective == "clear_mem":
            memory.clear_memory()
            continue
        elif objective == "print_mem":
            memory.print_memory()
            continue
        elif objective == "clear_mem":
            memory.write_memory_to_file("log.txt")
            continue
        
        memory.add_conversation("user", objective)
        
        with Spinner():
            try:
                response = openai.ChatCompletion.create(
                    model="gpt-3.5-turbo",
                    messages = [
                        {"role": "system", "content": SYSTEM_MESSAGE},
                        {"role": "user", "content": f"OBJECTIVE:{objective}"},
                        {"role": "user", "content": f"CONTEXT:\n{memory.get_recent_conversations()}"},
                        {"role": "user", "content": f"INSTRUCTIONS:\n{INSTRUCTIONS}"},
                    ],
                    max_tokens=1000
                )
            except Exception as e:
                term_print("Error accessing the OpenAI API: " + str(e), "red")
                response = {"error": "unable to access api"}
                sys.exit(0)
        
        print("")
        
        
        try:
            response_message = response['choices'][0]['message']['content']
        except Exception as e:
            response_message = {"error": "unable to access api"}
            
        parsed_response = response_message.replace("```", "").strip()
        #TODO Parse response so json loads can work
        print(f"Before: {parsed_response}")
        response_message = json.loads(parsed_response)
        commands = response_message.get("commands", [])
        for command in commands:
            command["arguments"] = eval(command.get("arguments", {}))
        
        if term_debug:
            term_print(f"Response: {json.dumps(response_message)}", "cyan")
         
        if "error" not in response_message.keys():
            memory.add_conversation("assistant", response_message)
            process_message(commands)
            
        

    term_print("Thanks for using terminal-helper!", "cyan")
