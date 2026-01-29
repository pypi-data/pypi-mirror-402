class LeaderboardService:
    """
    SDK placeholder for Leaderboard realtime updates.

    IMPORTANT:
    ----------
    - This service is BACKEND-ONLY
    - Leaderboard updates are pushed via WebSocket
    - SDK MUST NOT trigger or fetch leaderboard manually
    - Admin dashboards receive updates automatically

    Backend file:
    app/services/leaderboard_service.py
    """

    def __init__(self, *args, **kwargs):
        raise RuntimeError(
            "LeaderboardService cannot be used from SDK. "
            "Leaderboard updates are pushed automatically via WebSocket "
            "to admin clients."
        )
