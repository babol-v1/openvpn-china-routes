#!/usr/bin/env python3
import urllib.request
import sys

def generate_ovpn_routes():
    # 采用你提供的 blackmatrix7 高动态全量中国 IP 数据源
    url = 'https://raw.githubusercontent.com/blackmatrix7/ios_rule_script/refs/heads/master/rule/Clash/ChinaMax/ChinaMax_IP.txt'
    print("正在从 blackmatrix7 仓库抓取全量中国 IP 列表...")
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }
    
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=60) as response:
            data = response.read().decode('utf-8')
    except Exception as e:
        print(f"数据抓取失败（尝试使用 jsd 镜像加速源...）: {e}")
        try:
            # 备用加速源
            url_backup = 'https://oncept.top'
            req = urllib.request.Request(url_backup, headers=headers)
            with urllib.request.urlopen(req, timeout=60) as response:
                data = response.read().decode('utf-8')
        except Exception as e2:
            print(f"所有数据源抓取失败: {e2}", file=sys.stderr)
            sys.exit(1)
        
    print("正在过滤 IPv6 并转换为 OpenVPN 绕行路由格式...")
    routes = []
    
    for line in data.splitlines():
        line = line.strip()
        # 跳过空行和注释行
        if not line or line.startswith('#'):
            continue
            
        # 核心逻辑：仅处理含有单个 '/' 且不含 ':' 冒号的标准 IPv4 网段
        if '/' in line and ':' not in line:
            parts = line.split('/')
            ip = parts[0]
            try:
                cidr = int(parts[1])
                # 特殊防御：过滤掉 Clash 特有的 0.0.0.0/32 广播或异常网段
                if ip == "0.0.0.0":
                    continue
                    
                # 算法：将 CIDR 位数（如 24）无损转换为四段式子网掩码（如 255.255.255.0）
                mask_bits = (0xffffffff << (32 - cidr)) & 0xffffffff
                mask_str = f"{(mask_bits >> 24) & 255}.{(mask_bits >> 16) & 255}.{(mask_bits >> 8) & 255}.{mask_bits & 255}"
                
                # 追加到 OpenVPN 标准路由表
                routes.append(f"route {ip} {mask_str} net_gateway 5")
            except Exception:
                continue

    if not routes:
        print("错误：未能在数据源中解析到任何有效的 IPv4 中国网段！", file=sys.stderr)
        sys.exit(1)

    print(f"解析成功！共转换了 {len(routes)} 条合规的中国大陆 IPv4 路由规则。")
    print(f"💡 温馨提示：记得在 .ovpn 配置文件头部加上 'max-routes {len(routes) + 50}'，否则官方客户端会报错。")
    
    with open('routes.txt', 'w', encoding='utf-8') as f:
        f.write("# === 全量中国大陆 IP 绕行路由表 (基于 blackmatrix7 自动更新) ===\n")
        f.write("\n".join(routes))
        f.write("\n")
        
    print("routes.txt 文件已顺利生成并成功保存！")

if __name__ == '__main__':
    generate_ovpn_routes()
