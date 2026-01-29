from app.core.celery_app import celery_app
import logging

logger = logging.getLogger(__name__)


@celery_app.task(
    name="jobs.{group_snake}.{job_snake}",
    autoretry_for=(Exception,),
    retry_kwargs={{"max_retries": 3, "countdown": 10}},
)
def {job_snake}(*args, **kwargs):
    logger.info(
        "🚀 Job {job_display_name} iniciado",
        extra={{
            "args": args,
            "kwargs": kwargs,
        }},
    )

    # TODO: implementar lógica do job

    logger.info("✅ Job {job_display_name} finalizado")
