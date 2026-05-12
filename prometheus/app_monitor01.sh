#!/bin/bash
#Crontab
# */1 * * * * if /etc/node_exporter/scripts/app_monitor.sh > /etc/node_exporter/apprun.prom.$$; then mv /etc/node_exporter/apprun.prom.$$ /etc/node_exporter/apprun.prom; else rm /etc/node_exporter/apprun.prom.$$;fi

for APP_NAME in `ls -l /opt/apps | grep ^d | awk '{ print $9 }'`
 do
PORT=`cat /opt/apps/$APP_NAME/application-prod.properties | grep "server.port" | awk -F' = ' '{print $2}'`
PID=`/opt/apps/$APP_NAME/exec_jar.sh status | awk '{ print $6 }' |awk "NR==2"`

if [ -z $PORT ];then
  STATUS=1
else
  STATUS=$(ss -tuln | grep -q ":$PORT " && echo 1 || echo 0)
fi


echo "app{name=\"$APP_NAME\",port=\"$PORT\",PID=\"$PID\"} $STATUS"

done
