import sentry_sdk
from datetime import datetime
from sycommon.config.Config import Config
from sycommon.logging.kafka_log import SYLogger
from sentry_sdk.integrations.fastapi import FastApiIntegration
# from sentry_sdk.integrations.logging import LoggingIntegration


def sy_sentry_init():
    config = Config().config
    server_name = config.get('Name', '')
    environment = config.get('Nacos', {}).get('namespaceId', '')
    sentry_configs = config.get('SentryConfig', [])
    target_config = next(
        (item for item in sentry_configs if item.get('name') == server_name), None)
    if target_config:
        target_dsn = target_config.get('dsn')
        target_enable = target_config.get('enable')
        current_version = datetime.now().strftime("%Y-%m-%d %H:%M:%S-version")
        if target_config and target_dsn and target_enable:
            try:
                sentry_sdk.init(
                    dsn=target_dsn,
                    traces_sample_rate=1.0,
                    server_name=server_name,
                    environment=environment,
                    release=current_version,
                    integrations=[
                        FastApiIntegration(),
                        # LoggingIntegration(level=logging.INFO,
                        #                    event_level=logging.ERROR)
                    ],
                )
            except Exception as e:
                SYLogger.error(f"Sentry初始化失败: {str(e)}")
