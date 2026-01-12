#!/bin/bash
#Crontab
# */1 * * * * if /etc/node_exporter/scripts/app_monitor.sh > /etc/node_exporter/apprun.prom.$$; then mv /etc/node_exporter/apprun.prom.$$ /etc/node_exporter/apprun.prom; else rm /etc/node_exporter/apprun.prom.$$;fi

for i in `ls -l /opt/apps | grep ^d | awk '{ print $9 }' | grep maxfi`
 do
port=`cat /opt/apps/$i/application-prod.properties | grep "server.port" | awk -F' = ' '{print $2}'`
PID=`/opt/apps/$i/exec_jar.sh status | awk '{ print $6 }' |awk "NR==2"`

if [ -z $port ];then
  apps_port=1
else
  apps_port=`netstat -ntlp | grep -w $port |wc -l`
fi


if [[ $apps_port = 0 ]] || [[ -z $PID ]];then
  value=0
else
  value=1
fi

echo "app{name=\"$i\",port=\"$port\",PID=\"$PID\"} $value"

done
