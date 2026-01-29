import os

def is_api_saved(selected_option: str, api_key: str) -> bool:
    parent_dir = os.path.dirname(os.getcwd())  
    halo_path = os.path.join(parent_dir, ".env")

    if not os.path.exists(halo_path):
        content = f'OPENAI_API_KEY="{api_key}"\nAPI_OPTION="{selected_option}"\n'
        with open(halo_path, "w") as f:
            f.write(content)

        return True
    return False
