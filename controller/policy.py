class CanaryPolicy:
    def __init__(self, step, threshold, cooldown):
        self._step = step
        self._threshold = threshold
        self._cooldown = cooldown

    def calculate_traffic_percentage(self, error_count, request_count):
        """
        Calculate the percentage of traffic to route to the canary version based on the canary policy.
        """
        if request_count == 0:
            return 0
        error_rate = error_count / request_count
        if error_rate >= self._threshold:
            return 0
        else:
            return self._step

    def get_cooldown(self):
        """
        Get the duration of the cooldown period for the canary deployment.
        """
        return self._cooldown