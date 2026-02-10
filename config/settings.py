import os
from dotenv import load_dotenv

from pathlib import Path
from dotenv import load_dotenv

load_dotenv(dotenv_path=Path(__file__).resolve().parents[1] / ".env")

SLEEPER_USER_ID = os.getenv("SLEEPER_USER_ID")
if not SLEEPER_USER_ID:
    raise RuntimeError("Missing SLEEPER_USER_ID")

OSU_DYNASTY_LEAGUE_ID = os.getenv("OSU_DYNASTY_LEAGUE_ID")
if not OSU_DYNASTY_LEAGUE_ID:
    raise RuntimeError("Missing OSU_DYNASTY_LEAGUE_ID")
