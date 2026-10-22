#!/usr/bin/env python3
import urllib.request
import sys

def generate_android_routes():
    # 采用你指定的 MetaCubeX 官方最新全量中国 GeoIP 地址列表
    url = 'https://raw.githubusercontent.com/MetaCubeX/meta-rules-dat/refs/heads/meta/geo/geoip/cn.list'
    print("正在从 MetaCubeX 镜像源抓取最新中国 IP 列表...")
    
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
        
    print("正在过滤 IPv6 并转换为 OpenVPN Android 客户端专用排除格式...")
    routes = []
    
    for line in data.splitlines():
        line = line.strip()
        # 跳过空行和注释行
        if not line or line.startswith('#'):
            continue
            
        # 核心过滤：只有含有 '/' 且绝对不含 ':' 冒号的才是合规的 IPv4 网段
        if '/' in line and ':' not in line:
            # 蓝色客户端导入极其方便，可以直接识别标准 CIDR (如 1.0.1.0/24) 格式的行
            # 只要每行只留 IPv4 即可，无需再加上 net_gateway 的尾巴，客户端会自动识别为排除
            routes.append(line)

    if not routes:
        print("错误：未能在数据源中解析到任何有效的 IPv4 中国网段！", file=sys.stderr)
        sys.exit(1)

    print(f"解析成功！共转换了 {len(routes)} 条合规的中国大陆 IPv4 排除规则。")
    
    # 写入文件
    with open('routes.txt', 'w', encoding='utf-8') as f:
        f.write("\n".join(routes))
        f.write("\n")
        
    print("用于蓝色客户端独立导入的 routes.txt 文件已成功生成！")

if __name__ == '__main__':
    generate_android_routes()
