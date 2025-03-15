from apscheduler.executors.asyncio import AsyncIOExecutor
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from config import get_settings
from pydantic import PostgresDsn

jobstores = {
    "default": SQLAlchemyJobStore(
        url=PostgresDsn.build(
            scheme="postgresql+psycopg2",
            user=get_settings().database_user,
            password=get_settings().database_password,
            host=get_settings().database_host,
            port=str(get_settings().database_port),
            path=f"/{get_settings().database_name}",
        )
    )
}
executors = {"default": AsyncIOExecutor()}
job_defaults = {"coalesce": True, "max_instances": 3, "misfire_grace_time": 60}

# Create scheduler
scheduler = AsyncIOScheduler(
    jobstores=jobstores,
    executors=executors,
    job_defaults=job_defaults,
    timezone="UTC",
)


def start_scheduler():
    scheduler.start()
    return scheduler
