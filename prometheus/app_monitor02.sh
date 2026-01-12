#!/bin/bash
#Crontab
# */1 * * * * if /etc/node_exporter/scripts/app_monitor.sh > /etc/node_exporter/apprun.prom.$$; then mv /etc/node_exporter/apprun.prom.$$ /etc/node_exporter/apprun.prom; else rm /etc/node_exporter/apprun.prom.$$;fi

for i in `ls -l /opt/apps |grep ^d |awk '{ print $9 }'`
 do
PORT=`cat /opt/apps/$i/config.yaml | grep address | awk -F':' '{print $NF}' | awk -F'"' '{print $1}'`
PID=`/usr/bin/pidof $i`

if [ -z $PORT ];then
  apps_port=1
else
  apps_port=`netstat -ntlp | grep -w $PORT |wc -l`
fi


if [[ $apps_port = 0 ]] || [[ -z $PID ]];then
  value=0
else
  value=1
fi

echo "app{name=\"$i\",port=\"$PORT\",PID=\"$PID\"} $value"

done
