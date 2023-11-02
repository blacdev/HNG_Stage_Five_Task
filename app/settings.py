from decouple import config
import os


class Settings:
  MEDIA_DIR = config("MEDIA_DIR", default="media")
  FILES_BASE_FOLDER = config("FILES_BASE_FOLDER" , default="files")
  BLOB_BASE_FOLDER = config("BLOB_BASE_FOLDER", default="blob")
  THUMBNAIL_BASE_FOLDER = config("THUMBNAIL_BASE_FOLDER", default="thumbnail")
  COMPRESSION_BASE_FOLDER = config("COMPRESSION_BASE_FOLDER", default="compression")
 
  def create_base_folders(self):
    if not os.path.exists(self.MEDIA_DIR):
      os.mkdir(self.MEDIA_DIR)

    abs_path = os.path.abspath(self.MEDIA_DIR)
    FILES_BASE_FOLDER = os.path.join(abs_path, self.FILES_BASE_FOLDER)
    BLOB_BASE_FOLDER = os.path.join(abs_path, self.BLOB_BASE_FOLDER)
    THUMBNAIL_BASE_FOLDER = os.path.join(abs_path, self.THUMBNAIL_BASE_FOLDER)
    COMPRESSION_BASE_FOLDER = os.path.join(abs_path, self.COMPRESSION_BASE_FOLDER)

    for folder in [FILES_BASE_FOLDER, BLOB_BASE_FOLDER, THUMBNAIL_BASE_FOLDER, COMPRESSION_BASE_FOLDER]:
      if not os.path.exists(folder):
        os.mkdir(folder)

    return FILES_BASE_FOLDER, BLOB_BASE_FOLDER, THUMBNAIL_BASE_FOLDER, COMPRESSION_BASE_FOLDER


settings = Settings()