#Embedded file name: /root/cloud-autodeploy2/newcode/testEnv.py
import os
from paramiko import SSHClient, AutoAddPolicy
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
from analyseReport import reportAnalyser
from git_CI import github
import re

class testEnv:

    def __init__(self):
        self.workDir = '/automation/virtenv'
        self.marvinPath = '/automation/cloudstack/tools/marvin/dist/'
        self.testcasePath = '/automation/cloudstack/test'
        self.pythonPath = ''
        self.libPath = "/root/cloud-autodeploy2/newcode"
        self.jenkinsWorkspace = '/automation/jenkins/workspace'
        self.logger = logging.getLogger('testEnvMgr')
        self.resourceMgr = resourceManager()
        self.throttle_job_count = 13

    def initLogging(self, logFile = None, lvl = logging.INFO):
        try:
            if logFile is None:
                logging.basicConfig(level=lvl, format="'%(asctime)-6s: %(name)s                                 (%(threadName)s) - %(levelname)s - %(message)s'")
            else:
                logging.basicConfig(filename=logFile, level=lvl, format="'%(asctime)-6s: %(name)s                                 (%(threadName)s) - %(levelname)s - %(message)s'")
        except:
            logging.basicConfig(level=lvl)

    def create(self, hostInfo, build_number, version, logPath = None):
        configFilePath = hostInfo['configfile']
        os.chdir(self.workDir)
        if not os.path.isdir(self.workDir + '/' + hostInfo['mac'].replace(':', '-')):
            os.mkdir(hostInfo['mac'].replace(':', '-'))
        virtenvPath = self.workDir + '/' + hostInfo['mac'].replace(':', '-') + '/' + build_number
        if os.path.isdir(virtenvPath):
            os.system('rm -rf %s' % virtenvPath)
        os.system('mkdir -p %s' % virtenvPath)
        os.chdir(virtenvPath)
        bash('virtualenv testenv')
        self.logger.info('created virtual test environment')
        ssh = SSHClient()
        ssh.set_missing_host_key_policy(AutoAddPolicy())
        ssh.connect(hostname=hostInfo['hostname'], username='root', password=hostInfo['password'])
        scp = SCPClient(ssh.get_transport())
        scp.get(self.marvinPath, './dist/', recursive=True)
        self.pythonPath = virtenvPath + '/testenv/bin/'
        bash('wget http://cdn.mysql.com/Downloads/Connector-Python/mysql-connector-python-2.0.4.zip#md5=3df394d89300db95163f17c843ef49df')
        bash('%s/easy_install mysql-connector-python-2.0.4.zip' % self.pythonPath)
        marvinName = bash('ls ./dist/ | grep Marvin.*tar.gz').getStdout()
        bash('tar -xf ./dist/%s' % marvinName)
        scp.get(self.testcasePath, './', recursive=True)
        self.logger.info('executing %s install -e %s/%s' % (self.pythonPath + 'pip2.7', virtenvPath, marvinName.replace('.tar.gz', '')))
        os.system('%s install -e %s/%s ' % (self.pythonPath + 'pip2.7', virtenvPath, marvinName.replace('.tar.gz', '')))
        configFileName = hostInfo['mac'].replace(':', '-') + '.cfg'
        bash('cp %s ./%s' % (configFilePath, configFileName))
        bash("sed -i 's/10.147.28.149/%s/g' %s" % (hostInfo['hostname'], virtenvPath + '/' + configFileName))
        if logPath == None:
            logPath = virtenvPath.replace('/', '\\/') + '\\/results'
        bash("sed -i 's/\\/tmp\\/cloudstack/%s/g' %s" % (logPath, virtenvPath + '/' + configFileName))
        env = {'pythonPath': self.pythonPath,
         'config_file': configFileName,
         'virtenvPath': virtenvPath,
         'hostip': hostInfo['ip'],
         'build_number': build_number,
         'version': version,
         'noSimulator': hostInfo['noSimulator'],
         'repo_url': hostInfo['repo_url'],
         'startTime': hostInfo['startTime'],
         'commit_id': hostInfo['commit_id']}
        self.logger.info('Adding environment specific data to %s/testenv/lib/python2.7/site-packages/marvin/config/test_data.py' % virtenvPath)
        bash('/root/cloud-autodeploy2/newcode/editTestdata.sh /root/cloud-autodeploy2/newcode/env_specific_test_data %s/%s/marvin/config/test_data.py' % (virtenvPath, marvinName.replace('.tar.gz', '')))
        return env

    def createDataCenter(self, env, tag = None):
        try:
            os.chdir(env['virtenvPath'])
            marvin_config = env['config_file']
            pythonPath = env['pythonPath']
            self.logger.info('Deploying datacenter using marvin')
            marvinFolder = bash('ls | grep Marvin-[0-9].[0-9].[0-9]').getStdout()
            subprocess.check_call('%s/nosetests-2.7 -v --with-marvin --marvin-config=%s --deploy -w /tmp' % (pythonPath, marvin_config), shell=True)
            self.logger.info('Testing if setup is ready')
            subprocess.check_call('%s/nosetests-2.7 -v --with-marvin --marvin-config=%s /root/cloud-autodeploy2/newcode/testSetupSuccess.py' % (pythonPath, marvin_config), shell=True)
            self.logger.info('Restarting Management server for global setting changes to take effect')
            subprocess.check_call('%s/python2.7 /root/cloud-autodeploy2/newcode/restartMgmt.py --config  %s --noSimulator %s' % (pythonPath, marvin_config, env['noSimulator']), shell=True)
            self.logger.info('Waiting some time for managementserver startup')
            time.sleep(120)
        except Exception as e:
            self.logger.info('error occured while deploying datacenter.')
            self.logger.exception(e)
            raise Exception("failed to create datacenter")

    def execTests(self, env, noOfExecutors, tag = None):
        try:
            testMgr = testManager(testSpecifierString, env['virtenvPath'])
            tests = testMgr.getTests()
            while tests is not None:
                if tests.__len__() < noOfExecutors:
                    noOfExecutors = tests.__len__()
                pool = Pool(processes=noOfExecutors)

            self.logger.info('Launching integration tests after a sleep')
            self.logger.info('%s/nosetests-2.7 -v --with-marvin --marvin-config=%s -w ./test/integration/smoke  --load --with-xunit %s' % (pythonPath, marvin_config, '' if tag == None else '-a tag=%s' % tag))
            subprocess.check_out('%s/nosetests-2.7 -v --with-marvin --marvin-config=%s -w ./test/integration/smoke  --load --with-xunit %s' % (pythonPath, marvin_config, '' if tag == None else '-a tag=%s' % tag), shell=True)
        except Exception as e:
            self.info.error(e)

    def isJobComplete(self, queue):
        args = queue.get()
        envPath = args[0]
        jobIdentifier = args[1]
        while not os.path.isdir(envPath + '/' + '%sComplete' % jobIdentifier):
            self.logger.debug('testing on zone %s is in progress' % jobIdentifier)
            time.sleep(20)

        queue.task_done()
        bash('rm -rf %s/%sComplete' % (envPath, jobIdentifier))

    def waitForJobComplete(self, envPath, jobIdentifierList):
        self.logger.info('Waiting for test to complete on zones %s to refresh' % jobIdentifierList)
        jobQueue = Queue.Queue()
        for identifier in jobIdentifierList:
            t = threading.Thread(name='jobWait-%s' % jobIdentifierList.index(identifier), target=self.isJobComplete, args=(jobQueue,))
            t.setDaemon(True)
            t.start()

        [ jobQueue.put([envPath, identifier]) for identifier in jobIdentifierList ]
        jobQueue.join()
        self.logger.info('All test run jobs complete on zones %s`' % jobIdentifierList)

    def archiveTestRunLogs(self, env, hypervisor, reportGeneratorBuildName):
        self.logger.info('sh  %s/archive_test_results.sh %s %s %s %s %s %s %s' % (self.libPath, env['virtenvPath'],
         hypervisor,
         '%s/%s' % (self.jenkinsWorkspace, reportGeneratorBuildName),
         env['build_number'],
         '%s/%s' % (env['virtenvPath'], hypervisor),
         env['branch'],
         env['hostip']))
        bash('sh %s/archive_test_results.sh %s %s %s %s %s %s %s >> /var/log/test_archive.log 2>&1' % (self.libPath, env['virtenvPath'],
         hypervisor,
         '%s/%s' % (self.jenkinsWorkspace, reportGeneratorBuildName),
         env['build_number'],
         '%s/%s' % (env['virtenvPath'], hypervisor),
         env['branch'],
         env['hostip']))

    def execOnJenkins(self, env, testSpecifierString, mailto, reRunFailedTests=True, retryCount=1, report=True, execOnOneZone=True,
           postOnPr=False, testMgr=None, avoidZones=None):
        try:
            env['hypervisor'] = ''
            if avoidZones is None:
               avoidZones=[]
            if testMgr is None:
               testMgr = testManager(testSpecifierString, env['virtenvPath'])
            jobModifier = modifyJOb()
            modifiedjob = ''
            j = Jenkins('http://jenkins-ccp.citrix.com', 'bharatk', 'BharatK')
            tests = testMgr.getTests()
            if tests == None:
                raise Exception('found no tests to run')
            while tests is not None:
                os.chdir(env['virtenvPath'])
                self.logger.info('launching jenkins TestExecutor Job')
                cscfg = configGenerator.getSetupConfig(env['config_file'])
                for zone in cscfg.zones:
                    if zone.name in avoidZones:
                       continue
                    for pod in zone.pods:
                        for cluster in pod.clusters:
                            for modifiedjob in jobModifier.addTests(env['build_number'], tests, self.throttle_job_count):
                                file = open('/root/cloud-autodeploy2/newcode/' + modifiedjob, 'r')
                                config = file.read()
                                file.close()
                                bash('rm -f /root/cloud-autodeploy2/newcode/%s' % modifiedjob)
                                if not j.job_exists(modifiedjob):
                                    j.create_job(modifiedjob, config)
                                else:
                                    j.delete_job(modifiedjob)
                                    j.create_job(modifiedjob, config)
                                j.build_job(modifiedjob, {'BASEDIR': env['virtenvPath'],
                                 'MGMT_SVR': env['hostip'],
                                 'buildNumber': env['build_number'],
                                 'zoneName': zone.name,
                                 'hypervisor': cluster.hypervisor.lower(),
                                 'zoneType': zone.networktype,
                                 'configFileName': env['config_file'],
                                 'token': 'bharat'})
                                self.waitForJobComplete(env['virtenvPath'], [zone.name])
                                env['hypervisor'] = '%s,%s' % (env['hypervisor'], cluster.hypervisor.lower())

                            break

                        break

                    if execOnOneZone:
                        break

                tests = testMgr.getTests()

            j.delete_job(modifiedjob)

            reportAnalyserMap=self.getReportAnalysers(cscfg, env, execOnOneZone)
            if(reRunFailedTests):
               while retryCount > 0:
                     self.logger.info("checking if we need to re run any of the tests")
                     testsToReRun=[]
                     for key in reportAnalyserMap.keys():
                         tests=reportAnalyserMap[key].suitsToRerun
                         if(tests is None):
                            avoidZones.append(key)
                         else:
                            testMgr.addTestsToReRun(tests)
                     retryCount-=1
                     self.logger.info("zone name:%s The follwoing tests will be re run %s"%(key,tests))
                     if(len(testsToReRun)==0):
                       break
                     else:
                        self.execOnJenkins(env, testSpecifierString, mailto, reRunFailedTests, retryCount, False, execOnOneZone, postOnPr, testMgr, avoidZones)

            if report and postOnPr:
                for key in reportAnalyserMap.keys():
                    self.reportOnPr(reportAnalyserMap[key].generateTextReport2(), env)
            elif report:
                self.reportUsingJenkinsEmailPlugin(cscfg, env)
            return env
        except Exception as e:
            self.logger.exception(e)

    def getReportAnalysers(self,cloudstack_config, env, execOnOneZone=True):
        reportAnalyserMap={}
        for zone in cloudstack_config.zones:
            for pod in zone.pods:
                for cluster in pod.clusters:
                    bash('mkdir -p %s' % ('%s/report_generator_%s_%s_%s/%s/%s' % (self.jenkinsWorkspace,
                     env['build_number'],
                     cluster.hypervisor.lower(),
                     zone.name,
                     cluster.hypervisor.lower(),
                     'reports')))
                    self.archiveTestRunLogs(env, cluster.hypervisor.lower(), 'report_generator_%s_%s_%s' % (env['build_number'], cluster.hypervisor.lower(), zone.name))
                    self.logger.info('Generating plain text report')
                    report = reportAnalyser(env['virtenvPath'], os.path.join(self.jenkinsWorkspace, 'report_generator_%s_%s_%s' % (env['build_number'], cluster.hypervisor.lower(), zone.name), cluster.hypervisor.lower(), 'reports'), env['config_file'], cluster.hypervisor.lower(), zone.networktype, env['build_number'])
                    reportAnalyserMap.update({zone.name:report})
                    break

                break

            if execOnOneZone:
                break
        return reportAnalyserMap

    def reportOnPr(self, textReport, env ):
        retry=3
        while retry > 0:
            try:
               g = github()
               g.commentOnPr(long(env['version']), textReport)
               break
            except Exception as e:
               self.logger.error("unexpected error occured, error message: %s"%(e))
               time.sleep(120)
               retry=retry-1

    def reportUsingJenkinsEmailPlugin(self, marvinConfigJson, env, execOnOneZone = True):
        try:
            jobIdentifierList = []
            bugLoggerData = []
            j = Jenkins('http://jenkins-ccp.citrix.com', 'bharatk', 'BharatK')
            for zone in cscfg.zones:
                self.logger.info(zone.name)
                for pod in zone.pods:
                    for cluster in pod.clusters:
                        self.logger.info('creating a jeknins job to generate results and email notfication for hypervisor %s and zone %s' % (cluster.hypervisor, zone.name))
                        modifiedjob = jobModifier.modifyReportGenerator(env['build_number'] + '_' + zone.name + '_' + cluster.hypervisor, mailto)
                        jobname = modifiedjob
                        file = open('/root/cloud-autodeploy2/newcode/' + modifiedjob, 'r')
                        config = file.read()
                        file.close()
                        j.create_job(modifiedjob, config)
                        j.build_job(modifiedjob, {'buildNumber': env['build_number'],
                         'BuildNo': env['build_number'],
                         'MGMT_SVR': env['hostip'],
                         'BASEDIR': env['virtenvPath'],
                         'version': env['version'],
                         'BranchInfo': env['version'],
                         'GitRepoUrl': env['repo_url'],
                         'GitCommitId': env['commit_id'],
                         'CIRunStartDateTime': env['startTime'],
                         'CIRunEndDateTime': time.strftime('%c'),
                         'WikiLinks': 'https://cwiki.apache.org/confluence/display/CLOUDSTACK/Infrastructure%2CCI%2CSimulator%2CAutomation+Changes',
                         'hypervisor': cluster.hypervisor.lower(),
                         'HyperVisorInfo': cluster.hypervisor.lower(),
                         'zoneName': zone.name,
                         'BuildReport': 'https://www.dropbox.com/sh/yj3wnzbceo9uef2/AAB6u-Iap-xztdm6jHX9SjPja?dl=0',
                         'token': 'bharat'})
                        jobIdentifierList.append('report_' + zone.name)
                        jobDetails = {'job_name': modifiedjob,
                         'related_data_path': env['virtenvPath']}
                        self.resourceMgr.addJobDetails(jobDetails)
                        bugLoggerData.append({'hypervisor': cluster.hypervisor.lower(),
                         'branch': env['version'],
                         'logname': cluster.hypervisor.lower() + '__Log_' + env['build_number'],
                         'type': 'BVT'})
                        self.logger.info('bug logger data in zone looop %s' % bugLoggerData)
                        self.waitForJobComplete(env['virtenvPath'], jobIdentifierList)
                        self.archiveTestRunLogs(env, cluster.hypervisor.lower(), jobname)
                        break

                    break

                if execOnOneZone:
                    break
                self.logger.info('job identifier list %s' % jobIdentifierList)
                self.logger.info('cleaning up the workspace')
                bash('rm -f /root/cloud-autodeploy2/newcode/%s' % modifiedjob)
                self.logger.info('running bug logger')

        except Exception as e:
            self.logger.exception(e)

    def addBuildInfo(self, env):
        buildInfo = {'build_number': env['build_number'],
         'repo_url': env['repo_url'],
         'branch': env['version'],
         'commit_id': env['commit_id'],
         'hypervisor': env['hypervisor']}
        self.resourceMgr.addBuildInfo(buildInfo)

    def runBugLogger(self, bugLoggerData):
        self.logger.info(' in buglogger function')
        for entry in bugLoggerData:
            os.system('python2.7 /root/cloud-autodeploy2/newcode/runBugLogger.py -b %s -p %s -l %s -t %s' % (entry['branch'],
             entry['hypervisor'],
             entry['logname'],
             entry['type']))


class testManager:
    """coma seperated values testSpecifierString
    format of testSpecifier string p1:p2:p3:x-e1-e2-e3,t1:t2:t3-a1-a2-a3
    The testcases found in p1,p2,p3 will be filtered based on e1,e2,e3
    exclude list and run at a time. Tests t{x}  will be run after
    running the p{x} tests. There will be no ordering amoung the tests
    p{x} them selves. If the file path itsef has'-' charecters escape them
    using '' """

    def __init__(self, testSpecifierString, virtEnvPath):
        self.testSpecifierString = testSpecifierString
        self.virtEnvPath = virtEnvPath
        self.testDict = {}
        self.excludeDict = {}
        self._parseSpecifierStrings()
        self.testsToReRun=None
        self.test_file_format=re.compile('^test_.*\.py$', re.IGNORECASE)

    def addTestsToReRun(self, testList):
        if(testList is None):
           return
        self.testsToReRun=[]
        for test in testList:
            test=test.replace(".py","")
            self.testsToReRun.append(test)

    def _mask(self, path):
        return path.replace('\\-', '\\')

    def _unmask(self, path):
        return path.replace('\\', '-')

    def _parseSpecifierStrings(self):
        i = 1
        self.testSpecifierString = self._mask(self.testSpecifierString)
        for testSpecifier in self.testSpecifierString.split(','):
            values = testSpecifier.split('-')
            testpaths = []
            for path in values[0].split(':'):
                testpaths.append(self._unmask(path))

            self.testDict.update({i: list(set(testpaths))})
            excludeList = []
            for val in values[1:]:
                excludeList.append(self._unmask(val))

            self.excludeDict.update({i: list(set(excludeList))})
            i = i + 1

    def _verify(self, listOfPaths):
        for i in range(0, len(listOfPaths)):
            if not os.path.exists(listOfPaths[i]):
                path = os.path.join(self.virtEnvPath, listOfPaths[i])
                if os.path.exists(path):
                    listOfPaths[i] = path
                else:
                    raise Exception('path:%s dose not exist' % path)

    def _getTestSuits(self, listOfpaths):
        tests = []
        paths = list(listOfpaths)
        while len(paths) > 0:
            if not os.path.exists(paths[0]) and not os.path.exists(os.path.join(self.virtEnvPath, paths[0])) and paths[0].find('test') == 0:
                if(self.test_file_format.search(self._getBaseName(paths[0]))):
                  tests.append(self._getBaseName(paths[0]))
                listOfpaths.remove(paths[0])
            del paths[0]

        return tests

    def _getBaseName(self, path):
        while True:
            t = os.path.split(path)
            if t[1] is '':
                path = t[0]
            else:
                return t[1]

    def _findTests(self, listOfPaths):
        listOfTests = []
        for path in listOfPaths:
            if os.path.isdir(path):
               suits=filter(self.test_file_format.search, os.listdir(path))
               for suit in suits:
                   listOfTests.append(suit)

            else:
                path = self._getBaseName(path)
                if self.test_file_format.search(path):
                    listOfTests.append(path)

        return listOfTests

    def getTests(self):
        print "self.testsToReRun=",self.testsToReRun
        if(self.testsToReRun is not None and len(self.testsToReRun)!=0):
           return self.getTestsToReRun()
        else:
           return self.getTestsToRun()

    def getTestsToRun(self):
        excludeTests = []
        if len(self.testDict.keys()) == 0:
           return None
        listOfTestPaths = self.testDict[self.testDict.keys()[0]]
        del self.testDict[self.testDict.keys()[0]]
        if len(self.excludeDict.keys()) > 0:
             excludeTestPaths = self.excludeDict[self.excludeDict.keys()[0]]
             del self.excludeDict[self.excludeDict.keys()[0]]
        self._verify(listOfTestPaths)
        for test in self._getTestSuits(excludeTestPaths):
            excludeTests.append(test)

        #self._verify(excludeTestPaths)
        listOfTests = self._findTests(listOfTestPaths)
        #for test in self._findTests(excludeTestPaths):
        #excludeTests.append(test)

        for test in excludeTests:
           try:
               listOfTests.remove(test)
           except:
               pass

        for i in range(0, len(listOfTests)):
              listOfTests[i] = listOfTests[i].replace('.py', '')

        if len(listOfTests) != 0:
               return listOfTests


    def getTestsToReRun(self):
        print ("getting tests to rerun")
        if(self.testsToReRun is None):
          return None
        tests=[]
        self._parseSpecifierStrings()
        testBatch=self.getTestsToRun()
        while testBatch is not None:
            for test in self.testsToReRun:
               #print 'test=%s'%test
               if test in testBatch:
                  tests.append(test)
                  #print test
            if(len(tests)>0):
              break
            testBatch=self.getTestsToRun()
        for test in tests:
            self.testsToReRun.remove(test)
        self.testDict={}
        #print "testsToRerun=%s"%tests
        if(len(tests)==0):
           return None
        return tests
