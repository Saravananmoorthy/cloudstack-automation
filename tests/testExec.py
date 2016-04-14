from optparse import OptionParser
from bashUtils import bash
import os
import logging

global options
options=None
try:
    parser = OptionParser()
    parser.add_option("-b", "--basedir", action="store",
                       default="", dest="BASEDIR",
                       help="path to the xml remports")
    parser.add_option("--hypervisor", action="store",
                        default="", dest="hypervisor",
                        help="type of hypervisor")
    parser.add_option("-s", "--suite", action="store",
                        default="", dest="suite",
                        help="name of the test suite")
    parser.add_option("-t", "--zoneType", action="store",
                        default="", dest="zoneType",
                        help="network type of the zone")
    parser.add_option("-c", "--configfile", action="store",
                        default="", dest="configfile",
                        help="name of the marvin config file")
    parser.add_option("-n", "--zoneName", action="store",
                        default="", dest="zoneName",
                        help="name of the zone")
    (options,args) = parser.parse_args()

except Exception,e: 
       print e

logging.basicConfig()

os.chdir(options.BASEDIR)
#os.mkdir(options.BASEDIR+"/"+options.zoneName)

'''if options.hypervisor == "simulator":
     Tag="tags=advanced,required_hardware=false,'!BugId'"
else:
     Tag="tags=%s,required_hardware=true,'!BugId'"%options.zoneType.lower()'''

Tag="tags=%s"%options.zoneType.lower()

'''cmd= "%s/testenv/bin/nosetests-2.7 --with-xunit --xunit-file=%s.xml --with-marvin --marvin-config=%s %s/test/integration/smoke/%s.py -a %s  --zone=%s  --hypervisor=%s --log-folder-path=%s/%s/%s/results"%(options.BASEDIR,options.suite,options.BASEDIR+"/"+options.configfile,options.BASEDIR,options.suite,Tag,options.zoneName,options.hypervisor,options.BASEDIR,options.hypervisor,options.suite)'''


#not running based on tags.
cmd= "%s/testenv/bin/nosetests-2.7 --with-xunit --xunit-file=%s.xml --with-marvin --marvin-config=%s %s/test/integration/smoke/%s.py -a %s  --zone=%s  --hypervisor=%s --log-folder-path=%s/%s/%s/results"%(options.BASEDIR,options.suite,options.BASEDIR+"/"+options.configfile,options.BASEDIR,options.suite,Tag,options.zoneName,options.hypervisor,options.BASEDIR,options.hypervisor,options.suite)
print cmd


out=bash(cmd,timeout=5000)

print out
print out.getStdout()
print "received on stderror: %s"%out.getStderr()

bash("mkdir -p %s/reports"%os.environ['WORKSPACE'])
bash("mkdir -p %s/%s/reports/"%(options.hypervisor,options.suite))
bash("cp %s.xml %s/%s/reports/"%(options.suite,options.hypervisor,options.suite))
bash("cp %s.xml %s/reports"%(options.suite,os.environ['WORKSPACE']))
bash("rm -f %s.xml"%options.suite)

