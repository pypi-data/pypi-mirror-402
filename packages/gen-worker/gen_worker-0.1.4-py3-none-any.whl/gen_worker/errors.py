class WorkerError(Exception):
    """Base class for worker execution errors."""


class RetryableError(WorkerError):
    """Indicates the job can be retried safely."""


class FatalError(WorkerError):
    """Indicates the job should not be retried."""
