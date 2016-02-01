#!/usr/local/bin/python2.7
import os
import sys
absPath=os.path.abspath(os.path.dirname(sys.argv[0]))
sys.path.append(os.path.join(absPath,'lib/'))

from hostResource import hostManager, poolManager
from testEnv import testEnv
import logging
import bashUtils
import time
import shutil
import subprocess
import xunitparser
from paramiko import SSHClient,AutoAddPolicy
from scp import SCPClient
from jenkinsapi import api, jenkins, job
import smtplib
from email.MIMEMultipart import MIMEMultipart
from email.MIMEBase import MIMEBase
from email.MIMEText import MIMEText
from email.Utils import COMMASPACE, formatdate
from email import Encoders
from marvin.sshClient import SshClient as remoteSSHClient
from optparse import OptionParser


infraxen_ip="10.147.28.51"
infraxen_passwd="password"
mgmtHostInfo={}
managementHost = "" 
#logging.basicConfig("/root/ContinuousTesting.log",level=logging.DEBUG)
logging.basicConfig(format='%(asctime)s %(levelname)s  %(name)s %(lineno)d  %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p',level=logging.INFO)

inp_dict={}
try:
        parser = OptionParser()
        parser.add_option("-b", "--branch", action="store",
                          default="master", dest="branch_no",
                          help="The branch used for this coverage Information")
        parser.add_option("-c", "--commit", action="store",
                          default=None, dest="commit_id",
                          help="The Commit id used for to retrieve coverage")
        parser.add_option("-u", "--repo_url", action="store",
                          default=None, dest="repo_url", 
                          help="url of the git repo")
        parser.add_option("-m", "--mail-to", action="store",
                          default=None, dest="mailto",
                          help="email address to send the results")
        parser.add_option("-N", "--cfgname", action="store",
                          default=None, dest="configName",
                          help="name of the configuration to use.")
                                                                    
        parser.add_option("-d", "--destroy", action="store",
                          default=False, dest="destroy",
                          help="desroy the management server if found in pool")

        parser.add_option("-p", "--profiler", action="store",
                          default=None, dest="profile",
                          help="select only simulator configs")
        
        parser.add_option("-t", "--tests", action="store",
                           default="", dest="testSpecifierString",
                           help="specify the tests to run")

        (options,args) = parser.parse_args()
        if options.commit_id=="None":
            options.commit_id=None
        if options.commit_id=="None":
            options.configName==None
        
        
        if options.configName!=None:
           if options.configName.lower()=="none":
               options.configName=None
           
        if options.profile==None:
           logging.info("No profile specified")
           sys.exit(1)
        
        if str(options.destroy).lower()=="true":
           options.destroy=True
        else:
           options.destroy=False

        if options.testSpecifierString=="":
           raise Execption("no tests where specified")

        logging.info("mailto %s"%options.mailto)
        inp_dict={"branch":options.branch_no,"commit":options.commit_id,"repo_url":options.repo_url, "mailto":options.mailto, "configName":options.configName,"destroy":options.destroy,"profile":options.profile}
        inp_dict.update({"testSpecifierString":options.testSpecifierString})

except Exception, e:
        logging.error("\nException Occurred %s. Please Check" %(e))

buildNo = os.environ['BUILD_NUMBER']

if inp_dict['mailto']==None:
   logging.info("no email id specified.")
   sys.exit(1)

try:    
        poolmgr=poolManager()
        hostmgr=hostManager()

        mgmtHostInfo=poolmgr.findSutableHost(inp_dict['repo_url'],inp_dict['profile'],inp_dict['configName'])
        if mgmtHostInfo!=None and inp_dict['destroy']:
           poolmgr.destroy(mgmtHostInfo['hostname'])
           mgmtHostInfo=None

        if mgmtHostInfo is None:
           mgmtHostInfo = hostmgr.create(inp_dict['repo_url'],inp_dict['branch'], inp_dict['commit'],inp_dict['configName'],inp_dict['profile'])
           mgmtHostInfo.update({'state':'active'})
           poolmgr.addToPool(mgmtHostInfo) 
        else:
           mgmtHostInfo=hostmgr.refreshHost(mgmtHostInfo, inp_dict['branch'],inp_dict['commit'])
        #print mgmtHostInfo 
        managementHost = mgmtHostInfo['hostname']
        testenv=testEnv()
        env=testenv.create(mgmtHostInfo,buildNo,inp_dict['branch'])
        mailto=inp_dict['mailto'].replace(' ','') 
        mailto=inp_dict['mailto'].split(",")
        #print "will mail the results to %s"%mailto 
        testenv.createDataCenter(env)
        env=testenv.execOnJenkins(env,inp_dict['testSpecifierString'],mailto)
        testenv.addBuildInfo(env)
except Exception, e:
       logging.error(e)
finally:
       logging.info(" freeing resource")
       poolmgr.free(mgmtHostInfo)

	

