import sys
from optparse import OptionParser
import os
from os import chdir
from time import sleep as delay
import subprocess
import shlex
codes = {'FAILED':1,'SUCCESS':0}

def parse_options():
    try:
        parser = OptionParser()
        parser.add_option("-p", "--path", action="store",
                          default="", dest="path",
                          help="The path to the repo")

        parser.add_option("-k","--noSimulator", action="store",
                          default=False, dest="noSimulator",
                          help="will not buid sumulator if set to true")

        (options,args) = parser.parse_args()
        return {"path":options.path,"noSimulator":options.noSimulator}
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



def getCSCode(inp_dict):
    path = inp_dict['path'] 
    os.chdir(path)
    os.system("killall -9 java")
    print "*******************************Restarting Management Server****************************************"  
    delay(30)

    if (str(inp_dict['noSimulator']).lower()=="true"):
        os.system("mvn -pl :cloud-client-ui jetty:run &")
    else:
       os.system("mvn -Dsimulator -pl client jetty:run &")
    
def main():
     ret = init()
     getCSCode(ret)


if __name__ == '__main__':
     main()        
