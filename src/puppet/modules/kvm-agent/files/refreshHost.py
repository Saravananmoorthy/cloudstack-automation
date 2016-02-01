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
                          default=False, dest="package",
                          help="will package cloudstack if package is true")

        (options,args) = parser.parse_args()
        if (options.package.lower()=="false" or options.package==None):
            options.package=False
        else
           options.package=True
  
        return {"branch":options.branch_no,"commit":options.commit_id,"hostname":options.hostname}
    except Exception, e:
        print "\nException Occurred %s. Please Check" %(e)
        return codes['FAILED']

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
    print cmd
    return 

def getCSCode(inp_dict):
    os.chdir("/automation/cloudstack")
    os.system("killall -9 java")
    time.sleep(20)
    if os.system("git checkout -b temp_branch")!=0:
       os.system("git checkout temp_branch")
    os.system("git branch -D %s"%inp_dict['branch'])
    os.system("git fetch origin %s"%inp_dict['branch'])
    os.system("git checkout -b %s FETCH_HEAD"%inp_dict['branch'])
    if (inp_dict['commit'] !=""):
       os.system("git reset --hard %s"%inp_dict['commit'])
    os.system("mysql -uroot  -e \"GRANT ALL PRIVILEGES ON *.* TO 'root'@\'%s\' WITH GRANT OPTION \""%(inp_dict['hostname']))
    execCmd("mvn clean install -Pdeveloper -Dsimulator -DskipTests")
    execCmd("mvn -Pdeveloper -pl developer -Ddeploydb -DskipTests")
    os.system("mvn -Pdeveloper -pl developer -Ddeploydb-simulator -DskipTests")
    if (inp_dict['package']):
       os.chdir('/automation/cloudstack/packaging/centos63/')
       os.system('sh package.sh')
       os.chdir('/automation/cloudstack')
    os.system("mvn -Dsimulator -pl client jetty:run &")

def main():
     ret = init()
     getCSCode(ret)


if __name__ == '__main__':
     main()        
