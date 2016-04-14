import xml.etree.ElementTree as ET
import os
from jenkins import Jenkins
import logging

class modifyJOb():

      class indexObj():
          def __init__(self,incr=3):
              self.start=0
              self.end=0
              self.incr=incr
          def setVals(self,start,incr):
              self.start,self.incr=start,incr
              self.end=start+incr

      def __init__(self):
          self.filename='/root/cloud-autodeploy2/newcode/jeknkins_report_generator_build.xml'
          self.testExecutor='/root/cloud-autodeploy2/newcode/TestExecutor.xml'
          self.tree=ET.parse(self.filename)
          self.indexObj=self.indexObj()
          self.logger=logging.getLogger("jobCreator")
          #self.testExecutor=ET.parse('/root/cloud-autodeploy2/newcode/TestExecutor.xml')
          
      def modifyReportGenerator(self,buildNumber,ListofMailReceivers):
          email=self.tree.find('publishers').find('hudson.plugins.emailext.ExtendedEmailPublisher')
          #print "email",email
          recipientList=email.find('recipientList')
          #print "recipientlist", recipientList
          value=""
          for receiver in ListofMailReceivers:
              value=value+receiver+","
          recipientList.text=value
          #print value
          configTriggers=email.find('configuredTriggers')
          #print "configtrigger", configTriggers
          unstableReceivers=configTriggers.find('hudson.plugins.emailext.plugins.trigger.UnstableTrigger').find('email').\
          find('recipientList')
          unstableReceivers.text=value
          stillFailingReceivers=configTriggers.find('hudson.plugins.emailext.plugins.trigger.StillFailingTrigger').find('email').\
          find('recipientList')
          stillFailingReceivers.text=value
          successReceivers=configTriggers.find('hudson.plugins.emailext.plugins.trigger.SuccessTrigger').find('email').\
          find('recipientList')
          successReceivers.text=value
          outputfile="report_generator_%s.xml"%buildNumber
          #print "writing to file", outputfile
          os.system("touch %s"%outputfile)
          self.tree.write("/root/cloud-autodeploy2/newcode/"+outputfile)
          return outputfile

    
      def addTests2(self,buildNumber, listOfTests):
          self.testExecutor=ET.parse('/root/cloud-autodeploy2/newcode/TestExecutor.xml')
          values=self.testExecutor.find('axes').find('hudson.matrix.TextAxis').find('values') 
          count=0 
          test_list=[]
          self.logger.info("adding tests from start index %s to end index %s"%(self.indexObj.start, self.indexObj.end))
          for test in listOfTests[self.indexObj.start:self.indexObj.end]:
              count=count+1
              s=ET.Element("string")
              s.text=test
              test_list.append(test)
              values.append(s)
          if(count==0):
              return None
          self.logger.info("added tests %s"%test_list)
          outputfile="TestExecutor_%s"%buildNumber
          self.testExecutor.write("/root/cloud-autodeploy2/newcode/"+outputfile)
          self.indexObj.start=self.indexObj.end
          self.indexObj.end=self.indexObj.end+self.indexObj.incr
          return outputfile

      def addTests(self,buildNumber, listOfTests,testsPerJob):
          self.testExecutor=ET.parse('/root/cloud-autodeploy2/newcode/TestExecutor.xml')
          values=self.testExecutor.find('axes').find('hudson.matrix.TextAxis').find('values')
          values.clear()
          count=0
          start=0
          if(testsPerJob is None):
             end=listOfTests.__len__()
          else:
             end=testsPerJob
          test_list=[]
          #self.logger.info("adding tests from start index %s to end index %s"%(self.indexObj.start, self.indexObj.end))
          while(start < listOfTests.__len__()):
             print start,end
             for test in listOfTests[start:end]:
                 count=count+1
                 s=ET.Element("string")
                 s.text=test
                 test_list.append(test)
                 values.append(s)
             self.logger.info("added tests %s"%test_list)
             outputfile="TestExecutor_%s"%buildNumber
             self.testExecutor.write("/root/cloud-autodeploy2/newcode/"+outputfile)
             yield outputfile  
             start=end
             if not testsPerJob is None:
                end=end+testsPerJob
             test_list=[]    
             values.clear()

      def deleteJobs(self):
          j=Jenkins('http://jenkins-ccp.citrix.com','talluri','vmops.com')
          for i in range(757,918):
             print "deleting job %s"%("report_generator_"+str(i)+"_zone-xen_XenServer.xml")
             try:
                j.delete_job("report_generator_"+str(i)+"_zone-xen_XenServer.xml")
             except Exception,e:
                 print e
                 pass     

