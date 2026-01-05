from servises.config import config


CELERY_CONFIG = {
    'broker_url': f'redis://{config.REDIS_HOST}:{config.REDIS_PORT}/0',
    'result_backend': f'redis://{config.REDIS_HOST}:{config.REDIS_PORT}/0',
    'task_serializer': 'json',
    'accept_content': ['json'],
    'result_serializer': 'json',
    'timezone': 'UTC',
    'enable_utc': True,
    'task_track_started': True,
    'task_time_limit': 30 * 60,
    'worker_prefetch_multiplier': 1,
    'worker_max_tasks_per_child': 1000,
} 