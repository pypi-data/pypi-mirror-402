def clean_empty(target: dict) -> dict:
    return {k: v for k, v in target.items() if v}
