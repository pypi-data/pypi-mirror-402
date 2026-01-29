
from ninjacli.cli.commands import execute_safely, directory_exists, file_exists, create_file, read_file, update_file, delete_file, create_directory, read_directory, update_directory, delete_directory, build_project, run_project

available_tools = {
    "execute_safely": execute_safely,
    "create_file": create_file,
    "read_file": read_file,
    "update_file": update_file,
    "delete_file": delete_file,
    "create_directory": create_directory,
    "read_directory": read_directory,
    "update_directory": update_directory,
    "delete_directory": delete_directory,
    "build_project": build_project,
    "run_project": run_project,
    "directory_exists": directory_exists,
    "file_exists": file_exists,
}