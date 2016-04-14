from jenkinsGarbageCollector import garbageCollector
from hostImager import resourceManager
#resourceMgr=resourceManager()
jobDetail={'job_name':"testjobjenkins",'related_data_path':"/tmp/dummy"}
#resourceMgr.addJobDetails(jobDetail)
gc=garbageCollector()
gc.garbageCollect()

