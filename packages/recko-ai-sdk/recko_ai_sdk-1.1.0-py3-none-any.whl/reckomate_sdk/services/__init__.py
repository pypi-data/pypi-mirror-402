"""
Service layer for Reckomate SDK.

Each service maps directly to a backend domain.
"""

# =========================
# Core Services
# =========================
from .admin import AdminService
from .users import UserService
from .users_ingest import UsersIngestService

# =========================
# Question & Content
# =========================
from .question import QuestionService
from .qdrant_service import QdrantService

# =========================
# Excel & MCQ
# =========================
from .excel_service import ExcelService
from .linktestwithphone_service import LinkTestWithPhoneService
from .mcq_service import MCQService
from .mcq_schedule_service import MCQScheduleService
from .leaderboard_service import LeaderboardService

# =========================
# Interview
# =========================
from .interview_logic_service import InterviewLogicService
from .interview_realtime_service import InterviewRealtimeService
from .interview_scheduler_service import InterviewSchedulerService

# =========================
# User MCQ & Tests
# =========================
from .user_mcq_service import UserMCQService
from .usertest_service import UserTestService


__all__ = [
    # Core
    "AdminService",
    "UserService",
    "UsersIngestService",

    # Question & Content
    "QuestionService",
    "QdrantService",

    # Excel & MCQ
    "ExcelService",
    "LinkTestWithPhoneService",
    "MCQService",
    "MCQScheduleService",
    "LeaderboardService",

    # Interview
    "InterviewLogicService",
    "InterviewRealtimeService",
    "InterviewSchedulerService",

    # User
    "UserMCQService",
    "UserTestService",
]
