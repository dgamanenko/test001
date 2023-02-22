from datetime import datetime, timezone


def format_time(timestamp):
    """
    Format a UTC timestamp as a string.
    """
    return datetime.fromtimestamp(timestamp, timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')


def is_rollback_triggered(total_request_count, error_count, policy):
    """
    Determine whether the canary version should be rolled back to the stable version.
    """
    if total_request_count == 0:
        return False
    error_rate = error_count / total_request_count
    if error_rate >= policy.threshold:
        return True
    return False


def get_release_version(aliases):
    """
    Get the release version from the list of aliases.
    """
    for alias in aliases:
        if alias.get("Name") == "release":
            return alias.get("FunctionVersion")
    return None


def get_traffic_config(canary_percentage):
    """
    Get the traffic configuration for the canary and stable versions.
    """
    if canary_percentage == 0:
        return {
            "canary": 0,
            "stable": 100
        }
    else:
        return {
            "canary": canary_percentage,
            "stable": 100 - canary_percentage
        }