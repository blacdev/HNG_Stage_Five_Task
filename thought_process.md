
# Merge_Cast 

## Version 1.0

### User

- A user can have multiple sign in options(google, uesrname, password etc)
- A user only has a single bucket and many files
- A user can only access their own bucket and files
- A user can only access their own files
- A user can stream a file link shared with them
- A user can only download a file shared with them
- A user can delete a file they created

## Bucket

- A user has 2 buckets by default
  - `public` bucket
  - `private` bucket
- A bucket can have many files
- A bucket can only be accessed by the user who created it

### File(videos)

- A file is uploaded by a user in BLOBs
- A file only supports mp4 and webm formats
- A file can only be accessed by the user who created it
- A file can be shared with other users
- A file can be downloaded by other users
- A file can be streamed by other users
- A file can be deleted by the user who created it
- A file belongs to a bucket and can only be accessed by the user who created the bucket
- A file is hidden from other users by default
- A file is only visible to other users when it is shared with them

### BLOBs

- A BLOB is a part of a file
- A BLOB is uploaded by a user
- A BLOB can only be accessed by merging algorithm
- Merged BLOBs are available to the user who uploaded the file
- A BLOB is deleted after it has been successfully merged
- A BLOB has metadata that gives information about the BLOB like:
  - position of BLOB: The position the BLOB would be in the merged file
  - size of BLOB: The size of the BLOB in bytes
  - is_processed: A boolean value that indicates if the BLOB has been processed
  - is_merged: A boolean value that indicates if the BLOB has been merged

### Transcribe file

- A file can only be transcribed after it has been successfully merged
- A file trancrition holds information about the time each line was said in the video


### Sharing

- A user can share a file link with other users


