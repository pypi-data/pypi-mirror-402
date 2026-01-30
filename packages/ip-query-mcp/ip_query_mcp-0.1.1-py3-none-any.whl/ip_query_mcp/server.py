"""IP Query MCP Server implementation."""

import asyncio
import re
import socket
from typing import Any
import httpx
from mcp.server import Server
from mcp.types import Tool, TextContent
import mcp.server.stdio


# IP 查询服务配置
IP_SERVICES = {
    "domestic": [
        "http://myip.ipip.net",  # 国内服务，纯文本（使用 http）
        "http://ip-api.com/json/?lang=zh-CN",  # 支持中文的服务
        "http://ip.3322.net",  # 国内服务
        "http://pv.sohu.com/cityjson?ie=utf-8",  # 搜狐 IP 服务
        "https://api.ipify.org?format=json",  # 备用国际服务
    ],
    "international": [
        "https://1.1.1.1/cdn-cgi/trace",  # Cloudflare
        "https://api.ipify.org?format=json",  # 国际服务
        "https://api64.ipify.org?format=json",  # IPv4/IPv6
        "https://ifconfig.me/ip",  # 纯文本
    ]
}

# IP 地理位置查询服务
GEO_SERVICES = [
    "https://ipapi.co/{ip}/json/",  # 免费，支持中文
    "https://ipinfo.io/{ip}/json",  # 免费，英文
    "http://ip-api.com/json/{ip}?lang=zh-CN",  # 免费，支持中文
]


async def get_local_ip() -> str:
    """获取本机内网 IP 地址（优先返回局域网 IP）."""
    try:
        import netifaces
        
        # 获取所有网络接口
        interfaces = netifaces.interfaces()
        local_ips = []
        
        for interface in interfaces:
            addrs = netifaces.ifaddresses(interface)
            # 获取 IPv4 地址
            if netifaces.AF_INET in addrs:
                for addr_info in addrs[netifaces.AF_INET]:
                    ip = addr_info.get('addr')
                    if ip and ip != '127.0.0.1':
                        local_ips.append(ip)
        
        # 优先返回局域网 IP（192.168.x.x, 10.x.x.x, 172.16-31.x.x）
        for ip in local_ips:
            if ip.startswith('192.168.') or ip.startswith('10.') or \
               (ip.startswith('172.') and 16 <= int(ip.split('.')[1]) <= 31):
                return ip
        
        # 如果没有局域网 IP，返回第一个非回环地址
        if local_ips:
            return local_ips[0]
        
        return "无法获取"
    except ImportError:
        # 如果没有 netifaces，使用原来的方法
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            local_ip = s.getsockname()[0]
            s.close()
            return local_ip
        except Exception:
            return "无法获取"
    except Exception:
        return "无法获取"


async def query_ip_service(url: str, timeout: float = 5.0) -> str | None:
    """查询单个 IP 服务."""
    try:
        async with httpx.AsyncClient(timeout=timeout, follow_redirects=True) as client:
            response = await client.get(url)
            response.raise_for_status()
            
            # 处理不同的响应格式
            if "json" in url or url.endswith("?format=json") or "ip-api.com" in url:
                data = response.json()
                # ip-api.com 返回 query 字段
                ip = data.get("query") or data.get("ip", "")
                return ip.strip() if ip else None
            elif "trace" in url:
                # Cloudflare trace 格式
                for line in response.text.split("\n"):
                    if line.startswith("ip="):
                        return line.split("=")[1].strip()
            else:
                # 纯文本格式，提取 IP 地址
                import re
                text = response.text.strip()
                # 尝试从文本中提取 IP 地址
                ip_pattern = r'\b(?:\d{1,3}\.){3}\d{1,3}\b'
                match = re.search(ip_pattern, text)
                if match:
                    return match.group(0)
                return text if text else None
    except Exception as e:
        return None


async def get_public_ip_from_services(services: list[str]) -> str | None:
    """从服务列表中获取公网 IP（并发查询，返回最快的结果）."""
    tasks = [query_ip_service(url) for url in services]
    
    # 使用 as_completed 获取最快的成功结果
    for coro in asyncio.as_completed(tasks):
        result = await coro
        if result:
            return result
    
    return None


async def get_ip_geolocation(ip: str) -> dict[str, Any] | None:
    """查询 IP 地理位置信息."""
    for service_url in GEO_SERVICES:
        try:
            url = service_url.format(ip=ip)
            # 禁用代理，避免 VPN 关闭后代理失效
            async with httpx.AsyncClient(
                timeout=5.0, 
                follow_redirects=True,
                trust_env=False  # 禁用环境变量中的代理设置
            ) as client:
                response = await client.get(url)
                response.raise_for_status()
                data = response.json()
                
                # 统一不同 API 的返回格式
                if "ipapi.co" in url:
                    return {
                        "ip": data.get("ip"),
                        "country": data.get("country_name"),
                        "region": data.get("region"),
                        "city": data.get("city"),
                        "isp": data.get("org"),
                        "timezone": data.get("timezone"),
                    }
                elif "ipinfo.io" in url:
                    location = data.get("loc", "").split(",")
                    return {
                        "ip": data.get("ip"),
                        "country": data.get("country"),
                        "region": data.get("region"),
                        "city": data.get("city"),
                        "isp": data.get("org"),
                        "timezone": data.get("timezone"),
                        "location": f"{location[0]}, {location[1]}" if len(location) == 2 else None,
                    }
                elif "ip-api.com" in url:
                    return {
                        "ip": data.get("query"),
                        "country": data.get("country"),
                        "region": data.get("regionName"),
                        "city": data.get("city"),
                        "isp": data.get("isp"),
                        "timezone": data.get("timezone"),
                    }
        except Exception:
            continue
    
    return None


def is_ipv6(ip: str) -> bool:
    """判断是否为 IPv6 地址."""
    return ":" in ip


async def get_all_ips() -> dict[str, Any]:
    """获取所有 IP 信息（内网、真实公网、代理公网）."""
    # 并发查询所有信息
    local_ip_task = get_local_ip()
    domestic_ip_task = get_public_ip_from_services(IP_SERVICES["domestic"])
    international_ip_task = get_public_ip_from_services(IP_SERVICES["international"])
    
    local_ip, domestic_ip, international_ip = await asyncio.gather(
        local_ip_task,
        domestic_ip_task,
        international_ip_task,
        return_exceptions=True
    )
    
    # 处理异常
    if isinstance(local_ip, Exception):
        local_ip = "无法获取"
    if isinstance(domestic_ip, Exception):
        domestic_ip = None
    if isinstance(international_ip, Exception):
        international_ip = None
    
    # 判断是否使用了 VPN
    # 只有当两个 IP 都存在、协议版本相同、但 IP 不同时，才判断为 VPN
    vpn_detected = False
    if domestic_ip and international_ip:
        # 检查是否为同一协议版本
        domestic_is_v6 = is_ipv6(domestic_ip)
        international_is_v6 = is_ipv6(international_ip)
        
        # 只有同协议版本的 IP 不同时，才判断为 VPN
        if domestic_is_v6 == international_is_v6 and domestic_ip != international_ip:
            vpn_detected = True
    
    # 优先使用国内服务获取的 IP 作为真实 IP
    real_ip = domestic_ip or international_ip
    
    result = {
        "local_ip": local_ip,
        "public_ip": real_ip or "无法获取",  # 显示真实 IP
        "vpn_detected": vpn_detected,
    }
    
    if vpn_detected:
        result["real_ip"] = domestic_ip  # 真实 IP（国内服务获取）
        result["vpn_ip"] = international_ip  # VPN IP（国际服务获取）
    
    return result


# 创建 MCP 服务器
app = Server("ip-query-mcp")


@app.list_tools()
async def list_tools() -> list[Tool]:
    """列出可用的工具."""
    return [
        Tool(
            name="get_my_ip",
            description="快速查询我的 IP 地址。开着 VPN 时显示公网 IP + VPN IP + 内网 IP，"
                       "没开 VPN 时显示公网 IP + 内网 IP。",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": [],
            },
        ),
        Tool(
            name="get_ip_with_location",
            description="查询 IP 地址及地理位置信息（国家、地区、城市、ISP 等）。"
                       "开着 VPN 时显示公网 IP 和 VPN IP 的位置，没开 VPN 时显示公网 IP 的位置。",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": [],
            },
        ),
        Tool(
            name="get_ip_geolocation",
            description="查询指定 IP 地址的地理位置信息，包括国家、地区、城市、ISP、时区等",
            inputSchema={
                "type": "object",
                "properties": {
                    "ip": {
                        "type": "string",
                        "description": "要查询的 IP 地址",
                    }
                },
                "required": ["ip"],
            },
        ),
    ]


@app.call_tool()
async def call_tool(name: str, arguments: Any) -> list[TextContent]:
    """处理工具调用."""
    
    if name == "get_my_ip":
        ip_info = await get_all_ips()
        
        # 简洁输出
        if ip_info["vpn_detected"]:
            # 开着 VPN：显示公网 IP + VPN IP + 内网 IP
            lines = [
                f"公网 IP: {ip_info['real_ip']}",
                f"VPN IP: {ip_info['vpn_ip']}",
                f"内网 IP: {ip_info['local_ip']}",
            ]
        else:
            # 没开 VPN：显示公网 IP + 内网 IP
            lines = [
                f"公网 IP: {ip_info['public_ip']}",
                f"内网 IP: {ip_info['local_ip']}",
            ]
        
        return [TextContent(type="text", text="\n".join(lines))]
    
    elif name == "get_ip_with_location":
        ip_info = await get_all_ips()
        
        lines = []
        
        if ip_info["vpn_detected"]:
            # 开着 VPN：显示公网 IP + VPN IP + 内网 IP，并查询两个 IP 的地理位置
            lines.append(f"公网 IP: {ip_info['real_ip']}")
            lines.append(f"VPN IP: {ip_info['vpn_ip']}")
            lines.append(f"内网 IP: {ip_info['local_ip']}")
            
            # 查询公网 IP 的地理位置
            if ip_info['real_ip'] and ip_info['real_ip'] != "无法获取":
                geo = await get_ip_geolocation(ip_info['real_ip'])
                if geo:
                    lines.append(f"\n📍 公网 IP 地理位置:")
                    if geo.get("country"):
                        lines.append(f"  国家: {geo['country']}")
                    if geo.get("region"):
                        lines.append(f"  地区: {geo['region']}")
                    if geo.get("city"):
                        lines.append(f"  城市: {geo['city']}")
                    if geo.get("isp"):
                        lines.append(f"  ISP: {geo['isp']}")
            
            # 查询 VPN IP 的地理位置
            if ip_info['vpn_ip']:
                vpn_geo = await get_ip_geolocation(ip_info['vpn_ip'])
                if vpn_geo:
                    lines.append(f"\n📍 VPN IP 地理位置:")
                    if vpn_geo.get("country"):
                        lines.append(f"  国家: {vpn_geo['country']}")
                    if vpn_geo.get("region"):
                        lines.append(f"  地区: {vpn_geo['region']}")
                    if vpn_geo.get("city"):
                        lines.append(f"  城市: {vpn_geo['city']}")
                    if vpn_geo.get("isp"):
                        lines.append(f"  ISP: {vpn_geo['isp']}")
        else:
            # 没开 VPN：显示公网 IP + 内网 IP
            lines.append(f"公网 IP: {ip_info['public_ip']}")
            lines.append(f"内网 IP: {ip_info['local_ip']}")
            
            # 查询公网 IP 的地理位置
            if ip_info['public_ip'] and ip_info['public_ip'] != "无法获取":
                geo = await get_ip_geolocation(ip_info['public_ip'])
                if geo:
                    lines.append(f"\n📍 地理位置:")
                    if geo.get("country"):
                        lines.append(f"  国家: {geo['country']}")
                    if geo.get("region"):
                        lines.append(f"  地区: {geo['region']}")
                    if geo.get("city"):
                        lines.append(f"  城市: {geo['city']}")
                    if geo.get("isp"):
                        lines.append(f"  ISP: {geo['isp']}")
                    if geo.get("timezone"):
                        lines.append(f"  时区: {geo['timezone']}")
        
        return [TextContent(type="text", text="\n".join(lines))]
    
    elif name == "get_ip_geolocation":
        ip = arguments.get("ip")
        if not ip:
            return [TextContent(type="text", text="错误: 请提供 IP 地址")]
        
        geo = await get_ip_geolocation(ip)
        if not geo:
            return [TextContent(type="text", text=f"无法获取 IP {ip} 的地理位置信息")]
        
        lines = [f"IP: {geo.get('ip', ip)}"]
        if geo.get("country"):
            lines.append(f"国家: {geo['country']}")
        if geo.get("region"):
            lines.append(f"地区: {geo['region']}")
        if geo.get("city"):
            lines.append(f"城市: {geo['city']}")
        if geo.get("isp"):
            lines.append(f"ISP: {geo['isp']}")
        if geo.get("timezone"):
            lines.append(f"时区: {geo['timezone']}")
        if geo.get("location"):
            lines.append(f"坐标: {geo['location']}")
        
        return [TextContent(type="text", text="\n".join(lines))]
    
    else:
        raise ValueError(f"未知工具: {name}")


async def serve():
    """运行 MCP 服务器."""
    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
        await app.run(
            read_stream,
            write_stream,
            app.create_initialization_options()
        )
