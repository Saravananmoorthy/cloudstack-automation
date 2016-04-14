from analyseReport import reportAnalyser 
from git_CI import github
import re

class testAnalyser():
    def __init__(self):
       self.analyser=reportAnalyser('/automation/virtenv/00-16-3e-17-43-25/158', '/automation/jenkins/workspace/report_generator_158_xenserver_zone-xen/xenserver/reports/','00-16-3e-17-43-25.cfg', 'xenserver', 'Advanced', 158)
       txtreport=self.analyser.generateTextReport2(updateHistory=False)
       self.pattern1=re.compile('{errorcode.*},?')
       self.pattern2=re.compile('AssertionError:.*]')

    def getSuits(self):
        return self.analyser.listOfTestSuits
    
    def getTestsToReRun(self):
        self.analyser.populateErrors()
        self.analyser.collectTestsToReRun()
        print "in test_analysereport metoh getTestsToReRun"
        for suit in  self.analyser.suitsToRerun:
           print "suit=%s"%suit

 
if __name__=="__main__":
   report=reportAnalyser('/automation/virtenv/00-16-3e-17-43-25/132', '/automation/jenkins/workspace/report_generator_132_xenserver_zone-xen/xenserver/reports/','00-16-3e-17-43-25.cfg', 'xenserver', 'Advanced', 132) 
   #txtreport=report.generateTextReport2(updateHistory=False)
   #g=github()
   #g.repo=g.getGitHubRepo()
   #g.commentOnPr(1,report)
   #print txtreport
   analyser=testAnalyser()
   analyser.getTestsToReRun()
