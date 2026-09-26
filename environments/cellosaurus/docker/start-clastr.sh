#!/bin/sh
set -eu
mkdir -p /tmp/tomcat/conf /tmp/tomcat/logs /tmp/tomcat/work /tmp/tomcat/webapps /tmp/tomcat/temp
cp -R /opt/tomcat/conf/. /tmp/tomcat/conf/
# No access log of user STR parameters and no management applications.
sed -i '/<Valve className="org.apache.catalina.valves.AccessLogValve"/,/\/>/d' /tmp/tomcat/conf/server.xml
ln -s /opt/tomcat/webapps/str-search.war /tmp/tomcat/webapps/str-search.war
exec /opt/tomcat/bin/catalina.sh run
