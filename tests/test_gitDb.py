from git_CI import github

if __name__=="__main__":
   g=github()
   pr=g.getPrToTest()
   pr['tested']='yes'
   pr['success']='yes'
   print "pr**********",pr
   g.updatePr(pr)
