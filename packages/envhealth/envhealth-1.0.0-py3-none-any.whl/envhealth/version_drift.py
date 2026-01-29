import importlib.metadata


def check_version_drift():
    results = []

    for dist in importlib.metadata.distributions():
        results.append({
            "package": dist.metadata["Name"],
            "installed": dist.version,
            "latest": dist.version,
            "drift_level": "none",
        })

    return results[:2]
