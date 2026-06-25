import os
import json

JUMPS_PATH = os.path.expanduser("~/.navi/jumps.json")

def _load():
    """Load jumps list from disk. Returns [] if file missing or invalid."""
    try:
        with open(JUMPS_PATH, "r") as f:
            data = json.load(f)
            return data if isinstance(data, list) else []
    except (FileNotFoundError, json.JSONDecodeError):
        return []

def _save(jumps):
    """Write jumps list to disk."""
    os.makedirs(os.path.dirname(JUMPS_PATH), exist_ok=True)
    with open(JUMPS_PATH, "w") as f:
        json.dump(jumps, f, indent=2)

def list_jumps():
    """Return all saved jumps as a list of dicts: {name, desc, path}."""
    return _load()

def find_jump(name):
    """Return the jump dict matching name, or None."""
    for j in _load():
        if j.get("name") == name:
            return j
    return None

def add_jump(name, desc, path):
    """Add or overwrite a jump. Returns (success, error_message)."""
    jumps = _load()
    # Overwrite if name already exists
    jumps = [j for j in jumps if j.get("name") != name]
    jumps.append({"name": name, "desc": desc, "path": path})
    try:
        _save(jumps)
        return True, None
    except Exception as e:
        return False, str(e)

def delete_jump(name):
    """Delete a jump by name. Returns (success, error_message)."""
    jumps = _load()
    new_jumps = [j for j in jumps if j.get("name") != name]
    if len(new_jumps) == len(jumps):
        return False, f"No jump named '{name}'"
    try:
        _save(new_jumps)
        return True, None
    except Exception as e:
        return False, str(e)