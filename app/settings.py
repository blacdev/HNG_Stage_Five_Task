from decouple import config
import os


class Settings:
  
  DB_PORT= config("DB_PORT", default="5432")
  DB_HOST = config("DB_HOST", default="localhost")
  DB_USER = config("DB_USER", default="postgres")
  DB_PASSWORD = config("DB_PASSWORD", default="postgres")
  DB_NAME = config("DB_NAME", default="postgres")
  DB_TYPE = config("DB_TYPE", default="postgresql")

  SECRET_KEY = config("SECRET_KEY", default="secret")

  MEDIA_DIR = config("MEDIA_DIR", default="media")
  FILES_BASE_FOLDER = config("FILES_BASE_FOLDER" , default="files")
  BLOB_BASE_FOLDER = config("BLOB_BASE_FOLDER", default="blob")
  THUMBNAIL_BASE_FOLDER = config("THUMBNAIL_BASE_FOLDER", default="thumbnail")
  COMPRESSION_BASE_FOLDER = config("COMPRESSION_BASE_FOLDER", default="compression")
 
  def create_base_folders(self):
    if not os.path.exists(self.MEDIA_DIR):
      os.mkdir(self.MEDIA_DIR)

    abs_path = os.path.abspath(self.MEDIA_DIR)
    if not os.path.exists(os.path.join(abs_path, self.FILES_BASE_FOLDER)):
      FILES_BASE_FOLDER =  os.mkdir(os.path.join(abs_path, self.FILES_BASE_FOLDER))

    else:
      FILES_BASE_FOLDER = os.path.join(abs_path, self.FILES_BASE_FOLDER)

    if not os.path.exists(os.path.join(abs_path, self.BLOB_BASE_FOLDER)):
      BLOB_BASE_FOLDER =  os.mkdir(os.path.join(abs_path, self.BLOB_BASE_FOLDER))
    
    else:
      BLOB_BASE_FOLDER = os.path.join(abs_path, self.BLOB_BASE_FOLDER)

    if not os.path.exists(os.path.join(abs_path, self.THUMBNAIL_BASE_FOLDER)):
      THUMBNAIL_BASE_FOLDER =  os.mkdir(os.path.join(abs_path, self.THUMBNAIL_BASE_FOLDER))
    
    else:
      THUMBNAIL_BASE_FOLDER = os.path.join(abs_path, self.THUMBNAIL_BASE_FOLDER)

    if not os.path.exists(os.path.join(abs_path, self.COMPRESSION_BASE_FOLDER)):
      COMPRESSION_BASE_FOLDER =  os.mkdir(os.path.join(abs_path, self.COMPRESSION_BASE_FOLDER))
    
    else:
      COMPRESSION_BASE_FOLDER = os.path.join(abs_path, self.COMPRESSION_BASE_FOLDER)

    return FILES_BASE_FOLDER, BLOB_BASE_FOLDER, THUMBNAIL_BASE_FOLDER, COMPRESSION_BASE_FOLDER


settings = Settings()