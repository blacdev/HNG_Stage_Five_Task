from app.settings import settings
import sys
from file_processing.chunk_processor import video_processing_start
import asyncio
from typing import Dict
from pprint import pprint
import python3_gearman as gearman

gm_worker = gearman.GearmanWorker([settings.GEARMAN_HOST + settings.GEARMAN_PORT])




def import_task_listener(task_id, gearman_job:str):
    pprint("gearman job received", gearman_job)
#   if task_id == "process_video":
    id = gearman_job.strip(' ')[0]
    bucket_name = gearman_job.strip(" ")[1]
    file_name = gearman_job.strip(" ")[2]

    asyncio.run(video_processing_start(id, bucket_name, file_name))

    print("Completed!!!")
    return "success"
#   elif task_id == "transcribe":
#       pass



def restart_gearman_worker():
    try:
        gm_worker.work()
    except Exception as e:
        print(e)
        print("restarting gearman worker...")
        gm_worker.work()
    except KeyboardInterrupt:
        print("exiting gearman worker...")
        gm_worker.shutdown()
        sys.exit(0)

gm_worker.set_client_id("imports-worker")
gm_worker.register_task("process_video", import_task_listener)
gm_worker.register_task("transcribe", import_task_listener)



if __name__ == "__main__":
    
    # strat gearman worker
    # if error, print error and restart gearman worker 3 times then exit
    print("starting gearman worker")
  
    try:
        gm_worker.work()
    except Exception as e:
        print(e)
        print("restarting gearman worker...")
        restart_gearman_worker()

    # asyncio.run(video_processing_start("9ef71acd131b4dcf80b0ab745cf50e08", "seye12344", "adsad.mp4"))