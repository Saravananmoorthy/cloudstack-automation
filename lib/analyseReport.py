import sys
sys.path.append("/usr/lib/python2.7")
sys.path.append("/usr/lib/python2.7/site-packages")
from xunitparser import parse
#from jira.client import JIRA
import gzip
import os
import zlib
import time
import logging
import smtplib
import HTML
import random
import re
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
#from marvinBugLoggerDal import TcSearchLocalDb
from optparse import OptionParser
from startElastic import indexLogs

class reportAnalyser:
      
      def __init__(self, basedir, configfile, hypervisor, zoneType):
          self.basedir=basedir
          self.configfile=configfile
          self.zoneType=zoneType
          self.testResultFolder=basedir+"/"+hypervisor
          self.totalTests=None
          self.passedTests=None
          self.failedTests=None
          self.skippedTests=None
          self.listOfPassedTests=[]
          self.listOfFailedTests=[]
          self.listOfSkippedTests=[]
          
     def collectTestResults(self):
         if (os.path.isdir(self.testResultFolder)):
            for item in os.listdir(self.testResultFolder):
                 if os.path.isdir(self.testResultFolder + "/" + item) and item.startswith("test"):
                    self.analyseReport(self.testResultFolder+"/"+item)
                 
    def analyseReport(self,pathToTestDataFolder):
        ts,tr=parse(PathToTestDataFolder+"/"+report)
        for tc in ts:
            if (tc.result.lower() == 'failure' or tc.result.lower() == 'error'):
                self.listOfFaliedTests.append(tc)
            else:
                self.listOfPassedTests.append(tc)
             
   def getTotalTests(self):
       if (hypervisor.lower() != "simulator"):
          Tag="tags=%s,'!BugId'"%self.zoneType
       else:
          Tag="tags=selfservice,'!BugId'"
       bash("%s/testenv/bin/nosetests-2.7 --with-xunit --xunit-file=totalTests.xml --with-marvin --marvin-config=%s -w %s/test/integration/smoke -a %s --collect-only "%(self.basedir,options.BASEDIR+"/"+self.configfile, self.basedir,Tag))
       ts, tr=parse(self.basedir+"/totalTests.xml")
            
