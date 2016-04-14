from testEnv import testManager
testMgr=testManager('test/integration/smoke-test/integration/smoke/misc-test_ssvm.py-test_nuage_vsp.py,test/integration/smoke/test_ssvm.py','/automation/virtenv/00-16-3e-17-43-25/158/')
tests=testMgr.getTests()
#print tests
tests=testMgr.getTests()
#print tests
rerunTests=['test_nic_adapter_type.py','test_ssvm.py']
testMgr.addTestsToReRun(rerunTests)
#print "added tests= %s"%testMgr.testsToReRun
test1=testMgr.getTests() 
test2=testMgr.getTests()
print test1
print test2
