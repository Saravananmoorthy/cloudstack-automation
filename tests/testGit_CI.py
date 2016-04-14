from git_CI import github as git
git=git(update=True)
#prs=git.getPrs()
git.savePrs()
print  git.getPrToTest()

