from decouple import config
import python3_gearman as gearman


class Settings:
  FILES_BASE_FOLDER = config("FILES_BASE_FOLDER" , default="files")
  # FILES_BASE_URL = config("FILES_BASE_URL")
  GEARMAN_HOST = config("GEARMAN_HOST")
  GEARMAN_PORT = config("GEARMAN_PORT")
  CHUNK_BASE_FOLDER = config("CHUNK_BASE_FOLDER", default="chunks")
 
  





settings = Settings()