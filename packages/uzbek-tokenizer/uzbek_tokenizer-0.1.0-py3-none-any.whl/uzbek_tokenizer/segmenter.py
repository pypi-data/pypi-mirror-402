import os
import unicodedata
import regex as re
from functools import lru_cache

BASE_DIR = os.path.dirname(__file__)
with open(os.path.join(BASE_DIR, "data/prefixes.txt"), encoding="utf-8") as f:
    PREFIXES = sorted([line.strip() for line in f if line.strip()], key=len, reverse=True)

with open(os.path.join(BASE_DIR, "data/suffixes.txt"), encoding="utf-8") as f:
    SUFFIXES = sorted([line.strip() for line in f if line.strip()], key=len, reverse=True)


def normalize(text: str) -> str:
    """
    Applies normalization rules to Uzbek text.
    """
    # 1) Unicode normalize
    text = unicodedata.normalize("NFC", text)
    # 2) Lowercase
    text = text.lower()
    # 3) Punctuation normalization
    text = re.sub(r"[«»]", '"', text)
    text = re.sub(r"[–—]", "-", text)
    text = re.sub(r'([.!?;:,(){}[\]"`~@#$%^&*+=|\\/<>\-])', r' \1 ', text)
    
    # 4) Special handling for Uzbek apostrophes before O/G
    text = re.sub(r"([OoGg])[\'ʻ''`ʼ]", r"\1ʻ", text)
    
    # 5) Normalize all other apostrophe variants to ʼ (U+02BC)
    text = re.sub(r"[\'ʻ''`]", "ʼ", text)
    
    # 6) Handle special punctuation sequences
    text = re.sub(r'\.{3,}', ' ... ', text)  # Ellipsis
    text = re.sub(r'[!]{2,}', ' !! ', text)   # Multiple exclamations
    text = re.sub(r'[?]{2,}', ' ?? ', text)   # Multiple questions
    
    # 7) Collapse whitespace
    text = re.sub(r"\s+", " ", text).strip()
    return text


@lru_cache(maxsize=None)
def segment_morphological(token: str) -> list[str]:
    """
    Recursively strip the longest matching prefix or suffix from `token`.
    Returns a list of stems/affixes in order.
    """
    if len(token) <= 1:
        return [token]
    
    # 2) Try stripping a prefix
    for p in PREFIXES:
        if token.startswith(p) and len(token) > len(p) + 2:
            remainder = token[len(p):]
            return [p] + segment_morphological(remainder)

    # 3) Try stripping a suffix
    for s in SUFFIXES:
        if token.endswith(s) and len(token) > len(s) + 2:
            remainder = token[:-len(s)]
            return segment_morphological(remainder) + [s]

    # 4) No more affixes found: return the token itself
    return [token]


def apply_segmentation(line: str) -> list[str]:
    """
    Takes a single line of whitespace-tokenized text (e.g. "kitoblarimizdan o'qidim")
    and returns a list where each token is replaced by its
    affix-segmented pieces, e.g.
      ["kitob", "lar", "imiz", "dan", "o'q", "id", "im"]
    """
    pieces = []
    norm = normalize(line)

    for tok in norm.split(" "):
        if tok:  # Skip empty tokens
            pieces.extend(segment_morphological(tok))
    return pieces


# Example usage
if __name__ == "__main__":
    examples = [
        "kitoblarimizdan o'qidim",
        "yig'layvergan edilar",
        "qayta ishlov berish uchun",
        "borganmish"
    ]
    for ex in examples:
        print(f"\nOriginal:  {ex}")
        segmented = apply_segmentation(ex)
        print(f"Segmented: {segmented}")
        print(f"As string: {' '.join(segmented)}")