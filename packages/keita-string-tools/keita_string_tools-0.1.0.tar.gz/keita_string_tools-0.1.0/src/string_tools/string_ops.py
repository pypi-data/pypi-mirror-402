def reverse_string(s: str) -> str:
    """
    Inverse la chaîne de caractères donnée.

    Args:
        s (str): La chaîne à inverser.

    Returns:
        str: La chaîne inversée.
    """
    return s[::-1]


def count_vowels(s: str) -> int:
    """
    Compte le nombre de voyelles dans la chaîne.

    Args:
        s (str): La chaîne à analyser.

    Returns:
        int: Le nombre de voyelles.
    """
    vowels = "aeiouAEIOU"
    return sum(1 for char in s if char in vowels)


def capitalize_words(s: str) -> str:
    """
    Met en majuscule la première lettre de chaque mot.

    Args:
        s (str): La chaîne à capitaliser.

    Returns:
        str: La chaîne avec les mots capitalisés.
    """
    return " ".join(word.capitalize() for word in s.split())
