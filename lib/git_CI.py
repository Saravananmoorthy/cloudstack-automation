#!/bin/env python
from bashUtils import bash
from bashUtils import  remoteSSHClient
import MySQLdb
import logging
from github import Github
import datetime

class github:
  def __init__(self):
    slef.logger=logging.getLogger('git-hub')
    self.user='apache'
    ddself.userName='bvbharatk'
    self.passwd='***REMOVED***'
    self.repoName='cloudstack'
    self.repo=self.getGitHubRepo()
    self.testComments=[]
    self.timeDiff=datetime.timedelta(minutes=5)
 
  def getGitHubRepo(self):
      g=Github(self.userName,self.passwd)
      user=g.get_user(self.user)
      repo=user.get_repo(self.repoName)
      return repo

  def getPrsToTest(self):
      


class git:
   def __init__(self):
       self.logger=logging.getLogger("git-server")  
       self.gitServer='172.16.88.6'
       self.gitServerSshPort=22
       self.gitServerUserName='root'
       self.gitServerPassword='password'
       self.gitRepoPath='/root/cloudstack'
       self.pullFrom='github'    
       self.syncTo='origin'
       self.gitHost=remoteSSHClient(self.gitServer,self.gitServerSshPort,self.gitServerUserName,self.gitServerPassword)
       self.gitDb=gitDb()

   def getPrs(self):
       self.gitHost.execute("cd %s && git fetch %s"%(self.gitRepoPath,self.pullFrom))
       self.gitHost.execute("cd %s && git branch -r"%(self.gitRepoPath))
       branchlist=self.gitHost.stdout
       return branchlist

   def savePrs(self):
       for pr in self.getPrs():
         vals=pr.split("/")
         origin=vals[0]
         if "pr"!=vals[1]: continue
         prName=pr.split(vals[0]+"/")[1]
         if(self.gitDb.findPrByName(prName,origin)):
           self.logger.info("ignoring pr %s, pr already exists"%pr)
         else:
           pr={'prName':prName, 'origin':self.pullFrom, 'tested':'no', 'success':''}
           self.gitDb.addPr(pr)         
   
   def getPrToTest(self):
       return self.gitDb.getPrToTest()  

   
   def updatePr(self,pr):
       self.gitDb.updatePr(pr) 

class gitDb:
   def __init__(self):
      self.dbHost="localhost"
      self.username="root"
      self.passwd=""
      self.database="resource_db"
      self.__con = None
      self.logger=logging.getLogger("gitDb")

   def connect(self):
       self.logger.info("acquiring db connection")
       self.__con = MySQLdb.connect(self.dbHost,self.username, self.passwd, self.database)
       return self.__con is not None
  
   def findPrByName(self,name,origin):
       if self.__con or self.connect():
            cur=self.__con.cursor()
       cur.execute("SELECT * FROM `resource_db`.`pull_requests` where pr_name='%s' and origin='%s'"%(name,origin))
       return self.getDict(cur.fetchone(),cur)
  
   def addPr(self,prDict):
       if self.__con or self.connect():
            cur=self.__con.cursor()
       cur.execute("INSERT INTO `resource_db`.`pull_requests` (`pr_name`,`origin`, `tested`, `success`, `update_time`) VALUES ('%s' ,'%s', '%s', '%s', now())"%(prDict['prName'],prDict['origin'],prDict['tested'],prDict['success'])) 
       self.__con.commit()
   
   def updatePr(self,prDict):
       if self.__con or self.connect():
            cur=self.__con.cursor()
       if(prDict['prName']==None):
         raise Exception("prName is none, need to specify which pr to update")
       del prDict['prName']
       if(self.findPrByName(prName)==None):
          raise Exception("cannot update pr pr_name=%s, pr dose not exist"%prName)
       for key in prDict.keys():
          cur.execute("UPDATE `resource_db`.`pull_requests` SET %s='%s' where pr_name='%s'"%(key,self.prDict[key],prName)) 
       cur.execute("UPDATE `resource_db`.`pull_requests` SET update_time=now() where pr_name='%s'"%prName)
       self.__con.commit()
   
   def getDict(self, dbResponse, cur):
       if ( dbResponse and len(dbResponse)):
                 desc=cur.description
                 responseDict={}
                 for value in desc:
                     responseDict.update({value[0]:dbResponse[value[0]]})
                 return responseDict    

   def getPrToTest(self):
       if self.__con or self.connect():
            cur=self.__con.cursor()
       cur.execute("SELECT * FROM `resource_db`.`pull_requests` WHERE tested='no' ORDER BY ID")
       print cur.fetchone()
       return self.getDict(cur.fetchone(),cur)
