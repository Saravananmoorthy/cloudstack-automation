import xml.etree.ElementTree as ET
import os
from jenkins import Jenkins


class modifyJOb():
      def __init__(self):
          self.filename='/root/cloud-autodeploy2/newcode/jeknkins_report_generator_build.xml'
          self.testExecutor='/root/cloud-autodeploy2/newcode/TestExecutor.xml'
          self.tree=ET.parse(self.filename)
          #self.testExecutor=ET.parse('/root/cloud-autodeploy2/newcode/TestExecutor.xml')
          
      def modifyReportGenerator(self,buildNumber,ListofMailReceivers):
          email=self.tree.find('publishers').find('hudson.plugins.emailext.ExtendedEmailPublisher')
          print "email",email
          recipientList=email.find('recipientList')
          print "recipientlist", recipientList
          value=""
          for receiver in ListofMailReceivers:
              value=value+receiver+","
          recipientList.text=value
          print value
          configTriggers=email.find('configuredTriggers')
          print "configtrigger", configTriggers
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
          print "writing to file", outputfile
          os.system("touch %s"%outputfile)
          self.tree.write("/root/cloud-autodeploy2/newcode/"+outputfile)
          return outputfile


      def addTests(self,buildNumber,listOfTests):
          self.testExecutor=ET.parse('/root/cloud-autodeploy2/newcode/TestExecutor.xml')
          values=self.testExecutor.find('axes').find('hudson.matrix.TextAxis').find('values') 
          for test in listOfTests:
              s=ET.Element("string")
              s.text=test
              values.append(s)
          outputfile="TestExecutor_%s"%buildNumber
          self.testExecutor.write("/root/cloud-autodeploy2/newcode/"+outputfile)
          return outputfile

      def deleteJobs(self):
          j=Jenkins('http://jenkins-ccp.citrix.com','talluri','vmops.com')
          for i in range(757,918):
             print "deleting job %s"%("report_generator_"+str(i)+"_zone-xen_XenServer.xml")
             try:
                j.delete_job("report_generator_"+str(i)+"_zone-xen_XenServer.xml")
             except Exception,e:
                 print e
                 pass     
