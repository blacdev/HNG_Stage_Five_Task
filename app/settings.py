from decouple import config
import os


class Settings:
  FILES_BASE_FOLDER = config("FILES_BASE_FOLDER" , default="files")
  BLOB_BASE_FOLDER = config("BLOB_BASE_FOLDER", default="blob")
 
  def create_base_folders(self):
    if not os.path.exists(self.FILES_BASE_FOLDER):
      os.mkdir(self.FILES_BASE_FOLDER)

    if not os.path.exists(self.BLOB_BASE_FOLDER):
      os.mkdir(self.BLOB_BASE_FOLDER)


settings = Settings()