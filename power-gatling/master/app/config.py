import os


class Settings:
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://redis:6379")
    WORKER_COUNT: int = int(os.getenv("WORKER_COUNT", "3"))
    SCENARIOS_DIR: str = os.getenv("SCENARIOS_DIR", "/app/scenarios")
    RESULTS_DIR: str = os.getenv("RESULTS_DIR", "/app/results")
    SCRIPTS_DIR: str = os.getenv("SCRIPTS_DIR", "/app/scripts")
    GATLING_VERSION: str = os.getenv("GATLING_VERSION", "3.10.3")
    MASTER_HOST: str = os.getenv("MASTER_HOST", "0.0.0.0")
    MASTER_PORT: int = int(os.getenv("MASTER_PORT", "8000"))


settings = Settings()
