import contextlib
import json
import os
import traceback


@contextlib.contextmanager
def capture_error_to_file(filename: str, suppress_error: bool = False):
    if not filename:
        yield
    else:
        try:
            yield
        except Exception as e:
            error_info = {"traceback": traceback.format_exc(), "error_message": str(e), "is_success": False}
            os.makedirs(os.path.dirname(filename), exist_ok=True)
            with open(filename, "w") as f:
                json.dump(error_info, f, indent=2)
            if not suppress_error:
                raise
