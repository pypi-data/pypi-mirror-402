import os
from typing import Literal

from pydantic import computed_field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """OlmoEarth Settings, configured via environment variables"""

    # Redis configuration
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_USER: str | None = None
    REDIS_PASSWORD: str | None = None
    REDIS_DB: int = 0
    REDIS_MAX_CONNECTIONS: int = 20

    # The number of workers that should be employed to run tasks. Defaults to the number of CPUs available.
    NUM_WORKERS: int = os.cpu_count() or 1

    # Task status database sync configuration
    TASK_STATUS_SYNC_INTERVAL_SECONDS: int = 300  # 5 minutes
    TASK_STATUS_STALENESS_THRESHOLD_MINUTES: int = 15
    SYNC_JOB_REDIS_KEY: str = "olmoearth_run_sync_task_statuses_running"

    # Bulk gcs transfer config
    GCS_LS_PAGE_SIZE: int = 5000

    # The maximum degree of parallelism allowed when processing partitions. If a workflow creates more partitions
    # than this number, multiple partitions will be assigned to a single task and processed serially.
    MAX_PARTITION_PARALLELISM: int = 120

    # The number of dataset build processes that we will launch per CPU core on the machine.
    # Since dataset build is mostly IO bound, this can be set higher than 1.
    DATASET_BUILD_WORKERS_PER_CPU: int = 4

    # The URL that executor workers should use to call the API
    # This environment variable is required except for local runner.
    OERUN_API_URL: str = ""

    # Weights and Biases (https://wandb.ai)
    WANDB_API_KEY: str | None = None
    WANDB_PROJECT: str = "olmoearth_run_develop"
    WANDB_ENTITY: str = "eai-ai2"
    WANDB_API_KEY_SECRET_PATH: str = ""

    # PostgreSQL configuration
    POSTGRES_USER: str | None = None
    POSTGRES_PASSWORD: str | None = None
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_DB_NAME: str = "esrun"  # legacy name

    GOOGLE_CLOUD_BUCKET_NAME: str | None = None
    GOOGLE_CLOUD_PROJECT_ID: str | None = None
    GOOGLE_CLOUD_REGION: str = "us-west1"
    GOOGLE_CLOUD_SERVICE_ACCOUNT_EMAIL: str = ""

    # Grafana Alloy configuration for runner metrics collection
    OERUNNER_ALLOY_CONFIG_BUCKET_NAME: str = ""
    OERUNNER_ALLOY_CONFIG_OBJECT_KEY: str = ""

    # Grafana Cloud Prometheus remote write configuration
    GRAFANA_CLOUD_PROMETHEUS_URL: str = ""
    GRAFANA_CLOUD_PROMETHEUS_USERNAME: str = ""
    GRAFANA_CLOUD_ACCESS_TOKEN_SECRET_PATH: str = ""

    # Prometheus configuration
    PROMETHEUS_MULTIPROC_DIR: str | None = None  # None if not set (single-process mode)
    PROMETHEUS_METRICS_SERVER_PORT: int = 9090

    # The timeout in hours that we send to google batch.
    MAX_TASK_RUN_DURATION_HOURS: float = 8
    MAX_FINE_TUNING_TASK_DURATION_HOURS: float = 120

    # Google Batch provisioning model: FLEX_START or STANDARD
    GOOGLE_BATCH_PROVISIONING_MODEL: Literal["FLEX_START", "STANDARD"] = "FLEX_START"

    # ElasticSearch configuration
    ELASTIC_HOST: str = "localhost"  # Used in local dev & CI.
    ELASTIC_API_KEY: str | None = None  # Can be empty in local dev & CI
    ELASTIC_FEATURES_INDEX_NAME: str = "features"

    # Admin UI configuration
    ADMIN_UI_DIR: str = "admin_ui/"
    ADMIN_UI_PASSWORD: str | None = None

    # These are GCP secret paths. eg: projects/{project_id}/secrets/{SECRET_NAME}/versions/{version}
    AWS_ACCESS_KEY_ID_SECRET_PATH: str = ""
    AWS_ACCESS_KEY_SECRET_PATH: str = ""

    @computed_field  # type: ignore[prop-decorator]
    @property
    def gcs_storage_manager_thread_count(self) -> int:
        return self.NUM_WORKERS * 2

    @computed_field  # type: ignore[prop-decorator]
    @property
    def google_cloud_temp_prefix(self) -> str:
        return f"gs://{self.GOOGLE_CLOUD_BUCKET_NAME}/temp/"


OlmoEarthSettings = Settings()
