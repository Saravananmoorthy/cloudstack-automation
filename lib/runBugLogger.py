from jenkins import Jenkins
from hostImager import resourceManager
from optparse import OptionParser
 
parser = OptionParser()
parser.add_option("-b", "--branch", action="store",
                   default="master", dest="branch",
                   help="The branch used for this coverage Information")
parser.add_option("-p", action="store",
                   default=None, dest="hypervisor",
                   help="The hypervisor type")
parser.add_option("-l", "--logname", action="store",
                   default=None, dest="logname",
                   help="The name of the log archive")
parser.add_option("-t", "--type", action="store",
                   default="bvt", dest="buildType",
                   help="The branch used for this coverage Information")

(options,args) = parser.parse_args()

j=Jenkins('http://jenkins-ccp.citrix.com','bharatk','BharatK')
print "triggering filebugs build to log bugs"
j.build_job('fileBugs', {'TYPE':options.buildType, 'HYP':options.hypervisor, 'version':options.branch, 'BUILD':options.logname,'token':'bharat'})

