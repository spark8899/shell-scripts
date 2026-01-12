#!/bin/bash

/bin/ls -al
timestr=$(date +%Y%m%d%H%M)

/bin/echo "upload hprof"
filename="$(hostname)-$timestr.hprof"
upload_url=$(/usr/bin/curl -sXGET "http://10.32.24.119:8811/generate_presigned_urls?file_name=$filename" | awk -F'"' '{print $4}')
/bin/echo "upload_url: $upload_url"
/usr/bin/curl --progress-bar -XPUT -T /opt/app/dump.hprof $upload_url
/usr/bin/curl -sXGET "http://10.32.24.119:8811/check_file_exists?file_name=$filename"
/bin/echo "\ncheck upload hprof end..."

/bin/echo "upload gclog"
filename="$(hostname)-$timestr-gclog.tgz"
/bin/tar zcvf $filename *.log*
upload_url=$(/usr/bin/curl -sXGET "http://10.32.24.119:8811/generate_presigned_urls?file_name=$filename" | awk -F'"' '{print $4}')
/bin/echo "upload_url: $upload_url"
/usr/bin/curl --progress-bar -XPUT -T /opt/app/$filename $upload_url
/usr/bin/curl -sXGET "http://10.32.24.119:8811/check_file_exists?file_name=$filename"
/bin/echo "\ncheck upload gclog end..."

/bin/echo "upload app.jar"
filename="$(hostname)-$timestr-app.jar"
upload_url=$(/usr/bin/curl -sXGET "http://10.32.24.119:8811/generate_presigned_urls?file_name=$filename" | awk -F'"' '{print $4}')
/bin/echo "upload_url: $upload_url"
/usr/bin/curl --progress-bar -XPUT -T /opt/app/server.jar $upload_url
/usr/bin/curl -sXGET "http://10.32.24.119:8811/check_file_exists?file_name=$filename"
/bin/echo "\ncheck upload app.jar end..."
