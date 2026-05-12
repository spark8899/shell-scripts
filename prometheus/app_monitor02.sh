#!/bin/bash
#Crontab
# */1 * * * * if /etc/node_exporter/scripts/app_monitor.sh > /etc/node_exporter/apprun.prom.$$; then mv /etc/node_exporter/apprun.prom.$$ /etc/node_exporter/apprun.prom; else rm /etc/node_exporter/apprun.prom.$$;fi

for APP_NAME in `ls -l /opt/apps |grep ^d |awk '{ print $9 }'`
 do
PORT=`cat /opt/apps/$APP_NAME/config.yaml | grep address | awk -F':' '{print $NF}' | awk -F'"' '{print $1}'`
PID=`/usr/bin/pidof $APP_NAME`

if [ -z $PORT ];then
  STATUS=1
else
  STATUS=$(ss -tuln | grep -q ":$PORT " && echo 1 || echo 0)
fi


echo "app{name=\"$APP_NAME\",port=\"$PORT\",PID=\"$PID\"} $STATUS"

done
