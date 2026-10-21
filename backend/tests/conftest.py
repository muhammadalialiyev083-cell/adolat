import os

os.environ.setdefault("DEBUG", "true")
os.environ.setdefault("SECRET_KEY", "test-only-key-not-for-deployment-4cf0350ac83e")
os.environ.setdefault("ALLOWED_HOSTS", "localhost,127.0.0.1,testserver")
