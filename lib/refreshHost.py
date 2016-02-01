import sys
from optparse import OptionParser
import os
from os import chdir
import subprocess
import shlex
import time
codes = {'FAILED':1,'SUCCESS':0}

def parse_options():
    try:
        parser = OptionParser()
        parser.add_option("-b", "--branch", action="store",
                          default="master", dest="branch_no",
                          help="The branch used for this coverage Information")
        parser.add_option("-c", "--commit", action="store",
                          default="", dest="commit_id",
                          help="The Commit id used for to retrieve coverage")
        parser.add_option("-n", "--fqdn", action="store",
                          default="", dest="hostname",
                          help="fully qualified domain name of the host")
        parser.add_option("-p","--package", action="store",
                          default="False", dest="package",
                          help="will package cloudstack if package is true")
        
        parser.add_option("-s","--skip-tests", action="store",
                          default="False", dest="skipTests",
                          help="will skipTests if true")

        parser.add_option("--noSimulator",action="store",
                          default=False, dest="noSimulator",
                          help="will not buid sumulator if set to true")

        (options,args) = parser.parse_args()
        options.package=parseBoolOpts(options.package)
        options.noSimulator=parseBoolOpts(options.noSimulator)
 
        return {"branch":options.branch_no,"commit":options.commit_id,"hostname":options.hostname,"package":options.package,"skipTests":options.skipTests,"noSimulator":options.noSimulator}
    except Exception, e:
        print "\nException Occurred %s. Please Check" %(e)
        return codes['FAILED']

def parseBoolOpts(value):
     if (value.lower()=="false" or value==None):
         value=False
     else:
          value=True
     return value

def init():
    try:
        options_dict = parse_options()
        return options_dict
    except Exception, e:
        print "\nException Occurred under init. Please Check:%s" %(e)
        sys.exit(1)


def execCmd(cmd):
    pipe = subprocess.PIPE
    print shlex.split(cmd)
    proc = subprocess.check_call(shlex.split(cmd))
    return proc 

def buildSimulator(inp_dict,retryBuild):
    out=None
    while (out!=0 and retryBuild!=0):
          try:
              out=execCmd("mvn clean install -P developer,systemvm -Dsimulator %s"%("-DskipTests" if inp_dict['skipTests'] else ""))
          except Exception, e:
                 print ("mvn clean  install failed, will retry")
          retryBuild=retryBuild-1
    print "************************out=***************",out
    if out!=0:
       sys.exit(1)
    try:
        execCmd("mvn -Pdeveloper -pl developer -Ddeploydb %s"%("-DskipTests" if inp_dict['skipTests'] else ""))
        os.system("mvn -Pdeveloper -pl developer -Ddeploydb-simulator %s"%("-DskipTests" if inp_dict['skipTests'] else ""))
    except Exception, e:
        print "****************************Deploydb Failed********************"
        print e
        sys.exit(1)

def buildNoSimulator(inp_dict,retryBuild):
    out=None
    while (out!=0 and retryBuild!=0):
          try:
              out=execCmd("mvn clean install -P developer,systemvm  %s"%("-DskipTests" if inp_dict['skipTests'] else ""))
          except Exception, e:
                 print ("mvn clean  install failed, will retry")
          retryBuild=retryBuild-1
    print "************************out=***************",out
    if out!=0:
       sys.exit(1)
    try:
        execCmd("mvn -Pdeveloper -pl developer -Ddeploydb %s"%("-DskipTests" if inp_dict['skipTests'] else ""))
    except Exception, e:
        print "****************************Deploydb Failed********************"
        print e
        sys.exit(1)

def getCSCode(inp_dict):
    os.chdir("/automation/cloudstack")
    os.system("killall -9 java")
    time.sleep(20)
    print "inp_dict",  inp_dict
    if os.system("git checkout -b temp_branch")!=0:
       os.system("git checkout temp_branch")
    os.system("git branch -D %s"%inp_dict['branch'])
    os.system("git fetch origin %s"%inp_dict['branch'])
    os.system("git checkout -b %s FETCH_HEAD"%inp_dict['branch'])
    if (inp_dict['commit'] !=""):
       os.system("git reset --hard %s"%inp_dict['commit'])
    commit_id=output=subprocess.Popen("git log | grep -m 1 'commit' | cut -f 2 -d ' '", stdout=subprocess.PIPE, shell=True).communicate()[0].replace('\n','')
    print "building from commit_id %s"%commit_id
    os.system("mysql -uroot  -e \"GRANT ALL PRIVILEGES ON *.* TO 'root'@\'%s\' WITH GRANT OPTION \""%(inp_dict['hostname']))
   
    if (inp_dict['package']):
       os.system('mvn clean')     
       os.chdir('/automation/cloudstack/packaging/centos63/')
       os.system('sh package.sh')
       os.system('mkdir /root/cloudstack-repo')
       os.system('mv /automation/cloudstack/dist/rpmbuild/RPMS/x86_64/* /root/cloudstack-repo')
       os.chdir('/automation/cloudstack') 

    #flushing vmops.log
    os.system("echo > /automation/cloudstack/vmops.log")
    if (inp_dict['noSimulator']):
        buildNoSimulator(inp_dict,retryBuild=2)
    else:
        buildSimulator(inp_dict,retryBuild=2)
    
    if (inp_dict['noSimulator']):
      os.system("mvn -pl :cloud-client-ui jetty:run &")
    else:
       os.system("mvn -Dsimulator -pl client jetty:run &")
    return commit_id

def main():
     ret = init()
     return getCSCode(ret)


if __name__ == '__main__':
     main()        
