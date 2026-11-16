"""Consistent comic directory names for download and reader lookup."""

import re
import unicodedata

from models.const import MY_CONFIG


def comic_folder_name(title):
    if not MY_CONFIG.getboolean("general", "ascii_comic_names") or title.isascii():
        return title

    from pypinyin import Style, lazy_pinyin

    # Retain mixed English text and numbers. NFKC also folds full-width Latin
    # characters into ASCII before converting Chinese syllables without tones.
    title = unicodedata.normalize("NFKC", title)
    syllables = lazy_pinyin(title, style=Style.NORMAL, errors="default", v_to_u=False)
    parts = []
    for syllable in syllables:
        encoded = []
        for character in syllable:
            if character.isascii():
                encoded.append(character)
            else:
                # Kana, Hangul and unknown Han characters have no Mandarin
                # reading. Preserve their identity in an ASCII-only label.
                encoded.append(f"_u{ord(character):x}_")
        parts.append("".join(encoded))
    name = re.sub(r"[^A-Za-z0-9_-]+", "_", "_".join(parts))
    name = re.sub(r"_+", "_", name).strip("_-") or "comic"
    return name[:140].rstrip("_-")
