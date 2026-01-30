import logging
import threading

from altasigma.credentials.credential_utils import _credential_utils


class TokenRefresher:
    """
    Runs the _existing_token function every hour. This exists to make sure the refresh token is refreshed before it
    expires. If no traffic happens, then likely the refresh token will also not be refreshed.

    Mostly uses _existing_token instead of _refresh_token since that one requires the refresh token, and we don't want to care
    for handling that here.
    """
    def __init__(self, refresh_interval_seconds: int = 3600):
        self.refresh_interval = refresh_interval_seconds
        self.timer = None

    def schedule_refresh(self):
        self.timer = threading.Timer(self.refresh_interval, self._refresh_token_task)
        # Allow program to exit even if timer is alive
        self.timer.daemon = True
        self.timer.start()

    def _refresh_token_task(self):
        try:
            _credential_utils()._existing_token()
        except Exception as e:
            logging.error(f"Token refresh failed: {e}")
        finally:
            self.schedule_refresh()