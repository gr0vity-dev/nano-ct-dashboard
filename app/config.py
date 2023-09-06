from app import secrets

class Config(object):
    DEBUG = False
    TESTING = False

# Load all defined variables from app/secrets.py outside the class definition
for key, value in vars(secrets).items():
    if key.isupper():  # Assuming you're following the convention of using uppercase for config vars
        setattr(Config, key, value)

class ProductionConfig(Config):
    pass

class DevelopmentConfig(Config):
    DEBUG = True

class TestingConfig(Config):
    TESTING = True
