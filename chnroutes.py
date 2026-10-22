#!/usr/bin/env python3
import urllib.request
import sys

def generate_ovpn_routes():
    # 改用社区长期高可用、CDN 加速的中国 IPv4 地址列表镜像源
    url = 'https://githubusercontent.com'
    print("正在从稳定镜像源抓取最新中国 IP 列表...")
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }
    
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=60) as response:
            data = response.read().decode('utf-8')
    except Exception as e:
        # 如果备用源出问题，尝试另一个极速源
        print(f"主源抓取失败，正在尝试备用极速源... 错误原因: {e}")
        try:
            url_backup = 'https://oncept.top'
            req = urllib.request.Request(url_backup, headers=headers)
            with urllib.request.urlopen(req, timeout=60) as response:
                data = response.read().decode('utf-8')
        except Exception as e2:
            print(f"所有数据源抓取失败: {e2}", file=sys.stderr)
            sys.exit(1)
        
    print("正在转换为 OpenVPN 绕行路由格式...")
    routes = []
    
    # 该数据源每行直接是标准 CIDR 格式，例如: 1.0.1.0/24
    for line in data.splitlines():
        line = line.strip()
        if not line or line.startswith('#'):
            continue
            
        if '/' in line:
            parts = line.split('/')
            ip = parts[0]
            try:
                cidr = int(parts[1])
                # 将 CIDR 位数（如 24）无损转换为四段式子网掩码（如 255.255.255.0）
                mask_bits = (0xffffffff << (32 - cidr)) & 0xffffffff
                mask_str = f"{(mask_bits >> 24) & 255}.{(mask_bits >> 16) & 255}.{(mask_bits >> 8) & 255}.{mask_bits & 255}"
                
                # 写入带有默认跃点数 5 的 net_gateway 绕行规则
                routes.append(f"route {ip} {mask_str} net_gateway 5")
            except Exception:
                continue

    if not routes:
        print("错误：未能从列表中解析到有效的中国 IP 段！", file=sys.stderr)
        sys.exit(1)

    print(f"解析成功！共转换了 {len(routes)} 个合规中国大陆网段。正在写入 routes.txt...")
    
    with open('routes.txt', 'w', encoding='utf-8') as f:
        f.write("# === 全量中国大陆 IP 绕行路由表 (GitHub Actions 自动更新) ===\n")
        f.write("\n".join(routes))
        f.write("\n")
        
    print("routes.txt 文件已顺利生成完毕！")

if __name__ == '__main__':
    generate_ovpn_routes()
