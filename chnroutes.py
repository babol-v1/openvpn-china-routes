#!/usr/bin/env python3
import re
import urllib.request
import sys

def fetch_chnroutes():
    url = 'http://apnic.net'
    print("正在从 APNIC 抓取最新数据...")
    
    # 模拟真实浏览器，防止被服务器 403 拒绝
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }
    
    try:
        req = urllib.request.Request(url, headers=headers)
        response = urllib.request.urlopen(req, timeout=30)
        return response.read().decode('utf-8')
    except Exception as e:
        print(f"抓取数据失败: {e}")
        sys.exit(1)

def generate_routes():
    data = fetch_chnroutes()
    routes = []
    
    # 匹配中国大陆的 IPv4 分配网段
    pattern = re.compile(r'apnic\|cn\|ipv4\|([\d\.]+)\|(\d+)\|', re.IGNORECASE)
    
    for match in pattern.finditer(data):
        ip = match.group(1)
        count = int(match.group(2))
        
        # 将 IP 数量转换为子网掩码长度
        mask_len = 32
        while count > 1:
            count >>= 1
            mask_len -= 1
            
        # 将掩码长度转换为点分十进制格式 (e.g. 255.255.255.0)
        mask = []
        for i in range(4):
            if mask_len >= 8:
                mask.append(255)
                mask_len -= 8
            elif mask_len > 0:
                mask.append(256 - (1 << (8 - mask_len)))
                mask_len = 0
            else:
                mask.append(0)
                
        mask_str = ".".join(map(str, mask))
        routes.append(f"route {ip} {mask_str} net_gateway")

    if not routes:
        print("未提取到任何有效的中国 IP 网段，请检查网络。")
        sys.exit(1)

    with open('routes.txt', 'w', encoding='utf-8') as f:
        f.write("# === 全量中国大陆 IP 绕行路由表 (Python3 自动生成) ===\n")
        f.write("\n".join(routes))
        f.write("\n")
        
    print(f"成功生成 routes.txt，共包含 {len(routes)} 条路由规则！")

if __name__ == '__main__':
    generate_routes()
