class InterviewSchedulerService:
    """
    SDK placeholder for Interview Scheduler.

    IMPORTANT DESIGN NOTE:
    ----------------------
    - This service is BACKEND-ONLY
    - Interview scheduling is triggered automatically
      after MCQ completion
    - SDK must NOT create, modify, or schedule interviews

    Backend file:
    app/services/interview_scheduler_service.py
    """

    def __init__(self, *args, **kwargs):
        raise RuntimeError(
            "InterviewSchedulerService cannot be used from SDK. "
            "Interview scheduling is handled automatically by the backend "
            "after MCQ submission."
        )
