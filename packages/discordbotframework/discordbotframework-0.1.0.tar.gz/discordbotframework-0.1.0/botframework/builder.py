import os
import json
import base64

def rebuild_project(dump_file: str, target_dir: str):
    with open(dump_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    for file_info in data:
        path = file_info["path"]
        content = file_info["content"]
        is_binary = file_info.get("binary", False)

        full_path = os.path.join(target_dir, path)
        os.makedirs(os.path.dirname(full_path), exist_ok=True)

        if is_binary:
            content_bytes = base64.b64decode(content)
            with open(full_path, "wb") as f:
                f.write(content_bytes)
        else:
            with open(full_path, "w", encoding="utf-8") as f:
                f.write(content)

    print(f"Project rebuilt at {target_dir} ({len(data)} files)")