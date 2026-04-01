import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "parking-lot-secret-key-2024")
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL",
        "sqlite:///" + os.path.join(BASE_DIR, "instance", "parking.db"),
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    PARKING_TOTAL_SLOTS = 50
    PARKING_HOURLY_RATE = 30.0   # ₹ per hour
    PARKING_DAILY_MAX = 300.0    # ₹ max per day


class DevelopmentConfig(Config):
    DEBUG = True


class ProductionConfig(Config):
    DEBUG = False


config = {
    "development": DevelopmentConfig,
    "production": ProductionConfig,
    "default": DevelopmentConfig,
}
