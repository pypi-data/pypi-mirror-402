import subprocess, shlex, os

FORBIDDEN_CMDS = {"rm", "del", "format", "sudo", "chmod", "chown"}
EXIT_COMMANDS = {"exit", "quit", "bye", "stop", "leave", "ctrl+c"}

def execute_safely(cmd_str: str, allow_delete: bool = False):
    """
       Common method for executing commands with conditional delete permission.
    """
    try:
        args = shlex.split(cmd_str)
    except ValueError as e:
        return f"Shell Parse Error: {str(e)}"
    
    if not args:
        return "No command provided"
    
    cmd_name = args[0].lower()

    if cmd_name in FORBIDDEN_CMDS:
        if cmd_name in {"rm", "del"} and allow_delete:
            pass 
        else:
            return f"Access Denied: {cmd_name} is a restricted command."
    
    try: 
        exit_code = os.system(cmd_str)
        return f"Command executed with exit code: {exit_code}"
    except Exception as e:
        return str(e)
    

def create_file(cmd_str: str):
    """ This command creates a file """ 
    return execute_safely(cmd_str)

def read_file(cmd_str: str):
    """ This command reads a file """
    return execute_safely(cmd_str)

def update_file(cmd_str: str):
    """ This command updates a file """
    return execute_safely(cmd_str)

def delete_file(cmd_str: str):
    """ This command deletes a file """
    return execute_safely(cmd_str, allow_delete=True)

def create_directory(cmd_str: str):
    """ This command creates a directory """
    return execute_safely(cmd_str)

def read_directory(cmd_str: str):
    """ This command lists contents of a directory """
    return execute_safely(cmd_str)

def update_directory(cmd_str: str):
    """ This command updates a directory (e.g., renames it) """
    return execute_safely(cmd_str)

def directory_exists(cmd_str: str):
    """ This command checks if a directory exists """
    try:
        tokens = shlex.split(cmd_str)
        dir_path = tokens[-1] if tokens else ""
    except:
        return False
        
    if not dir_path:
        return "No directory path provided"
    return os.path.isdir(dir_path)

def file_exists(cmd_str: str) -> bool:
    if not cmd_str or not cmd_str.strip():
        return False 

    try:
        tokens = shlex.split(cmd_str)
        file_path = tokens[-1] if tokens else ""
    except:
        return False
    
    if not file_path:
        return False
    
    return os.path.isfile(file_path)

def delete_directory(cmd_str: str):
    """ This command deletes a directory """
    return execute_safely(cmd_str, allow_delete=True)

def run_project(cmd_str: str):
    """ This command runs a project """
    return execute_safely(cmd_str)

def build_project(cmd_str: str):
    """ This command builds a project """
    return execute_safely(cmd_str)