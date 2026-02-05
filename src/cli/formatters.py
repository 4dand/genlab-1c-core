"""Утилиты форматированного вывода CLI"""


def print_section(title: str) -> None:
    """Вывести заголовок секции"""
    print()
    print("=" * 60)
    print(f" {title}")
    print("=" * 60)


def print_kv(label: str, value: str) -> None:
    """Вывести пару ключ-значение"""
    print(f"  {label}: {value}")
