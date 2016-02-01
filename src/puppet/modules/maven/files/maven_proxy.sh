#!/bin/bash
sed  -i 's/<proxies>/<proxies>\n  <proxy>\n    <id>optional<\/id>\n    <active>true<\/active>\n    <protocol>http<\/protocol>\n    <host>172.16.88.5<\/host>\n    <port>3128<\/port>\n    <nonProxyHosts>local.net|some.host.com<\/nonProxyHosts>\n  <\/proxy>/' /opt/apache-maven-3.0.5/conf/settings.xml
