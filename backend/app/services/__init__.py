try:
    from app.services.notification_service import NotificationService, TargetAudience
    __all__ = ["NotificationService", "TargetAudience"]
except ImportError:
    NotificationService = None
    TargetAudience = None
    __all__ = []
