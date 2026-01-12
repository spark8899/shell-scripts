#!/bin/bash
#Crontab
# */30 * * * * if /etc/node_exporter/scripts/check.machine.info.sh > /etc/node_exporter/matchine_info.prom.$$; then mv /etc/node_exporter/matchine_info.prom.$$ /etc/node_exporter/matchine_info.prom; else rm /etc/node_exporter/matchine_info.prom.$$;fi

board_vendor=$(cat /sys/class/dmi/id/board_vendor 2>/dev/null | tr ' ' '_')
board_name=$(cat /sys/class/dmi/id/board_name 2>/dev/null | tr ' ' '_')
board_serial=$(cat /sys/class/dmi/id/board_serial 2>/dev/null | tr ' ' '_')
board_version=$(cat /sys/class/dmi/id/board_version 2>/dev/null | tr ' ' '_')
production_name=$(cat /sys/class/dmi/id/product_name 2>/dev/null | tr ' ' '_')
production_version=$(cat /sys/class/dmi/id/product_version 2>/dev/null | tr ' ' '_')
production_serial=$(cat /sys/class/dmi/id/product_serial 2>/dev/null | tr ' ' '_')
production_uuid=$(cat /sys/class/dmi/id/product_uuid 2>/dev/null | tr ' ' '_')

cpu_model=$(grep "model name" /proc/cpuinfo | head -n1 | cut -d: -f2 | sed 's/^[ \t]*//' | tr -s ' ' '_')
cpu_cores=$(nproc)

if which dmidecode &>/dev/null; then
    mem_total=$(dmidecode -t memory | grep "Size:" | grep -v "No Module Installed" | awk '{
        if ($3 == "GB") { sum += $2 * 1024 }
        else { sum += $2 }
    }
    END {
        if (sum > 0) {
            if (sum >= 1024) { printf "%.0fGB", sum/1024 }
            else { printf "%.0fMB", sum }
        }
    }')

    if [ -z "$mem_total" ]; then
        mem_total=$(free -h | awk '/^Mem:/ {print $2}')
    fi
else
    mem_total=$(free -h | awk '/^Mem:/ {print $2}')
fi

if which lsb_release &>/dev/null; then
    os=$(lsb_release -d -s 2>/dev/null | tr ' ' '_')
else
    os=$(cat /etc/centos-release 2>/dev/null | tr ' ' '_')
fi
kernel=$(uname -r)
arch=$(uname -m)

echo "machine_info{board_vendor=\"$board_vendor\",board_name=\"$board_name\",board_serial=\"$board_serial\",board_version=\"$board_version\",production_name=\"$production_name\",production_version=\"$production_version\",production_serial=\"$production_serial\",production_uuid=\"$production_uuid\",cpu_model=\"$cpu_model\",cpu_cores=\"$cpu_cores\",mem_total=\"$mem_total\"} 0"

echo "system_info{os=\"$os\",kernel=\"$kernel\",arch=\"$arch\"} 0"

if which lsblk &>/dev/null; then
    lsblk -d -n -o NAME,SIZE,TYPE,MODEL | while read name size type model; do
        if [ "$type" == "disk" ]; then
            if [ -z "$model" ]; then model="Unknown"; fi
            clean_model=$(echo "$model" | tr -s ' ' '_')
            echo "disk_layout_info{device=\"$name\",size=\"$size\",model=\"$clean_model\"} 0"
        fi
    done
fi
