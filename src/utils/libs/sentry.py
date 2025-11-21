import sentry_sdk

def sentry_init(mode: str, dns: str):
    sentry_sdk.init(
        dsn=dns,
        environment="production" if mode == False else 'development', 
        traces_sample_rate=1.0,
        profiles_sample_rate=1.0,
    )

