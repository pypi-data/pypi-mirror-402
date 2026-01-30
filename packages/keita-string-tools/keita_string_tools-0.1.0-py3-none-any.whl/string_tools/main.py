from string_tools.string_ops import reverse_string, count_vowels, capitalize_words


def main():
    """
    Fonction principale pour tester les opérations sur les strings.
    """
    test_string = "hello world"

    print(f"Chaîne originale: {test_string}")
    print(f"Inversée: {reverse_string(test_string)}")
    print(f"Nombre de voyelles: {count_vowels(test_string)}")
    print(f"Capitalisée: {capitalize_words(test_string)}")


if __name__ == "__main__":
    main()
