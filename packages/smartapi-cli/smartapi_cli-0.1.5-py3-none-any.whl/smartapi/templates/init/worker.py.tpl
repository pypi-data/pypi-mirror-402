from app.core.celery_app import celery_app
import app.jobs  # força registro dos jobs

__all__ = ("celery_app",)
