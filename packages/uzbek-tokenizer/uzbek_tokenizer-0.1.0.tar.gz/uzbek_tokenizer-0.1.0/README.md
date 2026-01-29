# Uzbek Tokenizer

A Python library for morphological segmentation of Uzbek text. This tokenizer breaks down Uzbek words into their constituent morphemes (stems and affixes), which is useful for natural language processing tasks like machine learning, text analysis, and linguistic research.

## Features

- 🔤 **Morphological Segmentation**: Breaks Uzbek words into stems and affixes
- 📝 **Text Normalization**: Handles Unicode, punctuation, and Uzbek-specific characters
- ⚡ **Efficient**: Cached segmentation for repeated tokens
- 📦 **Easy to Use**: Simple API for both single words and batch processing
- 🎯 **Agglutinative Language Support**: Designed specifically for Uzbek's morphological structure

## Installation

Install via pip:

```bash
pip install uzbek-tokenizer
```

Or clone the repository:

```bash
git clone https://github.com/IbratDO/uzbek-tokenizer.git
cd uzbek-tokenizer
pip install -e .
```

## Quick Start

### Basic Usage

```python
from uzbek_tokenizer import apply_segmentation, normalize

# Segment a word
text = "kitoblarimizdan"
result = apply_segmentation(text)
print(result)
# Output: ['kitob', 'lar', 'imiz', 'dan']

# Segment a sentence
sentence = "kitoblarimizdan o'qidim"
result = apply_segmentation(sentence)
print(result)
# Output: ['kitob', 'lar', 'imiz', 'dan', "o'q", 'id', 'im']
```

### Normalization Only

```python
from uzbek_tokenizer import normalize

text = "Salom, JAHON!"
normalized = normalize(text)
print(normalized)
# Output: "salom , jahon !"
```

### Morphological Segmentation Only

```python
from uzbek_tokenizer import segment_morphological

word = "o'qiyotgan"
segments = segment_morphological(word)
print(segments)
# Output: ["o'q", 'i', 'yotgan']
```

## API Reference

### `normalize(text: str) -> str`
Normalizes Uzbek text by:
- Converting to NFC Unicode form
- Lowercasing
- Standardizing punctuation
- Handling Uzbek apostrophe variants
- Collapsing whitespace

**Parameters:**
- `text` (str): Input text

**Returns:** Normalized text

### `segment_morphological(token: str) -> list[str]`
Recursively segments a single token into morphemes.

**Parameters:**
- `token` (str): A single word/token

**Returns:** List of morpheme components

### `apply_segmentation(line: str) -> list[str]`
Normalizes text and segments all tokens into morphemes.

**Parameters:**
- `line` (str): Input text (can be multiple words)

**Returns:** List of all morphemes

## How It Works

The tokenizer uses a **greedy longest-match-first algorithm**:

1. **Normalization**: Cleans and standardizes the input text
2. **Prefix Stripping**: Removes longest matching prefixes (be-, no-)
3. **Suffix Stripping**: Removes longest matching suffixes (47+ Uzbek suffixes)
4. **Recursion**: Repeats until no more affixes can be removed
5. **Output**: Returns the stem + all stripped affixes

Example: `kitoblarimizdan`
- Remove suffix "dan" → remainder: "kitoblarimiz"
- Remove suffix "imiz" → remainder: "kitoblar"
- Remove suffix "lar" → remainder: "kitob"
- No more affixes → stem: "kitob"
- Result: `[kitob, lar, imiz, dan]`

## Supported Affixes

### Prefixes (2)
- be-, no-

### Suffixes (47+)
Includes: -cha, -lar, -dagi, -dan, -ga, -ni, -ning, -lik, -ish, and many more

See `uzbek_tokenizer/data/prefixes.txt` and `uzbek_tokenizer/data/suffixes.txt` for the complete list.

## Requirements

- Python 3.8+
- regex >= 2022.0.0

## License

MIT License - see LICENSE file for details

## Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## Issues & Feedback

Found a bug or have a suggestion? Please open an [issue on GitHub](https://github.com/IbratDO/uzbek-tokenizer/issues).

## Citation

If you use this tokenizer in your research, please cite:

```bibtex
@software{uzbek_tokenizer_2026,
  author = {Ibrat Usmonov},
  title = {Uzbek Tokenizer: Morphological Segmentation for Uzbek},
  year = {2026},
  url = {https://github.com/IbratDO/uzbek-tokenizer}
}
```

## Roadmap

- [ ] Vowel harmony validation
- [ ] Stem lemmatization
- [ ] Support for additional Uzbek dialects
- [ ] Performance benchmarks
- [ ] Web API

## Acknowledgments

Built for Uzbek language processing with love ❤️

---

**Status**: Early alpha (v0.1.0) - API may change. Contributions welcome!
