from saas_base.settings import BaseSettings


class CommentSettings(BaseSettings):
    SETTINGS_KEY: str = 'WEB_COMMENT'
    DEFAULT_SETTINGS = {
        'TASK_QUEUE_NAME': 'default',
        'TURNSTILE_SITE_KEY': '',
        'COMMENT_SECURITY_RULES': [],
        'THREAD_RESOLVER': {
            'backend': 'webcomment.resolver.ModelThreadResolver',
        },
    }
    IMPORT_SETTINGS = [
        'COMMENT_SECURITY_RULES',
        'THREAD_RESOLVER',
    ]


comment_settings = CommentSettings()
