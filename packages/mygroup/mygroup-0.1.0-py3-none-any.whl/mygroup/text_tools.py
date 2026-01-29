import re


def slugify(text):
    text = text.strip().lower()
    text = re.sub(r"[^a-z0-9\s-]", "", text)
    text = re.sub(r"[\s-]+", "-", text)
    return text.strip("-")


def count_words(text):
    return len(re.findall(r"\b\w+\b", text))


def truncate(text, max_len, suffix="..."):
    if max_len < 0:
        raise ValueError("max_len must be >= 0")
    if len(text) <= max_len:
        return text
    if len(suffix) > max_len:
        return suffix[:max_len]
    return text[: max_len - len(suffix)] + suffix


def is_palindrome(text):
    s = re.sub(r"[^a-z0-9]", "", text.lower())
    return s == s[::-1]
