"""Portable v2 wrapper; cloud bundle also includes the two processor modules.

Copy as os4-pilot/tts-os4-live.py beside editorial_voice.py/editorial_plan.py.
Pass --plan and --output-dir. Include voice_runtime/ for local production, or
pass --ode-root for compatibility with the original ODE worker.
"""
from pathlib import Path
import sys

try:
    from editorial_voice import main, V2_DELIVERY_OVERRIDES
except ModuleNotFoundError as exc:
    if exc.name != "editorial_voice":
        raise
    repository_root = Path(__file__).resolve().parents[3]
    sys.path.insert(0, str(repository_root))
    from processor.editorial_voice import main, V2_DELIVERY_OVERRIDES


if __name__ == "__main__":
    main(delivery_overrides=V2_DELIVERY_OVERRIDES)
