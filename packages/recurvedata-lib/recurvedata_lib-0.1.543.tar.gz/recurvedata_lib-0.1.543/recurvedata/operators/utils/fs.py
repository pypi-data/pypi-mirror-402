import os.path


def get_exist_path(candidate_paths: list[str]) -> str:
    for path in candidate_paths:
        if not path:
            continue
        path = os.path.expanduser(path)
        if os.path.exists(path):
            return path
