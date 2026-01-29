# textgenerator/generator.py
import random
from .utils import parse_size, sentence_from_words

class Generator:
    """
    Klasa Generator do tworzenia sztucznego tekstu.
    Parametry:
        language: 'pl' lub 'en'
        source: 'local' (można później dodać Wikipedia/OpenSubtitles)
    """
    def __init__(self, language="pl", source="local"):
        self.language = language
        self.source = source

    def generate(self, size="1kb", topic="general", mode="story", output_file="output.txt"):
        """
        Generuje tekst o zadanym rozmiarze.
        size: str, np. '1kb', '5mb'
        topic: temat tekstu (obecnie symbolicznie)
        mode: typ tekstu ('story', 'dialog', 'article')
        output_file: nazwa pliku do zapisu
        """
        size_kb = parse_size(size)
        text = ""

        while len(text.encode('utf-8')) < size_kb * 1024:
            sentence = self._random_sentence(topic, mode)
            text += sentence + " "

        with open(output_file, "w", encoding="utf-8") as f:
            f.write(text.strip())
        print(f"Generated {size} of text in '{output_file}'")

    def _random_sentence(self, topic, mode):
        """
        Tworzy losowe zdanie w zależności od trybu.
        """
        if mode == "dialog":
            # prosty dialog: User: ... AI: ...
            user_sentence = sentence_from_words()
            ai_sentence = sentence_from_words()
            return f"User: {user_sentence} AI: {ai_sentence}"
        else:
            # story / article
            return sentence_from_words()
