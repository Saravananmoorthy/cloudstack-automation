#!/usr/local/bin/python2.7
from hostResourceMysqlProfiles import hostManager, poolManager
from testEnv import testEnv
import logging
import os
import bashUtils
import time
import sys
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
from git_CI import gitDb

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

        parser.add_option("-P","--buildFromPr",action="store",
                           dest="buildFromPr",
                           help="build from github pull requests")

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
           raise Exception("no tests where specified")


        logging.info("mailto %s"%options.mailto)
        inp_dict={"branch":options.branch_no,"commit":options.commit_id,"repo_url":options.repo_url, "mailto":options.mailto, "configName":options.configName,"destroy":options.destroy,"profile":options.profile}
        inp_dict.update({"testSpecifierString":options.testSpecifierString})
        inp_dict.update({"buildFromPr":options.buildFromPr})

except Exception as  e:
        logging.exception(e)

buildNo = os.environ['BUILD_NUMBER']
g=None
prToTest=None
githubPrno=None

def needsTesting(prToTest):
    avoidList=['ui','vmware','checkstyle', 'logrotate','kvm','automation', 'automated']
    titleWords=[word.lower() for word in prToTest['pr_name'].split()]
    for word in titleWords:
        if(word in avoidList):
           return False
    return True

if inp_dict['mailto']==None:
   logging.info("no email id specified.")
   sys.exit(1)

g=gitDb()
if inp_dict['buildFromPr']=="None":
   prToTest=None
   while(True):
     prToTest=g.getPrToTest()
     if((prToTest is not None) and (not needsTesting(prToTest))):
        logging.info("pr %s title %s needs no testing"%(prToTest['pr_no'],prToTest['pr_name']))
        prToTest['tested']='NA'
        g.updatePr(prToTest)
        prToTest=None
     else:
        break
else:
    pr=inp_dict['buildFromPr']
    pr=pr.split(":")
    prToTest=g.findPrByNumber(pr[0], pr[1])

if(prToTest is None):
     logging.info("Found no pr to test")
     sys.exit(0)
githubPrno=long(prToTest['pr_no'])

try:
        poolmgr=poolManager()
        hostmgr=hostManager()

        mgmtHostInfo=poolmgr.findSutableHost(inp_dict['repo_url'],inp_dict['profile'],inp_dict['configName'])
        if mgmtHostInfo!=None and inp_dict['destroy']:
           poolmgr.destroy(mgmtHostInfo['hostname'])
           mgmtHostInfo=None

        if mgmtHostInfo is None:
           mgmtHostInfo = hostmgr.create(inp_dict['repo_url'],inp_dict['branch'],githubPrno, inp_dict['commit'],inp_dict['configName'],inp_dict['profile'])
           mgmtHostInfo.update({'state':'active'})
           poolmgr.addToPool(mgmtHostInfo)
        else:
           mgmtHostInfo=hostmgr.refreshHost(mgmtHostInfo, inp_dict['branch'],githubPrno,inp_dict['commit'])
        #print mgmtHostInfo
        managementHost = mgmtHostInfo['hostname']
        testenv=testEnv()
        env=testenv.create(mgmtHostInfo,buildNo,"%s"%githubPrno if inp_dict['buildFromPr'] else inp_dict['branch'])
        if inp_dict['buildFromPr']:
           env.update({'branch':inp_dict['branch']})
        mailto=inp_dict['mailto'].replace(' ','')
        mailto=inp_dict['mailto'].split(",")
        #print "will mail the results to %s"%mailto
        testenv.createDataCenter(env)
        env=testenv.execOnJenkins(env,inp_dict['testSpecifierString'],mailto, postOnPr=inp_dict['buildFromPr'])
        testenv.addBuildInfo(env)

        if inp_dict['buildFromPr']:
           prToTest['tested']='yes'
           prToTest['success']='yes'
           g.updatePr(prToTest)
           logging.info('adding Pr details')
           prDetail=[{'pr_no':prToTest['pr_no'], 'key':'build_number', 'value':buildNo}]
           g.updatePrDetails(prToTest,prDetail)

except Exception as e:
       logging.exception(e)
finally:
       logging.info("freeing resource")
       poolmgr.free(mgmtHostInfo)


