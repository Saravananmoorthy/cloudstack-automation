from datetime import datetime
from hostImager import resourceManager
from jenkins import Jenkins
import time
from bashUtils import bash
import os

class garbageCollector():
      def __init__(self):
            self.deleteAfterDays=2
            self.resourceMgr=resourceManager()

      def garbageCollect(self):
          jobDetails=self.resourceMgr.getJobDetails()
          gcJobList=[]
          for detail in jobDetails:
              #print detail
              ctime=datetime.strptime(time.ctime(), '%a %b %d %H:%M:%S %Y') 
              diff=ctime-detail['created']
              print "diff days for job %s is %s"%(detail, diff.days)
              if (diff.days >= self.deleteAfterDays):
                 gcJobList.append([detail['job_name'],detail['related_data_path']])
          print "Deleting the following jobs"
          print gcJobList
          self.deleteJobs(gcJobList)
     
      def deleteJobs(self,jobList):
          j=Jenkins('http://jenkins-ccp.citrix.com','bharatk','BharatK')
          for jobdetail in jobList:
              try:
                 print "deleteing job %s"%jobdetail[0]
                 j.delete_job(jobdetail[0])
              except Exception,e:
                   # try:
                   #   j.delete_job(jobdetail[0].replace("Sandbox-simulator_simula","Sandbox-simulator_simul").replace("Sandbox-simulator_simul","Sandbox-simulator_simulator.xml"))
                   #    print "deleting job %s"%jobdetail[0].replace("Sandbox-simulator_simula","Sandbox-simulator_simul").replace("Sandbox-simulator_simul","Sandbox-simulator_simulator") 
                   # except Exception,e:
                   print e
              print "deleting job %s"%jobdetail[0]
              self.resourceMgr.removeJob(jobdetail[0])
              print "deleted job %s"%jobdetail[0]
              print "cleaning up related data"
              os.system("rm -rf %s"%jobdetail[1])
              os.system("rm -rf /automation/jenkins/workspace/%s"%jobdetail[0])
              


def main():
     gc=garbageCollector()
     gc.garbageCollect()


if __name__ == '__main__':
     main()

