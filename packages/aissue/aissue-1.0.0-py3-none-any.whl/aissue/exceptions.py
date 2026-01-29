class AIssueError(Exception):
    """Base exception for AIssue middleware"""
    pass


class AIssueConfigurationError(AIssueError):
    """Raised when AIssue middleware is misconfigured"""
    pass


class AIssueAPIError(AIssueError):
    """Raised when there's an error communicating with AIssue API"""
    pass 