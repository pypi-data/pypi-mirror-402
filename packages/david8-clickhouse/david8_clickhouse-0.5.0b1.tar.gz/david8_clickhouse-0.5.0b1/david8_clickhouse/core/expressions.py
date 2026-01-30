def on_cluster(value: str | None) -> str:
    if isinstance(value, str):
        return f"ON CLUSTER {value}"

    return ''
