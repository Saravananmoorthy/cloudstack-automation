#!/usr/bin/env python2.7
import os
from paramiko import SSHClient,AutoAddPolicy
import time
import subprocess
from scp import SCPClient
from bashUtils import bash
import xunitparser
from jenkins import Jenkins
import logging
from jenkinsJob import modifyJOb
from marvin.configGenerator import ConfigManager
from marvin import configGenerator
import Queue
import threading
from hostImagerProfiles import resourceManager
from modifyTestData import modifyTestData

class testEnv():

    def __init__(self):
       self.workDir="/automation/virtenv"
       self.marvinPath="/automation/cloudstack/tools/marvin/dist/"
       self.testcasePath="/automation/cloudstack/test"
       self.pythonPath=""
       self.libPath="/root/cloud-autodeploy2/newcode"
       self.jenkinsWorkspace="/automation/jenkins/workspace"
       self.logger=logging.getLogger("testEnvMgr")
       self.resourceMgr=resourceManager()

    def initLogging(self,logFile=None, lvl=logging.INFO):
       try:
          if logFile is None:
            logging.basicConfig(level=lvl, \
                                format="'%(asctime)-6s: %(name)s \
                                (%(threadName)s) - %(levelname)s - %(message)s'")
          else:
            logging.basicConfig(filename=logFile, level=lvl, \
                                format="'%(asctime)-6s: %(name)s \
                                (%(threadName)s) - %(levelname)s - %(message)s'")
       except:
           logging.basicConfig(level=lvl)

    def create(self,hostInfo,build_number,version,logPath=None):
        configFilePath=hostInfo['configfile']
        os.chdir(self.workDir)
        if not (os.path.isdir(self.workDir+"/"+hostInfo['mac'].replace(":","-"))):
               os.mkdir(hostInfo['mac'].replace(":","-"))
        virtenvPath=self.workDir+"/"+hostInfo['mac'].replace(":","-")+"/"+build_number
        if (os.path.isdir(virtenvPath)):
            os.system("rm -rf %s"%virtenvPath)
        os.system("mkdir -p %s"%virtenvPath)
        os.chdir(virtenvPath)
        bash("virtualenv testenv")
        self.logger.info ("created virtual test environment")
        ssh = SSHClient()
        ssh.set_missing_host_key_policy(AutoAddPolicy())
        ssh.connect(hostname=hostInfo['hostname'],username="root",password=hostInfo['password'])
        scp = SCPClient(ssh.get_transport())
        scp.get(self.marvinPath,"./dist/",recursive=True)
        self.pythonPath=virtenvPath+"/testenv/bin/"
        #download and install mysql-connector for python.
        bash("wget http://cdn.mysql.com/Downloads/Connector-Python/mysql-connector-python-2.0.4.zip#md5=3df394d89300db95163f17c843ef49df")
        bash("%s/easy_install mysql-connector-python-2.0.4.zip"%self.pythonPath)
        marvinName=bash("ls ./dist/ | grep Marvin.*tar.gz").getStdout()
        bash("tar -xf ./dist/%s"%marvinName)
        #print marvinName
        scp.get(self.testcasePath,"./",recursive=True)
        ##install marvin
        self.logger.info("executing", "%s install %s/%s --allow-external mysql-connector-python"%(self.pythonPath+"pip2.7",virtenvPath,marvinName.replace(".tar.gz",""))) 
        os.system("%s install %s/%s --allow-external mysql-connector-python"%(self.pythonPath+"pip2.7",virtenvPath,marvinName.replace(".tar.gz","")))
        #copy config template and add hostname to config template
        configFileName=hostInfo['mac'].replace(":","-")+".cfg"
        bash("cp %s ./%s"%(configFilePath,configFileName))
        bash("sed -i 's/10.147.28.149/%s/g' %s"%(hostInfo['hostname'],virtenvPath+"/"+configFileName))
        if logPath==None:
             logPath=virtenvPath.replace("/","\/")+"\/results"
        #copy test_data.py->contains env specific changes.
        #bash("cp -f  /root/cloud-autodeploy2/newcode/test_data.py %s/testenv/lib/python2.7/site-packages/marvin/config/test_data.py"%virtenvPath)
        bash("sed -i 's/\/tmp\/cloudstack/%s/g' %s"%(logPath,virtenvPath+"/"+configFileName))
        env={'pythonPath':self.pythonPath,'config_file':configFileName,'virtenvPath':virtenvPath,'hostip':hostInfo['ip'], 'build_number':build_number, 'version':version, 'noSimulator':hostInfo['noSimulator'], 'repo_url':hostInfo['repo_url'], \
           'startTime':hostInfo['startTime'], 'commit_id':hostInfo['commit_id']}
        self.logger.info("Adding environment specific data to %s/testenv/lib/python2.7/site-packages/marvin/config/test_data.py"%virtenvPath)
        bash("/root/cloud-autodeploy2/newcode/editTestdata.sh /root/cloud-autodeploy2/newcode/env_specific_test_data %s/testenv/lib/python2.7/site-packages/marvin/config/test_data.py"%virtenvPath)
        return env 
   
    def createDataCenter(self,env,tag=None):
        try:
            os.chdir(env['virtenvPath'])
            marvin_config=env['config_file']
            pythonPath=env['pythonPath']
            self.logger.info("Deploying datacenter using marvin")
            #subprocess.check_call("%s/nosetests-2.7 -v --with-marvin --marvin-config=%s -w /tmp"%(pythonPath,marvin_config),shell=True)
            marvinFolder=bash("ls | grep Marvin-[0-9].[0-9].[0-9]").getStdout()
            subprocess.check_call("%s/nosetests-2.7 -v --with-marvin --marvin-config=%s --deploy -w /tmp"%(pythonPath,marvin_config),shell=True)
            #subprocess.check_call("%s/python2.7 ./%s/marvin/deployDataCenter.py -i %s"%(pythonPath,marvinFolder,marvin_config),shell=True)
            self.logger.info("Testing if setup is ready")
            subprocess.check_call("%s/nosetests-2.7 -v --with-marvin --marvin-config=%s /root/cloud-autodeploy2/newcode/testSetupSuccess.py"%(pythonPath,marvin_config),shell=True) 
            self.logger.info("Restarting Management server for global setting changes to take effect")
            subprocess.check_call("%s/python2.7 /root/cloud-autodeploy2/newcode/restartMgmt.py --config  %s --noSimulator %s"%(pythonPath,marvin_config,env['noSimulator']),shell=True)
            self.logger.info("Waiting some time for managementserver startup")
            time.sleep(120)
        except Exception, e:
            self.logger.info("error occured while deploying datacenter.")
            self.logger.error(e)
            return 1
    
    def execTests(self, env, tag=None): 
        #launch test suite 
        try:
           #subprocess.check_call("bash setup-test-data.sh -t integration/smoke -m %s -p password -d %s -h xen"%(mgmtHostInfo['ip'],mgmtHostInfo['ip']),shell=True)
           self.logger.info("Launching integration tests after a sleep")
           #time.sleep(300)
           self.logger.info("%s/nosetests-2.7 -v --with-marvin --marvin-config=%s -w ./test/integration/smoke  --load --with-xunit %s"%(pythonPath,marvin_config,("" if tag==None else "-a tag=%s"%tag)))
           subprocess.check_out("%s/nosetests-2.7 -v --with-marvin --marvin-config=%s -w ./test/integration/smoke  --load --with-xunit %s"%(pythonPath,marvin_config,("" if tag==None else "-a tag=%s"%tag)),shell=True)
        except Exception, e:
               self.info.error(e) 

    def isJobComplete(self,queue):
          args=queue.get()
          envPath=args[0]
          jobIdentifier=args[1]
          while not os.path.isdir(envPath+"/"+"%sComplete"%jobIdentifier):
                    self.logger.debug("testing on zone %s is in progress"%jobIdentifier)
                    time.sleep(20)
          queue.task_done()
          bash("rm -f %s/%sComplete"%(envPath,jobIdentifier))
   
    def waitForJobComplete(self,envPath,jobIdentifierList):
          self.logger.info("Waiting for test to complete on zones %s to refresh"%jobIdentifierList)
          jobQueue = Queue.Queue()
          for identifier in jobIdentifierList:
              t = threading.Thread(name='jobWait-%s'%jobIdentifierList.index(identifier), target=self.isJobComplete,
                             args=(jobQueue, ))
              t.setDaemon(True)
              t.start()
          [jobQueue.put([envPath,identifier]) for identifier in jobIdentifierList ]
          jobQueue.join()
          self.logger.info("All test run jobs complete on zones %s`"%jobIdentifierList)
 
    def execOnJenkins(self,env,testSpecifierString,mailto,execOnOneZone=True):
        try:
              testMgr=testManager(testSpecifierString,env['virtenvPath'])
              jobModifier=modifyJOb()
              modifiedjob=""
              j=Jenkins('http://jenkins-ccp.citrix.com','bharatk','BharatK')
              tests=testMgr.getTests()
              if(tests==None):
                raise Exception("found no tests to run")
              while(not tests is None):
                  #trigger a jenkins job.
                  os.chdir(env['virtenvPath'])
                  self.logger.info("launching jenkins TestExecutor Job")
                  #createing testexecutorjobs for each zone.
                  cscfg=configGenerator.getSetupConfig(env['config_file'])
                  jobIdentifierList=[]
                  for zone in cscfg.zones:
                      for pod in zone.pods:
                         for cluster in pod.clusters:
                             modifiedjob=jobModifier.addTests(env['build_number'],tests)
                             file=open("/root/cloud-autodeploy2/newcode/"+modifiedjob,'r')
                             config=file.read()
                             file.close()
                             bash("rm -f /root/cloud-autodeploy2/newcode/%s"%modifiedjob)
                             if(not j.job_exists(modifiedjob)):
                                  j.create_job(modifiedjob,config)
                             else:
                                  j.reconfig_job(modifiedjob,config)
                             j.build_job(modifiedjob, {'BASEDIR':env['virtenvPath'], 'MGMT_SVR' : env['hostip'],'buildNumber':env['build_number'],'zoneName':zone.name,'hypervisor':cluster.hypervisor.lower(),'zoneType':zone.networktype,'configFileName':env['config_file'],'token':'bharat'})
                             jobIdentifierList.append(zone.name)
                             break
                         break
                      if (execOnOneZone):
                        break
                  self.waitForJobComplete(env['virtenvPath'],jobIdentifierList)
                  tests=testMgr.getTests()  

              j.delete_job(modifiedjob) 
              jobIdentifierList=[]
              bugLoggerData=[]
              time.sleep(30)
              for zone in cscfg.zones:
                 self.logger.info(zone.name)
                 for pod in zone.pods:
                     for cluster in pod.clusters:
                         self.logger.info("creating a jeknins job to generate results and email notfication for hypervisor %s and zone %s"%(cluster.hypervisor, zone.name))
                         modifiedjob=jobModifier.modifyReportGenerator(env['build_number']+"_"+zone.name+"_"+cluster.hypervisor, mailto)
                         jobname=modifiedjob
                         file=open("/root/cloud-autodeploy2/newcode/"+modifiedjob,'r')
                         config=file.read()
                         file.close()
                         j.create_job(modifiedjob,config)
                         j.build_job(modifiedjob, {'buildNumber':env['build_number'],'BuildNo':env['build_number'], 'MGMT_SVR' : env['hostip'], 'BASEDIR':env['virtenvPath'], 'version':env['version'], 'BranchInfo':env['version'],\
                         'GitRepoUrl':env['repo_url'],'GitCommitId':env['commit_id'], 'CIRunStartDateTime':env['startTime'],'CIRunEndDateTime':time.strftime("%c"), 'WikiLinks':'https://cwiki.apache.org/confluence/display/CLOUDSTACK/Infrastructure%2CCI%2CSimulator%2CAutomation+Changes','hypervisor':cluster.hypervisor.lower(), 'HyperVisorInfo':cluster.hypervisor.lower(), 'zoneName':zone.name, 'BuildReport':"http://jenkins-ccp.citrix.com/job/"+jobname+"/1/testReport/",'token':'bharat'})
                         jobIdentifierList.append("report_"+zone.name)
                         jobDetails={"job_name":modifiedjob,"related_data_path":env['virtenvPath']}
                         self.resourceMgr.addJobDetails(jobDetails)
                         bugLoggerData.append({'hypervisor':cluster.hypervisor.lower(), 'branch':env['version'],'logname':cluster.hypervisor.lower()+'__Log_'+env['build_number'], 'type':'BVT'})
                         self.logger.info("bug logger data in zone looop %s"%bugLoggerData)
                         break
                     break
                 if (execOnOneZone):
                    #env['hypervisor':cluster.hypervisor.lower()]
                    break  
              self.logger.info("job identifier list", jobIdentifierList)       
              self.waitForJobComplete(env['virtenvPath'],jobIdentifierList)
              #self.logger.info("deleting the reporter job on jenkins job_name=%s",jobname)
              #j.delete_job(jobname)
              self.logger.info("cleaning up the workspace")
              bash("rm -f /root/cloud-autodeploy2/newcode/%s"%modifiedjob)
              self.logger.info("running bug logger")
              #self.runBugLogger(bugLoggerData)
              #os.system("rm -rf %s"%(self.jenkinsWorkspace+"/"+jobname))
        except Exception, e:
               self.logger.error(e) 
        return env
    
    def addBuildInfo(self,env):
        buildInfo={'build_Number':env['build_number'],'repo_url':env['repo_url'],'branch':env['version'],'commit_id':env['commit_id'],'hypervisor':env['hypervisor']}
        self.resourceMgr.addBuildInfo(buildInfo)
  
    def runBugLogger(self, bugLoggerData):
        self.logger.info(" in buglogger function")
        for entry in bugLoggerData:
            #print "executing python2.7 /root/cloud-autodeploy2/newcode/runBugLogger.py -b %s -p %s -l %s -t %s"%(entry['branch'], entry['hypervisor'], entry['logname'], entry['type'])
            os.system("python2.7 /root/cloud-autodeploy2/newcode/runBugLogger.py -b %s -p %s -l %s -t %s"%(entry['branch'], entry['hypervisor'], entry['logname'], entry['type'])) 

            
class testManager():
   '''coma seperated values testSpecifierString   
      format of testSpecifier string p1:p2:p3:x-e1-e2-e3,t1:t2:t3-a1-a2-a3
      The testcases found in p1,p2,p3 will be filtered based on e1,e2,e3 
      exclude list and run at a time. Tests t{x}  will be run after 
      running the p{x} tests. There will be no ordering amoung the tests
      p{x} them selves. If the file path itsef has'-' charecters escape them
      using '\' '''
   
   def __init__(self,testSpecifierString,virtEnvPath):
       self.testSpecifierString=testSpecifierString
       self.virtEnvPath=virtEnvPath
       self.testDict={}
       self.excludeDict={}
       self._parseSpecifierStrings()

   def _mask(self,path):
       return path.replace('\-','\\')

   def _unmask(self,path):
      return path.replace('\\','-')    
   
   def _parseSpecifierStrings(self):
       i=1
       self.testSpecifierString=self._mask(self.testSpecifierString)
       for testSpecifier in self.testSpecifierString.split(","):
           values=testSpecifier.split('-')
           testpaths=[]
           for path in values[0].split(':'):
               testpaths.append(self._unmask(path))
           self.testDict.update({i:list(set(testpaths))})
           excludeList=[]
           for val in values[1:]:
               excludeList.append(self._unmask(val))
           self.excludeDict.update({i:list(set(excludeList))})
           i=i+1

   def _verify(self,listOfPaths):
        #print listOfPaths
        for i in range(0,len(listOfPaths)):
          if(not os.path.exists(listOfPaths[i])):
            path=os.path.join(self.virtEnvPath,listOfPaths[i])
            #print path
            if(os.path.exists(path)):
              listOfPaths[i]=path
            else: 
              raise Exception("path:%s dose not exist"%path)

   def _getTestSuits(self,listOfpaths):
       tests=[]
       paths=list(listOfpaths)
       while(len(paths)>0):
           if(not os.path.exists(paths[0]) and (not os.path.exists(os.path.join(self.virtEnvPath,paths[0]))) and (paths[0].find("test")==0)):
             tests.append(self._getBaseName(paths[0]))
             listOfpaths.remove(paths[0])
           del paths[0] 
       #print "direct test names=%s"%tests
       #print "list of paths %s"%listOfpaths
       return tests
    
   def _getBaseName(self,path):
       while(True):
          t=os.path.split(path)
          if(t[1] is ''):
              path=t[0]
          else:
             return t[1]
                 
   def _findTests(self,listOfPaths):
        listOfTests=[]
        for path in listOfPaths:
          if(os.path.isdir(path)):
            for root, dirs, files in os.walk(path):
              for suit in files:
                 #name of the test suit should begin with test
                 if(suit.find("test")==0):
                     listOfTests.append(suit)
          else:
               path=self._getBaseName(path)
               if(path.find("test")==0):
                     listOfTests.append(path)
        return listOfTests 
              
   def getTests(self):
      excludeTests=[]
      if(len(self.testDict.keys())<=0):
        return
      listOfTestPaths=self.testDict[self.testDict.keys()[0]]
      del self.testDict[self.testDict.keys()[0]]
      if(len(self.excludeDict.keys())>0):
         excludeTestPaths=self.excludeDict[self.excludeDict.keys()[0]]
         del self.excludeDict[self.excludeDict.keys()[0]]
      self._verify(listOfTestPaths)
      for test in self._getTestSuits(excludeTestPaths):
            excludeTests.append(test)
      self._verify(excludeTestPaths)
      listOfTests=self._findTests(listOfTestPaths)
      for test in self._findTests(excludeTestPaths):
           excludeTests.append(test)
      for test in excludeTests:
        try:
           listOfTests.remove(test)
        except:
              pass
      for i in range(0,len(listOfTests)):
          listOfTests[i]=listOfTests[i].replace(".py","")
      return listOfTests if (len(listOfTests)!=0) else None
      
