#!/usr/bin/env python3
import urllib.request
import sys

def main():
    # 采用你指定的 MetaCubeX 官方最新全量中国 GeoIP 地址列表
    url = 'https://raw.githubusercontent.com/MetaCubeX/meta-rules-dat/refs/heads/meta/geo/geoip/cn.list'
    print("正在从 MetaCubeX 镜像源抓取最新中国双栈 IP 列表...")
    
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
        
    print("正在分类提取纯 CIDR 格式的中国大陆双栈网段...")
    routes_v4 = []
    routes_v6 = []
    
    for line in data.splitlines():
        line = line.strip()
        if not line or line.startswith('#'):
            continue
            
        if '/' in line:
            # 过滤掉 0.0.0.0 广播或异常网段
            if line.startswith("0.0.0.0"):
                continue
                
            # 严格区分 IPv4 和 IPv6，只保留最纯粹的原始网段格式 (无前缀，无后缀)
            if ':' in line:
                routes_v6.append(line)
            else:
                routes_v4.append(line)

    if not routes_v4:
        print("错误：未能在数据源中解析到任何有效的 IPv4 中国网段！", file=sys.stderr)
        sys.exit(1)

    print(f"提取成功！共获取纯 IPv4 网段 {len(routes_v4)} 条，纯 IPv6 网段 {len(routes_v6)} 条。")
    
    # 分别保存为两个完全干净、无杂质的纯文本文件
    with open('routes_CIDR.txt', 'w', encoding='utf-8') as f:
        f.write("\n".join(routes_v4))
        f.write("\n")
        
    with open('routes_v6_CIDR.txt', 'w', encoding='utf-8') as f:
        f.write("\n".join(routes_v6))
        f.write("\n")
        
    print("routes.txt (纯IPv4版) 与 routes_v6.txt (纯IPv6版) 已全部顺利生成！")

if __name__ == '__main__':
    main()
