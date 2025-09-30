from time import time
from fastapi import Request
from src.utils.helpers.errors import RateLimitExceededError


class RateLimiter:
    def __init__(self, limit: int = 60, reset_time: int = 60):
        self.requests = {}  # Memory dictionary (temporary, replace with Redis later)
        self.limit = limit  # Max requests allowed
        self.reset_time = reset_time  # Reset window in seconds

    async def __call__(self, request: Request):
        client_ip = request.client.host
        current_time = time()

        # If IP not seen before, initialize tracking
        if client_ip not in self.requests:
            self.requests[client_ip] = {'count': 1, 'time': current_time}
            return

        request_info = self.requests[client_ip]

        # Reset counter if time window expired
        if current_time - request_info['time'] > self.reset_time:
            self.requests[client_ip] = {'count': 1, 'time': current_time}
            return

        # If within limit
        if request_info['count'] < self.limit:
            request_info['count'] += 1
            return

        # Rate limit exceeded
        if request_info['count'] >= self.limit:
            raise RateLimitExceededError()
