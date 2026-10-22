#!/usr/bin/env python3
import re
import urllib.request
import sys
import math

def generate_ovpn_routes():
    url = 'https://apnic.net'
    print("正在从 APNIC 抓取最新全球 IP 分配表...")
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }
    
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=60) as response:
            data = response.read().decode('utf-8')
    except Exception as e:
        print(f"数据抓取失败: {e}", file=sys.stderr)
        sys.exit(1)
        
    print("正在解析中国大陆 IPv4 网段...")
    routes = []
    
    # 使用通用的正则表达式匹配中国大陆的 ipv4 行，防范各镜像源开头的格式差异
    # 格式通常形如: xxx|cn|ipv4|1.0.1.0|256|...
    pattern = re.compile(r'cn\|ipv4\|([\d\.]+)\|(\d+)\|', re.IGNORECASE)
    
    for line in data.splitlines():
        match = pattern.search(line)
        if match:
            ip = match.group(1)
            count = int(match.group(2))
            
            try:
                # 计算子网掩码长度 (例如 256 对应 /24)
                mask_cidr = 32 - int(math.log(count, 2))
                
                # 将 CIDR 长度转换为 4 段点分十进制掩码 (e.g. 255.255.255.0)
                mask_bits = (0xffffffff << (32 - mask_cidr)) & 0xffffffff
                mask_str = f"{(mask_bits >> 24) & 255}.{(mask_bits >> 16) & 255}.{(mask_bits >> 8) & 255}.{mask_bits & 255}"
                
                routes.append(f"route {ip} {mask_str} net_gateway 5")
            except Exception as parse_err:
                # 略过可能由于垃圾数据导致的计算错误行
                continue

    if not routes:
        print("错误：未能成功解析到任何中国 IP 段！请检查抓取到的原始数据格式。", file=sys.stderr)
        sys.exit(1)

    print(f"解析成功！共找到 {len(routes)} 个网段。正在写入 routes.txt...")
    
    with open('routes.txt', 'w', encoding='utf-8') as f:
        f.write("# === 全量中国大陆 IP 绕行路由表 (GitHub Actions 自动更新) ===\n")
        f.write("\n".join(routes))
        f.write("\n")
        
    print("routes.txt 文件已成功生成！")

if __name__ == '__main__':
    generate_ovpn_routes()
