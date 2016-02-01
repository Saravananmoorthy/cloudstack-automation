from ConfigParser import ConfigParser
from optparse import OptionParser
import marvin
from marvin import configGenerator
from marvin.sshClient import SshClient
from time import sleep as delay
import telnetlib
import socket

if __name__ == '__main__':
    parser = OptionParser()
    parser.add_option("-c", "--config", action="store", default="xen.cfg",
                      dest="config", help="the path where the server configurations is stored")

    parser.add_option("-k","--noSimulator", action="store",
                          default=True, dest="noSimulator",
                          help="will not buid sumulator if set to true")
 
    (options, args) = parser.parse_args()
    
    if options.config is None:
        raise

#    cscfg = configGenerator.get_setup_config(options.config)
    cscfg = configGenerator.getSetupConfig(options.config)
    mgmt_server = cscfg.mgtSvr[0].mgtSvrIp
    ssh = SshClient(mgmt_server, 22, "root", "password")
    ssh.execute("python /root/restartMgmtServer.py -p /automation/cloudstack --noSimulator %s > /var/log/cloudstack.log"%(options.noSimulator))

    #Telnet wait until api port is open
    tn = None
    timeout = 120
    while timeout > 0:
        try:
            tn = telnetlib.Telnet(mgmt_server, 8096, timeout=120)
            break
        except Exception:
            delay(5)
            timeout = timeout - 1
    if tn is None:
        raise socket.error("Unable to reach API port")

