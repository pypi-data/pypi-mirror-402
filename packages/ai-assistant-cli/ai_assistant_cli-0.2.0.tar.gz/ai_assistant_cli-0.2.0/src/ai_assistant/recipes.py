import json
import time
from uuid import uuid4
from .config import RECIPES_FILE


def load_recipes():
    """Load all saved CLI recipes."""
    if not RECIPES_FILE.exists():
        return []

    try:
        return json.loads(RECIPES_FILE.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return []


def save_recipe(name: str, command: str, tags=None):
    """Save a new CLI recipe."""
    if tags is None:
        tags = []

    recipes = load_recipes()

    recipes.append({
        "id": str(uuid4()),
        "name": name.strip(),
        "command": command.strip(),
        "tags": tags,
        "created_at": time.strftime("%Y-%m-%d %H:%M:%S"),
    })

    RECIPES_FILE.write_text(
        json.dumps(recipes, indent=2, ensure_ascii=False),
        encoding="utf-8"
    )
import json
import time
from uuid import uuid4
from .config import RECIPES_FILE


def load_recipes():
    """Load all saved CLI recipes."""
    if not RECIPES_FILE.exists():
        return []

    try:
        return json.loads(RECIPES_FILE.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return []


def save_recipe(name: str, command: str, tags=None):
    """Save a new CLI recipe."""
    if tags is None:
        tags = []

    recipes = load_recipes()

    recipes.append({
        "id": str(uuid4()),
        "name": name.strip(),
        "command": command.strip(),
        "tags": tags,
        "created_at": time.strftime("%Y-%m-%d %H:%M:%S"),
    })

    RECIPES_FILE.write_text(
        json.dumps(recipes, indent=2, ensure_ascii=False),
        encoding="utf-8"
    )
