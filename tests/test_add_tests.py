from jenkinsJob import modifyJOb

if __name__=="__main__":
  tests=[]
  for i in range(12):
      tests.append('test_'+str(i)+'.py')
  jobMod=modifyJOb()
  jobMod.indexObj.setVals(0,4)
  # while(jobMod.addTests('125', tests)):
  #       print "added tests"
  for jobs in jobMod.addTests('125',tests,4):
     print jobs

