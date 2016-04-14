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
import re
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
#from marvinBugLoggerDal import TcSearchLocalDb
from optparse import OptionParser
#from startElastic import indexLogs
from tabulate import tabulate
from bashUtils import bash
import logging
import filelock
import string
import random
from sets import Set

logging.basicConfig(format='%(asctime)s %(levelname)s  %(name)s %(lineno)d  %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p',level=logging.INFO)

class reportAnalyser:

    class testSuit():

         def __init__(self,ts,tr):
             self.ts=ts
             self.tr=tr
             self.failedTests=[]
             self.skippedTests=[]
             self.passedTests=[]
             self.errors={}
             self.test_file_format=re.compile('test[_a-z]+\.py',re.IGNORECASE)

         def getClassName(self):
             classname=None
             for tc in self.ts:
                 classname=tc.classname
                 break;
             if classname is not  None:
                suitName=classname.split(".")[-2:-1][0]+".py"
                match=self.test_file_format.search(suitName)
                if(match is None):
                       print("getting suitname from trace logs suit %s"%classname)
                       suitName=self.getNameFromTrace()
                       print "suitName",suitName
             else:
                 suitName=self.getNameFromTrace()
             return suitName

         def getNameFromTrace(self):
             for tc in self.failedTests:
                 #print tc.trace
                 match=self.test_file_format.search(tc.trace)
                 if match is not None:
                    suitName=match.string[match.start():match.end()]
                    return suitName

         def hasSetupError(self):
             for tc in self.failedTests:
                 print tc.methodname
                 if "setup" in tc.methodname:
                      print "tc.methodname=%s has setup errors"%tc.methodname
                      return True
             return False

    def __init__(self, basedir, reportDir, configfile, hypervisor, zoneType, buildNo):
          self.logger=logging.getLogger('reportAnalyser')
          self.libDir='/root/cloud-autodeploy2/newcode/'
          self.basedir=basedir
          self.thMgr=TestHistoryManager()
          self.reportDir=reportDir
          self.configfile=configfile
          self.zoneType=zoneType
          self.hypervisor=hypervisor
          self.buildNo=buildNo
          self.testResultFolder=basedir+"/"+hypervisor
          self.totalTests=0
          self.passedTests=0
          self.failedTests=0
          self.skippedTests=0
          self.listOfPassedTests=[]
          self.listOfFailedTests=[]
          self.listOfSkippedTests=[]
          self.listOfTestSuits=[]
          self.report_file_format=re.compile('^test_.*\.xml',re.IGNORECASE)
          self.errorPatterns=self.getErrorPatterns()
          self.collectTestResults()
          self.populateErrors()
          self.suitsToRerun=[]

    def getErrorPatterns(self):
        patterns={'apiError':re.compile('{errorcode.*},?'), 'AssertionError':re.compile('AssertionError:.*]')}
        return patterns

    def getErrorMessagesToReRun(self):
        errorMessages=['SSH Connection Failed', 'SSH failed']
        return errorMessages

    def collectTestResults(self):
         self.logger.info("collecting results")
         files=filter(self.report_file_format.search, os.listdir(self.reportDir))
         for file in files:
             self.processReport(os.path.join(self.reportDir,file))

    def getNameFromTrace(self,suit):
        for tc in suit.failedTests:
            match=self.test_file_format.search(tc.trace)
            if match is not None:
               suitName=match.string[match.start():match.end()]
               return suitName

    def collectTestsToReRun(self):
        self.logger.info('collecting tests to rerun')
        for suit in self.listOfTestSuits:
            suitName=suit.getClassName()
            if suit.hasSetupError():
               self.suitsToRerun.append(suitName)
               continue
            rerun=False
            for errorType in suit.errors.keys():
                self.logger.info("suit=%s, error=%s"%(suitName, suit.errors[errorType]))
                for error in suit.errors[errorType]:
                    for message in self.getErrorMessagesToReRun():
                       if (message in error):
                          self.logger.info("Adding suit %s to rerun %s"%(suitName, error))
                          self.suitsToRerun.append(suitName)
                          rerun=True
                          break
                    if(rerun):
                       break
                if(rerun):
                      break


    def processReport(self,suitFile):
        ts,tr=parse(suitFile)
        suit=self.testSuit(ts,tr)
        self.listOfTestSuits.append(suit)
        for tc in ts:
            if (tc.result.lower() == 'failure' or tc.result.lower() == 'error'):
                self.listOfFailedTests.append(tc)
                suit.failedTests.append(tc)
                self.failedTests=self.failedTests+1
            elif(tc.skipped):
                self.listOfSkippedTests.append(tc)
                suit.skippedTests.append(tc)
                self.skippedTests=self.skippedTests+1
            elif(tc.success):
                self.listOfPassedTests.append(tc)
                suit.passedTests.append(tc)
                self.passedTests=self.passedTests+1

    def populateErrors(self):
        self.logger.info('populating errors')
        for suit in self.listOfTestSuits:
            for errorType in self.errorPatterns.keys():
                suit.errors[errorType]=[]
            for tc in suit.failedTests:
                for errorType in self.errorPatterns.keys():
                    match=self.errorPatterns[errorType].search(tc.message)
                    if(match is not None):
                      suit.errors[errorType].append(match.string[match.start():match.end()])


    def getTotalTests(self):
       if (self.hypervisor.lower() != "simulator"):
          Tag="tags=%s"%self.zoneType
       else:
          Tag="tags=selfservice,'!BugId'"
       bash("%s/testenv/bin/nosetests-2.7 --with-xunit --xunit-file=totalTests.xml -w %s/test/integration/smoke -a %s --collect-only "%(self.basedir, self.basedir,Tag))
       ts, tr=parse(self.basedir+"/totalTests.xml")
       #print dir(tr)

    '''def generateTextReport(self):
       table=[]
       table.append("Suit Name | Passed | Failed | Skipped | Total")
       table.append("---|---|---|---|---|")
       for suit in self.listOfTestSuits:
           #print dir(suit.tr)
           #print dir(suit.ts)
           table.append([str(suit.getClassName())+' | ', str(suit.passedTests.__len__())+' | ', str(suit.failedTests.__len__())+' | ', str(suit.skippedTests.__len__())+' | ', str(suit.ts.countTestCases())+' | '])
           if(suit.failedTests.__len__()!=0):
               for tc in suit.failedTests:
                   table.append(["Failed "+tc.methodname, '','','',''])
       return tabulate(table)'''



    def generateTextReport(self):
       table=[]
       table.append("### ACS CI BVT Run\n **Sumarry:**\n Build Number %s\n Hypervisor %s\n NetworkType %s"%(self.buildNo, self.hypervisor,self.zoneType))
       table.append("Passed=%s\n Failed=%s\n Skipped=%s\n"%(self.listOfPassedTests.__len__(), self.listOfFailedTests.__len__(), self.listOfSkippedTests.__len__()))
       table.append("_Link to logs Folder (search by build_no):_ https://www.dropbox.com/sh/yj3wnzbceo9uef2/AAB6u-Iap-xztdm6jHX9SjPja?dl=0\n")

       table.append("Failed | Skipped | Passed | Total | Suit Name")
       table.append("---|---|---|---|---|")
       for suit in self.listOfTestSuits:
           #print dir(suit.tr)
           #print dir(suit.ts)
           table.append("%s | %s | %s | %s | %s)"%(str(suit.failedTests.__len__()), str(suit.skippedTests.__len__()), str(suit.passedTests.__len__()), str(suit.ts.countTestCases()), str(suit.getClassName())))
           if(suit.failedTests.__len__()!=0):
               for tc in suit.failedTests:
                   table.append("Failed %s | | | |"%tc.methodname)
       return "\n".join(table)

    def getStringIntDict(self, pair):
          if pair.__len__() > 0:
             return {pair[0]:int(pair[1])}

    def filterByError(self):
        if (self.listOfTestSuits is None or self.listOfTestSuits.__len__() > 0):
           for suit in self.listOfSuits:
               for tc in suit.failedTests:
                 pass

    def generateTextReport2(self,updateHistory=True,addKnownIssues=False):
       self.logger.info("generating report")
       table_failed=[]
       table_passed=[]
       table_skipped=[]
       table=[]
       #table.append("### ACS CI BVT Run\n **Sumarry:**\n Build Number %s\n Hypervisor %s\n NetworkType %s"%(self.buildNo, self.hypervisor,self.zoneType))
       #table.append(" Passed=%s\n Failed=%s\n Skipped=%s\n"%(self.listOfPassedTests.__len__(), self.listOfFailedTests.__len__(), self.listOfSkippedTests.__len__()))
       known_test_issues=self.thMgr.getKnownIssuesString()

       table_failed.append("**Failed tests:**")
       table_skipped.append("**Skipped tests:**")
       table_passed.append("**Passed test suits:**")

       known_issues=self.thMgr.getKnownIssuesDict()
       failed_issues=self.thMgr.getFailedIssuesDict()

       failed_tests_not_in_known_issues=0

       for suit in self.listOfTestSuits:
           #print dir(suit.tr)
           #print dir(suit.ts)

           for tc in suit.failedTests:
                #print ("failed test %s"%tc.methodname)
                if (tc.methodname not in known_issues.keys()):
                       #print "tc metod name %s"%tc.methodname
                       failed_tests_not_in_known_issues+=1
                       if ("* "+suit.getClassName()+"\n" not in table_failed):
                           table_failed.append("* %s\n"%suit.getClassName())

                       if(tc.methodname in failed_issues.keys()):
                            failed_issues[tc.methodname]+=1
                            table_failed.append(" * %s Failing since %s runs\n"%(tc.methodname,failed_issues[tc.methodname]))
                       else:
                           failed_issues[tc.methodname]=1
                           table_failed.append(" * %s Failed\n"%(tc.methodname))
                elif (tc.methodname not in failed_issues.keys()):
                      failed_issues[tc.methodname]=1
                else:
                     failed_issues[tc.methodname]+=1

           for tc in suit.skippedTests:
                   table_skipped.append("%s"%tc.methodname)

           for tc in suit.passedTests:
               #print "passed test %s"%tc.methodname
               if (tc.methodname in known_issues.keys()):
                   #print "in known issues %s"%tc.methodname
                   known_issues[tc.methodname]+=1
               if (tc.methodname in failed_issues.keys()):
                   self.logger.info("%s method passed, removing from failed tests"%tc.methodname)
                   failed_issues[tc.methodname]=0

           if(suit.passedTests.__len__()!=0 and suit.failedTests.__len__()==0 and suit.skippedTests.__len__()==0):
                   table_passed.append("%s"%suit.getClassName())

       if(updateHistory):
          self.logger.info("updating history")
          self.thMgr.persistKnownIssues(known_issues)
          self.thMgr.persistFailedIssues(failed_issues)

       table.append("### ACS CI BVT Run\n **Sumarry:**\n Build Number %s\n Hypervisor %s\n NetworkType %s"%(self.buildNo, self.hypervisor,self.zoneType))
       if(addKnownIssues):
         table.append(" Passed=%s\n Failed=%s\n Skipped=%s\n"%(self.listOfPassedTests.__len__(), self.listOfFailedTests.__len__(), self.listOfSkippedTests.__len__()))
         table.append("**The follwing tests have known issues**")
         table.append(known_test_issues+'\n')
       else:
         table.append(" Passed=%s\n Failed=%s\n Skipped=%s\n"%(self.listOfPassedTests.__len__(), failed_tests_not_in_known_issues, self.listOfSkippedTests.__len__()))
       table.append("_Link to logs Folder (search by build_no):_ https://www.dropbox.com/sh/yj3wnzbceo9uef2/AAB6u-Iap-xztdm6jHX9SjPja?dl=0\n")
       return "\n".join(table)+"\n\n"+"\n".join(table_failed)+"\n\n"+"\n".join(table_skipped)+"\n\n"+"\n".join(table_passed)


class TestHistoryManager:
    def __init__(self):
        self.logger=logging.getLogger('testhistoryManager')
        self.libDir='/root/cloud-autodeploy2/newcode'
        self.knownIssuesFile='%s/known_test_issues'%self.libDir
        self.failedIssuesFile='%s/failed_test_issues'%self.libDir
        self.klockFilePath="%s/.klockFile"%self.libDir
        self.flockFilePath="%s/.flockFile"%self.libDir
        self.knownIssueThreshold=3
        if (not os.path.isfile(self.klockFilePath)):
             bash("touch %s"%self.klockFilePath)
        if (not os.path.isfile(self.flockFilePath)):
             bash("touch %s"%self.flockFilePath)
        self.klock=filelock.FileLock(self.klockFilePath)
        self.flock=filelock.FileLock(self.flockFilePath)

    def _getStringIntDict(self, pair):
          if pair.__len__() > 0:
             #print pair
             return {pair[0]:int(pair[1])}

    def _getIssuesDict(self,file):
       f=open(file,'r')
       issuesData=f.read()
       f.close()
       issuesDict={}
       for issue in issuesData.split('\n'):
           if issue.__len__() > 0:
              issuesDict.update(map(self._getStringIntDict, [issue.split(",")])[0])
       return  issuesDict

    def _getIssuesString(self,file):
        f=open(file, 'r')
        fdata=f.read()
        issuelist=[issue.split(',')[0] for issue in fdata.split('\n')]
        return "\n".join(issuelist)

    def persistKnownIssues(self,issuesDict):
        data=[key+","+str(issuesDict[key]) for key in issuesDict.keys() if issuesDict[key] <= self.knownIssueThreshold]
        tempFile="."+''.join(random.SystemRandom().choice(string.ascii_uppercase + string.digits) for _ in range(10))
        retry=3
        while retry >0:
           try:
              with self.klock.acquire(timeout=10):
                   file=open("%s/%s"%(self.libDir,tempFile),'w')
                   file.write("\n".join(data))
                   file.close()
                   break
           except Exception as e:
                  retry-=1
                  self.logger.info('failed to update known issues files due to %s'%e)
        #print "mv %s/%s  %s"%(self.libDir, tempFile, self.knownIssuesFile)
        bash("mv %s/%s  %s"%(self.libDir, tempFile, self.knownIssuesFile))

    def persistFailedIssues(self,issuesDict):
        data=[key+","+str(issuesDict[key]) for key in issuesDict.keys() if issuesDict[key] > 0]
        retry=3
        tempFile="."+''.join(random.SystemRandom().choice(string.ascii_uppercase + string.digits) for _ in range(10))
        #print tempFile
        while retry >0:
           try:
              with self.flock.acquire(timeout = 10):
                   file=open("%s/%s"%(self.libDir,tempFile),'w')
                   file.write("\n".join(data))
                   file.close()
                   break
           except Exception as e:
                  retry-=1
                  self.logger.info('failed to update failed issues files due to %s'%e)
        bash("mv %s/%s  %s"%(self.libDir, tempFile, self.failedIssuesFile))


    def getKnownIssuesDict(self):
        return self._getIssuesDict(self.knownIssuesFile)

    def getFailedIssuesDict(self):
        return self._getIssuesDict(self.failedIssuesFile)

    def getKnownIssuesString(self):
        return self._getIssuesString(self.knownIssuesFile)

    def getFailedIssuesString(self):
        return self._getIssuesString(self.failedIssuesFile)


