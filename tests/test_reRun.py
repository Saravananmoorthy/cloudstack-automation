from testEnv import testEnv,testManager
from marvin import configGenerator

env = {'pythonPath': '/automation/virtenv/00-16-3e-17-43-25/146/testenv/bin',
         'config_file': '/automation/virtenv/00-16-3e-17-43-25/146/00-16-3e-17-43-25.cfg',
         'virtenvPath': '/automation/virtenv/00-16-3e-17-43-25/158',
         'hostip': '10.147.28.221',
         'build_number': '158',
         'version': '1254',
         'noSimulator': True,
         'repo_url': 'https://github.com/apache/cloudstack.git',
         'startTime': '',
         'commit_id': None,
         'branch':'1254' }

cscfg = configGenerator.getSetupConfig(env['config_file'])
testMgr = testManager('test/integration/smoke-test/integration/smoke/misc-test_ssvm.py-test_nuage_vsp.py,test/integration/smoke/test_ssvm.py', env['virtenvPath'])
tests=testMgr.getTests()
print "tests=  ",tests
tests=testMgr.getTests()
print "tests=  ",tests
reportAnalyserMap=testEnv().getReportAnalysers(cscfg, env, True)
print reportAnalyserMap
for key in reportAnalyserMap.keys():
                         reportAnalyserMap[key].collectTestsToReRun()
                         tests=reportAnalyserMap[key].suitsToRerun
                         if(tests is None):
                            avoidZones.append(key)
                         else:
                            #print "tests to rerun",tests
                            testMgr.addTestsToReRun(tests)
while tests is not None:
      tests=testMgr.getTests() 
      print tests
