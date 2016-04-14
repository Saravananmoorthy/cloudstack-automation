from datetime import datetime
from hostImager import resourceManager
from jenkins import Jenkins
import time
from bashUtils import bash
import os
import logging
from git_CI import gitDb

logging.basicConfig(format='%(asctime)s %(levelname)s  %(name)s %(lineno)d  %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p',level=logging.INFO)

class garbageCollector():
      def __init__(self,days=2):
            self.deleteAfterDays=days
            #self.resourceMgr=resourceManager()
            self.logger=logging.getLogger('garbageCollector')

      def setCollectAfterDays(self,days):
          self.deleteAfterDays=days

      def garbageCollect(self, entitieList, dateAttribute, deleteMethod):
          #entitieList=self.resourceMgr.getJobDetails()
          listOfGcEntities=[]
          for entity in entitieList:
              #print entity
              ctime=datetime.strptime(time.ctime(), '%a %b %d %H:%M:%S %Y') 
              diff=ctime-entity[dateAttribute]
              self.logger.info("diff days for entity %s is %s"%(entity, diff.days))
              if (diff.days >= self.deleteAfterDays):
                 listOfGcEntities.append(entity)
          print listOfGcEntities
          self.deleteEntities(listOfGcEntities,deleteMethod)
     
      def deleteEntities(self,entityList, deleteMethod):
          deleteMethod(entityList)


class jenKinsJob():
      
      def __init__(self):
          self.j=Jenkins('http://jenkins-ccp.citrix.com','bharatk','BharatK')
          self.resourceMgr=resourceManager()
          self.logger=logging.getLogger('jenkinsJob')

      def deleteJob(self,jobList):
          print "***********",jobList
          for jobentity in jobList:
              try:
                 self.logger.info("deleteing job %s"%jobentity['job_name'])
                 self.j.delete_job(jobentity['job_name'])
              except Exception,e:
                   # try:
                   #   j.delete_job(jobentity[0].replace("Sandbox-simulator_simula","Sandbox-simulator_simul").replace("Sandbox-simulator_simul","Sandbox-simulator_simulator.xml"))
                   #    print "deleting job %s"%jobentity[0].replace("Sandbox-simulator_simula","Sandbox-simulator_simul").replace("Sandbox-simulator_simul","Sandbox-simulator_simulator") 
                   # except Exception,e:
                   print e
              self.resourceMgr.removeJob(jobentity['job_name'])
              self.logger.info("cleaning up related data")
              os.system("rm -rf %s"%jobentity['related_data_path'])
              os.system("rm -rf /automation/jenkins/workspace/%s"%jobentity['related_data_path'])
              


def main():
   
     def deleteTestLogs(prList):
         logger=logging.getLogger('prLogClenUpMethod')
         for pr in prList:
             try:   
                bash("rm -rf /mnt/test_result_archive/%s"%(pr['build_number']))
             except KeyError as e:
                logger.error('keyError occured, no key named %s for prNo %s'%(e.args[0],pr['pr_no']))

     gc=garbageCollector()
     j=jenKinsJob()
     resourceMgr=resourceManager()
     gc.garbageCollect(resourceMgr.getJobDetails(), 'created', j.deleteJob)
     gc.setCollectAfterDays(2)
     g=gitDb()
     gc.garbageCollect(g.getTestedPrs(), 'updated_at', deleteTestLogs)       

if __name__ == '__main__':
     main()

