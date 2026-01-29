# textgenerator/utils.py
import random
import string

def parse_size(size):
    """
    Zamienia '1kb', '5mb' na liczbę kilobajtów.
    """
    units = {"kb": 1, "mb": 1024}
    size = size.lower().strip()
    for unit in units:
        if unit in size:
            try:
                return int(float(size.replace(unit, "")) * units[unit])
            except ValueError:
                raise ValueError(f"Niepoprawny format rozmiaru: {size}")
    # jeśli podano bez jednostki, traktujemy jako kb
    try:
        return int(size)
    except ValueError:
        raise ValueError(f"Niepoprawny format rozmiaru: {size}")

def sentence_from_words(min_words=5, max_words=12):
    """
    Generuje losowe zdanie z losowych słów.
    """
    word_count = random.randint(min_words, max_words)
    words = [random_word() for _ in range(word_count)]
    sentence = " ".join(words).capitalize() + "."
    return sentence

def random_word(min_len=3, max_len=8):
    """
    Generuje losowe słowo z liter a-z.
    """
    length = random.randint(min_len, max_len)
    return "".join(random.choices(string.ascii_lowercase, k=length))
