import os 
USERNAME = "election2024"
PASSWORD = "Asar@9301807"
class BaseConfig(object):
	SECRET_KEY = os.environ.get('SECRET_KEY') or 'abcdef123456'
	DEBUG = False
	TESTING = False

class DevelopmentConfig(BaseConfig):
	SECRET_KEY = os.environ.get('SECRET_KEY') or 'abcdef123456'
	DEBUG = True
	TESTING = True

class TestingConfig:
	DEBUG = False
	TESTING = True