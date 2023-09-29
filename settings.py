from decouple import config


class Settings:
  FILES_BASE_FOLDER = config("FILES_BASE_FOLDER" , default="files")
  # FILES_BASE_URL = config("FILES_BASE_URL")
  cloud_name = config("cloud_name")
  api_key = config("api_key")
  secret_key = config("api_secret")


settings = Settings()