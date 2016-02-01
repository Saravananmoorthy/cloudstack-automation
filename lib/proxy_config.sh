#!/bin/bash
#insers proxy config onto the hosts
git config --global http.proxy http://172.16.88.5:3128
git config --global https.proxy http://172.16.88.5:3128
echo "export http_proxy=http://172.16.88.5:3128" >> /root/.bashrc
source /root/.bashrc
