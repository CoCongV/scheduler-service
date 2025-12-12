class RequestStatus:
    """Request status constants (for callback notification)"""
    COMPLETE = "COMPLETE"
    FAIL = "FAIL"


class TaskStatus:
    """Task status constants (for database task lifecycle)"""
    PENDING = "PENDING"       # Pending/Waiting
    RUNNING = "RUNNING"       # Running
    COMPLETED = "COMPLETED"   # Completed (Single task success)
    FAILED = "FAILED"         # Failed
    CANCELLED = "CANCELLED"   # Cancelled
