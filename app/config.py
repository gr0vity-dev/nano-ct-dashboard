from app.secrets import GITHUB_TOKEN


class Config(object):
    DEBUG = False
    TESTING = False
    GITHUB_TOKEN = GITHUB_TOKEN


class ProductionConfig(Config):
    pass


class DevelopmentConfig(Config):
    DEBUG = True


class TestingConfig(Config):
    TESTING = True
