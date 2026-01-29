def to_snake(name: str) -> str:
    return "".join(
        f"_{c.lower()}" if c.isupper() else c
        for c in name
    ).lstrip("_")
