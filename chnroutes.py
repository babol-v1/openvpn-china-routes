#!/usr/bin/env python3
import re
import urllib.request
import sys
import argparse
import math
import textwrap

def generate_ovpn(metric):
    results = fetch_ip_data()  
    rfile = open('routes.txt', 'w', encoding='utf-8')
    for ip, mask, _ in results:
        route_item = "route %s %s net_gateway %d\n" % (ip, mask, metric)
        rfile.write(route_item)
    rfile.close()
    print("Usage: Append the content of the newly created routes.txt to your openvpn config file," \
          " and also add 'max-routes %d', which takes a line, to the head of the file." % (len(results) + 20))

def generate_linux(metric):
    results = fetch_ip_data()
    upscript_header = textwrap.dedent("""\
    #!/bin/bash
    export PATH="/bin:/sbin:/usr/sbin:/usr/bin"
    
    OLDGW=`ip route show | grep '^default' | sed -e 's/default via \\([^ ]*\\).*/\\1/'`
    
    if [ \$OLDGW == '' ]; then
        exit 0
    fi
    
    if [ ! -e /tmp/vpn_oldgw ]; then
        echo \$OLDGW > /tmp/vpn_oldgw
    fi
    
    """)
    
    downscript_header = textwrap.dedent("""\
    #!/bin/bash
    export PATH="/bin:/sbin:/usr/sbin:/usr/bin"
    
    OLDGW=`cat /tmp/vpn_oldgw`
    
    """)
    
    upfile = open('ip-pre-up', 'w', encoding='utf-8')
    downfile = open('ip-down', 'w', encoding='utf-8')
    
    upfile.write(upscript_header)
    upfile.write('\n')
    downfile.write(downscript_header)
    downfile.write('\n')
    
    for ip, mask, _ in results:
        upfile.write('route add -net %s netmask %s gw \$OLDGW\n' % (ip, mask))
        downfile.write('route del -net %s netmask %s\n' % (ip, mask))

    downfile.write('rm /tmp/vpn_oldgw\n')
    upfile.close()
    downfile.close()

def generate_mac(metric):
    results = fetch_ip_data()
    
    upscript_header = textwrap.dedent("""\
    #!/bin/sh
    export PATH="/bin:/sbin:/usr/sbin:/usr/bin"
    
    OLDGW=`netstat -nr | grep '^default' | grep -v 'ppp' | sed 's/default *\\([0-9\.]*\\) .*/\\1/' | awk '{if($1){print $1}}'`

    if [ ! -e /tmp/pptp_oldgw ]; then
        echo "\${OLDGW}" > /tmp/pptp_oldgw
    fi
    
    dscacheutil -flushcache

    route add 10.0.0.0/8 "\${OLDGW}"
    route add 172.16.0.0/12 "\${OLDGW}"
    route add 192.168.0.0/16 "\${OLDGW}"
    """)
    
    downscript_header = textwrap.dedent("""\
    #!/bin/sh
    export PATH="/bin:/sbin:/usr/sbin:/usr/bin"
    
    if [ ! -e /tmp/pptp_oldgw ]; then
            exit 0
    fi
    
    OLDGW=`cat /tmp/pptp_oldgw`

    route delete 10.0.0.0/8 "\${OLDGW}"
    route delete 172.16.0.0/12 "\${OLDGW}"
    route delete 192.168.0.0/16 "\${OLDGW}"
    """)
    
    upfile = open('ip-up', 'w', encoding='utf-8')
    downfile = open('ip-down', 'w', encoding='utf-8')
    
    upfile.write(upscript_header)
    upfile.write('\n')
    downfile.write(downscript_header)
    downfile.write('\n')
    
    for ip, _, mask in results:
        upfile.write('route add %s/%s "\${OLDGW}"\n' % (ip, mask))
        downfile.write('route delete %s/%s \${OLDGW}\n' % (ip, mask))
    
    downfile.write('\n\nrm /tmp/pptp_oldgw\n')
    upfile.close()
    downfile.close()

def generate_win(metric):
    results = fetch_ip_data()  

    upscript_header = textwrap.dedent("""@echo off
    for /F "tokens=3" %%* in ('route print ^| findstr "\\<0.0.0.0\\>"') do set "gw=%%*"
    
    """)
    
    upfile = open('vpnup.bat', 'w', encoding='utf-8')
    downfile = open('vpndown.bat', 'w', encoding='utf-8')
    
    upfile.write(upscript_header)
    upfile.write('\n')
    upfile.write('ipconfig /flushdns\n\n')
    
    downfile.write("@echo off\n")
    
    for ip, mask, _ in results:
        upfile.write('route add %s mask %s %s metric %d\n' % (ip, mask, "%gw%", metric))
        downfile.write('route delete %s\n' % (ip))
    
    upfile.close()
    downfile.close()

def generate_android(metric):
    results = fetch_ip_data()
    
    upscript_header = textwrap.dedent("""\
    #!/bin/sh
    alias nestat='/system/xbin/busybox netstat'
    alias grep='/system/xbin/busybox grep'
    alias awk='/system/xbin/busybox awk'
    alias route='/system/xbin/busybox route'
    
    OLDGW=`netstat -rn | grep ^0\.0\.0\.0 | awk '{print $2}'`
    
    """)
    
    downscript_header = textwrap.dedent("""\
    #!/bin/sh
    alias route='/system/xbin/busybox route'
    
    """)
    
    upfile = open('vpnup.sh', 'w', encoding='utf-8')
    downfile = open('vpndown.sh', 'w', encoding='utf-8')
    
    upfile.write(upscript_header)
    upfile.write('\n')
    downfile.write(downscript_header)
    downfile.write('\n')
    
    for ip, mask, _ in results:
        upfile.write('route add -net %s netmask %s gw \$OLDGW\n' % (ip, mask))
        downfile.write('route del -net %s netmask %s\n' % (ip, mask))
    
    upfile.close()
    downfile.close()

def fetch_ip_data():
    print("Fetching data from apnic.net, it might take a few minutes, please wait...")
    url = r'https://apnic.net'
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }
    
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=60) as response:
            data = response.read().decode('utf-8')
    except Exception as e:
        print(f"抓取数据失败: {e}", file=sys.stderr)
        sys.exit(1)
    
    cnregex = re.compile(r'apnic\|cn\|ipv4\|[0-9\.]+\|[0-9]+\|[0-9]+\|a.*', re.IGNORECASE)
    cndata = cnregex.findall(data)
    
    results = []

    for item in cndata:
        unit_items = item.split('|')
        starting_ip = unit_items[3]          # 修复：获取正确的起始IP位置
        num_ip = int(unit_items[4])          # 修复：获取正确的IP数量位置
        
        imask = 0xffffffff ^ (num_ip - 1)
        imask = hex(imask)[2:]
        imask = imask.zfill(8)
        
        # 修复：正确解构生成4段式点分十进制掩码
        mask = [imask[0:2], imask[2:4], imask[4:6], imask[6:8]]
        mask = [int(i, 16) for i in mask]
        mask_str = "%d.%d.%d.%d" % tuple(mask)
        
        mask2 = 32 - int(math.log(num_ip, 2))
        results.append((starting_ip, mask_str, mask2))
         
    return results

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Generate routing rules for vpn.")
    parser.add_argument('-p', '--platform',
                        dest='platform',
                        default='openvpn',
                        nargs='?',
                        help="Target platforms, it can be openvpn, mac, linux, win, android. openvpn by default.")
    parser.add_argument('-m', '--metric',
                        dest='metric',
                        default=5,
                        nargs='?',
                        type=int,
                        help="Metric setting for the route rules")
    
    args = parser.parse_args()
    
    if args.platform.lower() == 'openvpn':
        generate_ovpn(args.metric)
    elif args.platform.lower() == 'linux':
        generate_linux(args.metric)
    elif args.platform.lower() == 'mac' or args.platform.lower() == 'darwin':
        generate_mac(args.metric)
    elif args.platform.lower() == 'win':
        generate_win(args.metric)
    elif args.platform.lower() == 'android':
        generate_android(args.metric)
    else:
        print(f"Platform {args.platform} is not supported.", file=sys.stderr)
        exit(1)
