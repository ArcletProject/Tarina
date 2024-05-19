from pathlib import Path

from tarina.lang import lang


lang.load(Path(__file__).parent)

from .model import Lang as Lang
