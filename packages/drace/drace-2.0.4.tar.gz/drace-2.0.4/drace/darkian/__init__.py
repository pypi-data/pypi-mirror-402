# ======================= STANDARDS =========================
from typing import Callable
from pathlib import Path
import importlib
import os

# ========================= LOCALS ==========================
from drace.types import Context, Dict


def get_rules(ignore: tuple[str], only: list[str]
             ) -> list[Callable[[Context], list[Dict]]]:
    """
    Dynamically discover and load all callable linting rule
    functions from the 'drace/darkian' subdirectories
    (organized by series).

    Each rule is expected to:
      - Reside in a .py file named descriptively (excluding
        underscores or dot-prefixed).
      - Contain a function starting with `check_`.
      - Return a list of Dicts when called with a Context.

    Args:
        ignore: A tuple of rule names (uppercase, no 'check_'
                prefix) to exclude.
        only: A list of specific rule names to load. If
              non-empty, all others are skipped.

    Returns:
        A list of functions that take a Context and return a
        list of Dicts.
    """
    rules   = []
    pvt     = ["_", "."]
    pkg     = __package__
    darkian = os.listdir(Path(__file__).resolve().parent)
    series  = [s for s in darkian if not any(s.startswith(c)
              for c in pvt)]

    for s in sorted(series):
        path = Path(__file__).resolve().parent / Path(s)
        for rule in os.listdir(path):
            # Skip private or non-.py files
            if any(rule.startswith(c) for c in pvt): continue
            name = rule[:-3]  # Strip '.py' extension

            # Filter out unwanted rules based on name
            if only and name.upper() not in only: continue
            if name.upper() in ignore: continue

            # Dynamically import the module and look for
            # functions starting with 'check_' in the module
            mod = importlib.import_module(f"{pkg}.{s}.{name}")
            for attr in dir(mod):
                if attr.startswith("check_"):
                    fn = getattr(mod, attr)
                    if callable(fn): rules.append(fn)

    return rules
