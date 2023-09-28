from decouple import config


class Settings:
  FILES_BASE_FOLDER = config("FILES_BASE_FOLDER" , default="files")
  # FILES_BASE_URL = config("FILES_BASE_URL")


settings = Settings()