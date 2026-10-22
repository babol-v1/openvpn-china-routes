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
        
    print("正在分类解析并转换为可直接添加至 .ovpn 的标准路由指令...")
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
                
            # 区分 IPv4 和 IPv6 并转换为 OpenVPN 标准支持的格式
            if ':' in line:
                # 【核心修复】IPv6 路由排除必须显式指定 net_gateway-ipv6 后缀，才能被客户端识别为“排除的网络”
                routes_v6.append(f"route-ipv6 {line} net_gateway-ipv6")
            else:
                # IPv4 沿用你测试通过的拆分掩码经典格式
                parts = line.split('/')
                ip = parts
                try:
                    cidr = int(parts)
                    mask_bits = (0xffffffff << (32 - cidr)) & 0xffffffff
                    mask_str = f"{(mask_bits >> 24) & 255}.{(mask_bits >> 16) & 255}.{(mask_bits >> 8) & 255}.{mask_bits & 255}"
                    routes_v4.append(f"route {ip} {mask_str} net_gateway")
                except Exception:
                    continue

    if not routes_v4:
        print("错误：未能在数据源中解析到任何有效的 IPv4 中国网段！", file=sys.stderr)
        sys.exit(1)

    print(f"解析成功！共转换 IPv4 路由指令 {len(routes_v4)} 条，IPv6 路由指令 {len(routes_v6)} 条。")
    
    # 分别保存为两个独立的、可直接无脑追加到 .ovpn 末尾的文件
    with open('routes.txt', 'w', encoding='utf-8') as f:
        f.write("# === 全量中国大陆 IPv4 绕行路由表（可直接追加至 .ovpn 末尾） ===\n")
        f.write("\n".join(routes_v4))
        f.write("\n")
        
    with open('routes_v6.txt', 'w', encoding='utf-8') as f:
        f.write("# === 全量中国大陆 IPv6 绕行路由表（可直接追加至 .ovpn 末尾） ===\n")
        f.write("\n".join(routes_v6))
        f.write("\n")
        
    print("routes.txt (IPv4版) 与 routes_v6.txt (IPv6版) 已全部完美生成！")

if __name__ == '__main__':
    main()
