from pathlib import Path
import os

BASE_DIR = Path(__file__).resolve().parent
TEMPLATES_DIR = BASE_DIR / "templates"
GENERATED_DIR = BASE_DIR / "generated"
DATABASE_PATH = BASE_DIR / "salary_bot.db"


def _default_font_path(bold: bool = False) -> str:
    candidates = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "C:/Windows/Fonts/arialbd.ttf" if bold else "C:/Windows/Fonts/arial.ttf",
    ]
    for item in candidates:
        if Path(item).exists():
            return item
    return candidates[0]


FONT_PATH = os.getenv("FONT_PATH", _default_font_path(False))
FONT_BOLD_PATH = os.getenv("FONT_BOLD_PATH", _default_font_path(True))
BOT_TOKEN = os.getenv("BOT_TOKEN", "")
