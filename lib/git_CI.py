#!/bin/env python
from bashUtils import bash
from bashUtils import  remoteSSHClient
import MySQLdb
import logging
from github import Github
import datetime
from exceptions import KeyError

logging.basicConfig(format='%(asctime)s %(levelname)s  %(name)s %(lineno)d  %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p',level=logging.INFO)

class github:
  def __init__(self,update=False):
    self.logger=logging.getLogger('git-hub')
    self.user='apache'
    self.userName='bvbharatk'
    self.passwd='***REMOVED***'
    self.repoName='cloudstack'
    self.testComments=[]
    self.timeDiff=datetime.timedelta(minutes=5)
    self.prList=[]
    self.gitDb=gitDb()
    self.repo=self.getGitHubRepo()
    if update:
       self.getPrsFromGithub()

  def getGitHubRepo(self):
      g=Github(self.userName,self.passwd)
      user=g.get_user(self.user)
      self.logger.info("connecting with the repo")
      repo=user.get_repo(self.repoName)
      return repo

  def getPrsFromGithub(self):
      pulls=self.repo.get_pulls(state='open')
      self.logger.info("gathering pull requests from github")
      self.prList=[{'title':pull.title[:20], 'patch_url': pull.patch_url, 'updated_at':pull.updated_at, 'prNo':pull.number, 'commits':[commit.commit.sha for commit in pull.get_commits()],'pull':pull} for pull in pulls]
      self.logger.info("gathering of pull requests complete.")

  def savePrs(self):
       for pr in self.prList:
           print pr
           if(self.gitDb.findPrByNumber(pr['prNo'],self.repo.full_name)):
              self.logger.info("ignoring pr %s, pr already exists"%pr)
           else:
              prRecord={'pr_name':pr['title'], 'origin':self.repo.full_name, 'tested':'no', 'success':'', 'updated_at':pr['updated_at'], 'prNo':pr['prNo']}
              prDetailList=[{'key':'patch_url', 'value':pr['patch_url']}]
              prDetailList.append({'key':'commits', 'value':",".join(pr['commits'])})
              self.gitDb.addPr(prRecord)
              self.updatePrDetails(self.gitDb.findPrByNumber(pr['prNo'], self.repo.full_name), prDetailList)

  def syncChangesToPrs(self):
      prsInRepo=[pr['prNo']  for pr in self.prList]
      prsInDb=self.gitDb.getAllPrsInDb( self.repo.full_name )
      prRepoMap={}
      prDbMap={}
      for pr in self.prList:
          prRepoMap[pr['prNo']]=pr
      for pr in prsInDb:
          prDbMap[pr['pr_no']]=pr

      for pr in prsInDb:
          try:
             if pr['pr_no'] not in prsInRepo:
                self.logger.info("Pr %s is either closed or removed, so remove this from db"%pr['pr_no'])
                self.gitDb.removePrById(pr['id'])
             elif pr['commits']!=prRepoMap[pr['pr_no']]['commits']:
                #update Commit details in Db and reset the tested and success status.
                self.logger.info('commit ids have changed for pr no %s, upadatin the details and testing again'%pr['pr_no'])
                pr['tested']='No'
                pr['success']=''
                self.updatePr(pr)
                prDetailList=[{'key':'commits', 'value':prRepoMap[pr['pr_no']]['commits']}]
                self.updatePrDetails(pr,prDetailList)
                #self.notifyPr(pr,'Noticed a change in commits, updated and added to run queue')
             else:
                self.logger.info("no changes in pr %s"%pr['pr_no'])
          except KeyError, e:
               self.logger.error("pr %s, keyError %s"%(pr, e))
               if 'commits' in e.args:
                  self.logger.info("adding commit info to pr %s"%pr['pr_no'])
                  prDetailList=[{'key':'commits', 'value':prRepoMap[pr['pr_no']]['commits']}]
                  self.updatePrDetails(pr,prDetailList)

  def notifyPr(self,pr, info, deleteOld=True):
       Headding="###ACS CI Notification\n"
       try:
          pullrq=self.repo.get_pull(prNo)
          #print pr
          if('issue_comment_id' in pr.keys() and deleteOld):
             self.logger.info("deleteing previously made comment")
             try:
                 issue_comment=pullrq.get_issue_comment(long(pr['issue_comment_id']))
                 issue_comment.delete()
             except Exception as e:
                 self.logger.exception(e)
          issue_comment=pullrq.create_issue_comment(Headding+info)
          prDetailList=[{'pr_no':prNo, 'key':'issue_comment_id','value':issue_comment.id}]
          self.gitDb.updatePrDetails(pr,prDetailList)
       except Exception as e:
          self.logger.exception(e)


  def getPrToTest(self):
      return self.gitDb.getPrToTest()

  def updatePr(self,pr):
       self.gitDb.updatePr(pr)

  def commentOnPr(self,prNo,commentData, deleteOld=True):
       try:
          pullrq=self.repo.get_pull(prNo)
          pr=self.gitDb.findPrByNumber(prNo, self.repo.full_name)
          #print pr
          if('issue_comment_id' in pr.keys() and deleteOld):
             self.logger.info("deleteing previously made comment")
             try:
                 issue_comment=pullrq.get_issue_comment(long(pr['issue_comment_id']))
                 issue_comment.delete()
             except Exception as e:
                 self.logger.exception(e)
          issue_comment=pullrq.create_issue_comment(commentData)
          prDetailList=[{'pr_no':prNo, 'key':'issue_comment_id','value':issue_comment.id}]
          self.gitDb.updatePrDetails(pr,prDetailList)
       except Exception as e:
          self.logger.exception(e)

  def commentOnPrByEditing(self,prNo,commentData):
       pr=self.gitDb.findPrByNumber(prNo, self.repo.full_name)
       pullrq=self.repo.get_pull(prNo)
       if('issue_comment_id' in pr.kyes()):
          #edit the existing comment.
          issue_comment=pullrq.get_issue_comment(pr['issue_comment_id'])
          issue_comment.edit(commentData)
       else:
          issue_comment=pullrq.create_issue_comment(commentData)
          pr=self.gitDb.findPrByNumber(prNo, self.repo.full_name)
          prDetail={'pr_no':prNo, 'key':'issue_comment_id','value':issue_comment.id}
          self.gitDb.updatePrDetails(pr,prDetail)

  def updatePrDetails(self,pr,prDetails):
       self.gitDb.updatePrDetails(pr,prDetails)

class git:
   '''this class is useful when maintainging a staging branch and pulling code from there'''
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

   def getPrsFromRepo(self):
       self.gitHost.execute("cd %s && git fetch %s"%(self.gitRepoPath,self.pullFrom))
       self.gitHost.execute("cd %s && git branch -r"%(self.gitRepoPath))
       branchlist=self.gitHost.stdout
       return branchlist


   def savePrs(self):
       for pr in self.getPrs():
         vals=pr.split("/")
         origin=vals[0]
         if "pr"!=vals[1]: continue
         pr_name=pr.split(vals[0]+"/")[1]
         if(self.gitDb.findPrByName(pr_name,origin)):
           self.logger.info("ignoring pr %s, pr already exists"%pr)
         else:
           pr={'pr_name':prName, 'origin':self.pullFrom, 'tested':'no', 'success':''}
           self.gitDb.addPr(pr)

   def commentOnPr(self,prNo,commentData):
       pullrq=self.repo.get_pull(prNo)
       pullrq.create_issue_comment(commentData)

   def updatePr(self,pr):
       self.gitDb.updatePr(pr)

   def updatePrDetails(self,pr,prDetails):
       self.gitDb.updatePrDetails(pr,prDetails)

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

   def findPrByNumber(self,pr_no,origin):
       if self.__con or self.connect():
            cur=self.__con.cursor(MySQLdb.cursors.DictCursor)
       cur.execute("SELECT * FROM `resource_db`.`pull_requests` where pr_no='%s' and origin='%s'"%(pr_no,origin))
       prDict=self.getDict(cur.fetchone(),cur)
       details_dict=None
       if(prDict is not None):
           details_dict=cur.execute("SELECT `key`, `value` FROM `resource_db`.`pull_request_details` WHERE pr_id='%s'"%prDict['id'])
           prDetails=self.getDetailsDict(cur.fetchall(),cur)
           if (prDetails is not None):
               #print prDict
               #pri
               prDict.update(prDetails)
       return prDict

   def addPr(self,prDict):
       if self.__con or self.connect():
            cur=self.__con.cursor()
       cmd="INSERT INTO `resource_db`.`pull_requests` (`pr_name`,`origin`, `tested`, `success`, `updated_at`, `pr_no`) VALUES '%s' ,'%s', '%s', '%s', '%s','%s')"
       cur.execute(cmd, (prDict['pr_name'].replace("'","/'"), prDict['origin'], prDict['tested'], prDict['success'], prDict['updated_at'], prDict['prNo']))
       #cur.execute("INSERT INTO `resource_db`.`pull_requests` (`pr_name`,`origin`, `tested`, `success`, `updated_at`, `pr_no`) VALUES '%s' ,'%s', '%s', '%s', '%s','%s')"%(prDict['pr_name'].replace("'","/'"), prDict['origin'], prDict['tested'], prDict['success'], prDict['updated_at'], prDict['prNo']))
       cur.execute("INSERT INTO `resource_db`.`pull_request_details` (`pr_id`, `key`, `value`) VALUES('%s', '%s', '%s')"%(prDict['id'],'patch_url',prDict['patch_url']))
       self.__con.commit()

   def updatePrDetails(self,prDict,prDetailList):
       if self.__con or self.connect():
            cur=self.__con.cursor()
       if(prDict['id']==None):
         raise Exception("pr id is none, need to specify which pr to update")
       for detail in prDetailList:
          print detail
          cur.execute("DELETE  FROM `resource_db`.`pull_request_details` where `key`='%s' and `pr_id`='%s'"%(detail['key'], prDict['id']))
          cur.execute("INSERT INTO `resource_db`.`pull_request_details` (`pr_id`, `key`, `value`) VALUES('%s', '%s', '%s')"%(prDict['id'], detail['key'], detail['value']))
       self.__con.commit()

   def updatePr(self,prDict):
       if self.__con or self.connect():
            cur=self.__con.cursor()
       cur.execute('''Update `resource_db`.`pull_requests` SET `pr_name`=%s, `origin`=%s, `tested`=%s, `success`=%s, `updated_at`=now() where `pr_no`=%s''',(prDict['pr_name'],prDict['origin'],prDict['tested'], prDict['success'],prDict['pr_no']))
       self.__con.commit()

   def getDict(self,dbResponse, cur):
       if ( dbResponse and len(dbResponse)):
                 desc=cur.description
                 responseDict={}
                 for value in desc:
                     responseDict.update({value[0]:dbResponse[value[0]]})
                 return responseDict


   def getDetailsDict(self,dbResponses, cur):
       print dbResponses
       if(dbResponses and len(dbResponses)):
           responseDict={}
           #d=[responseDict.__setitem__(k,v) for k,v in dbResponse]
           for res in dbResponses:
               responseDict.update({res['key']:res['value']})
           return responseDict

   def getPrToTest(self):
       if self.__con or self.connect():
            cur=self.__con.cursor(MySQLdb.cursors.DictCursor)
       cur.execute("SELECT * FROM `resource_db`.`pull_requests` WHERE tested='no' ORDER BY ID")
       #print cur.fetchone()
       prDict=self.getDict(cur.fetchone(),cur)
       details_dict=cur.execute("SELECT `key`, `value` FROM `resource_db`.`pull_request_details` WHERE pr_id='%s'"%prDict['id'])
       prDetails=self.getDetailsDict(cur.fetchall(),cur)
       #print prDict
       #print prDetails
       if (prDetails is not None):
            prDict.update(prDetails)
       return prDict

   def getTestedPrs(self):
       if self.__con or self.connect():
            cur=self.__con.cursor(MySQLdb.cursors.DictCursor)
       cur.execute("SELECT * FROM `resource_db`.`pull_requests` WHERE tested='yes'")
       prList=[]
       responseList=cur.fetchall()
       for response in responseList:
          prDict=self.getDict(response, cur)
          prList.append(prDict)
       for pr in prList:
          details_dict=cur.execute("SELECT `key`, `value` FROM `resource_db`.`pull_request_details` WHERE pr_no='%s'"%pr['pr_no'])
          prDetails=self.getDetailsDict(cur.fetchall(),cur)
          pr.update(prDetails)
       return prList

   def getAllPrsInDb(self, origin):
       if self.__con or self.connect():
            cur=self.__con.cursor(MySQLdb.cursors.DictCursor)
       print "SELECT * FROM `resource_db`.`pull_requests` where origin='%s'"%origin
       cur.execute("SELECT * FROM `resource_db`.`pull_requests` where origin='%s'"%origin)
       prList=[]
       responseList=cur.fetchall()
       for response in responseList:
          prDict=self.getDict(response, cur)
          prList.append(prDict)
       for pr in prList:
          details_dict=cur.execute("SELECT `key`, `value` FROM `resource_db`.`pull_request_details` WHERE pr_id='%s'"%pr['id'])
          prDetails=self.getDetailsDict(cur.fetchall(),cur)
          if(prDetails is not None):
              print prDetails
              pr.update(prDetails)
       return prList


   def removePrById(self,prId):
       if self.__con or self.connect():
            cur=self.__con.cursor()
       cur.execute("DELETE FROM `resource_db`.`pull_requests` where id='%s' "%prId)
       cur.execute("DELETE FROM `resource_db`.`pull_request_details` WHERE pr_id='%s'"%prId)
