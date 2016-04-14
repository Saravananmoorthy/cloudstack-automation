import sys
from optparse import OptionParser
import os
from os import chdir
import subprocess
import shlex
codes = {'FAILED':1,'SUCCESS':0}

def parse_options():
    try:
        parser = OptionParser()
        parser.add_option("-u", "--repo_url", action="store",
                          default="", dest="repo_url",
                          help="The branch used for this coverage Information")
        parser.add_option("-b", "--branch", action="store",
                          default="master", dest="branch_no",
                          help="The branch used for this coverage Information")
        parser.add_option("-c", "--commit", action="store",
                          default=None, dest="commit_id",
                          help="The Commit id used for to retrieve coverage")
        parser.add_option("-n", "--fqdn", action="store",
                          default="", dest="hostname",
                          help="fully qualified domain name of the host")
        parser.add_option("-s","--skipTests", action="store",
                          default=False, dest="skipTests",
                          help="skip unit tests while building")
        parser.add_option("-p","--package", action="store",
                          default=False, dest="package",
                          help="will package cloudstack if package is true")
        parser.add_option("-k","--noSimulator", action="store",
                          default=False, dest="noSimulator",
                          help="will not buid sumulator if set to true")
        parser.add_option("-o","--buildOffline", action="store",
                          default=False, dest="buildOffline",
                          help="will force maven to build offline")
        parser.add_option("","--githubPrno", action="store",
                          default=None, dest="githubPrno",
                          help="git hub pr number")
        (options,args) = parser.parse_args()
        options.package=parseBoolOpts(options.package)
        options.noSimulator=parseBoolOpts(options.noSimulator)       
     
        return {"repo_url":options.repo_url,"branch":options.branch_no,"commit":options.commit_id,"hostname":options.hostname, "skipTests":options.skipTests, "package":options.package,"noSimulator":options.noSimulator,"buildOffline":options.buildOffline,"githubPrno":options.githubPrno}
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
    print proc
    print dir(proc)
    return proc 


def buildSimulator(inp_dict,retryBuild):
    out=None
    print "building simulator"
    while (out!=0 and retryBuild!=0):
          try:
              out=execCmd("mvn clean install -P developer,systemvm -Dsimulator %s %s"%("-DskipTests" if inp_dict['skipTests'] else "", "-o" if inp_dict['buildOffline'] else ""))
          except Exception, e:
                 print ("mvn clean  install failed, will retry")
                 print e
          retryBuild=retryBuild-1
    print "************************out=***************",out
    if out!=0:
       return 1 
    try:
        execCmd("mvn -Pdeveloper -pl developer -Ddeploydb %s %s"%("-DskipTests" if inp_dict['skipTests'] else "", "-o" if inp_dict['buildOffline'] else ""))
    except Exception, e:
        print "****************************Deploydb Failed********************"
        print e
        return 1 
    return 0

def buildNoSimulator(inp_dict,retryBuild):
    out=None
    print "will not build simulator"
    while (out!=0 and retryBuild!=0):
          try:
              out=execCmd("mvn clean install -P developer,systemvm  %s %s"%("-DskipTests" if inp_dict['skipTests'] else "","-o" if inp_dict['buildOffline'] else ""))
          except Exception, e:
                 print ("mvn clean  install failed, will retry")
                 print e
          retryBuild=retryBuild-1
    print "************************out=***************",out
    if out!=0:
       return 1 
    try:
        execCmd("mvn -Pdeveloper -pl developer -Ddeploydb %s %s"%("-DskipTests" if inp_dict['skipTests'] else "","-o" if inp_dict['buildOffline'] else ""))
    except Exception, e:
        print "****************************Deploydb Failed********************"
        print e
        return 1 
    return 0

def getCSCode(inp_dict):
    repo_url = inp_dict['repo_url']
    os.system("mkdir -p /automation/cloudstack")
    os.system("git clone %s /automation/cloudstack"%repo_url)
    os.chdir("/automation/cloudstack")
    if(not inp_dict['githubPrno'] is None):
       os.system("git fetch origin pull/%s/head:%s"%(inp_dict['githubPrno'],inp_dict['githubPrno']))
       print ("cleaning if there are any local uncommited changes")
       os.system("git reset --hard")
       success=os.system("git checkout %s"%(inp_dict['githubPrno']))
       if(success !=0):
          echo "failed to checkout prno %s"%inp_dict['githubPrno'] > &2
       os.system("git branch -D master")
       success=os.system("echo 'git fetch origin master' 1>&2")
       if(success !=0):
         os.system("echo 'git fetch master failed' 1>&2")     
       os.system("git checkout -b master FETCH_HEAD")
       success=os.system("git merge %s"%inp_dict['githubPrno'])
       if(success !=0):
           message="git merge with master failed merge_branch:%s"%inp_dict['githubPrno']
           os.system("echo '%s'1>&2"%message)
    else:
       os.system("git fetch origin %s"%inp_dict['branch'])
       print ("cleaning if there are any local uncommited changes")
       os.system("git reset --hard")
       os.system("git checkout -b %s FETCH_HEAD"%(inp_dict['branch']))
    os.system("sed -iv 's/download.cloud.com/10.147.28.7/g' /automation/cloudstack/setup/db/templates.sql")
    print ("altered the download url for built in templates.")
    os.system ("killall -9 java")
    if (inp_dict['commit'] !=None):
       os.system("git reset --hard %s"%inp_dict['commit'])
    os.system("cp /root/vhd-util /automation/cloudstack/scripts/vm/hypervisor/xenserver/")
    os.system("mysql -uroot  -e \"GRANT ALL PRIVILEGES ON *.* TO 'root'@\'%s\' WITH GRANT OPTION \""%(inp_dict['hostname']))
     
    '''if (inp_dict['noSimulator']):
       success=os.system("sh /root/secseeder.sh > secseeder.log 2>&1")
       if (success !=0 ): 
           print "system vm template seeding failed"
           return 1''' 
    
    #if pakage is true it is kvm, we need to pacakage kvm agent, the packaging takes care of building cloudstack.
    print inp_dict
    if (inp_dict['noSimulator'] and not inp_dict['package']):
        result=buildNoSimulator(inp_dict,retryBuild=2)
    else:
        result=buildSimulator(inp_dict,retryBuild=2)
    if(result == 1):
         return 1
    #open port 8096 for marvin integration tests.
    execCmd("mysql -ucloud -pcloud -Dcloud -e\"update configuration set value=8096 where name like 'integr%'\"") 

    if (str(inp_dict['package']).lower == "true"):
       os.chdir('/automation/cloudstack/packaging/centos63/')
       try:
          os.system('sh package.sh')
       except Exception, e:
          print e
          return 1
       os.chdir('/automation/cloudstack')
    #if (inp_dict['noSimulator']):
       #os.system("mvn -pl client jetty:run &")
    #else:
       #os.system("mvn -Dsimulator -pl client jetty:run &")
    #return 0 

def main():
     ret = init()
     return getCSCode(ret)


if __name__ == '__main__':
     main()        
