#!/usr/bin/env python3
"""
抖音直播间链接解析工具
帮助从分享链接中提取直播间ID
"""
import requests
import re
import urllib.parse
from typing import Optional, Tuple


def resolve_douyin_short_url(short_url: str) -> Optional[str]:
    """
    解析抖音短链接，获取真实URL
    
    参数:
        short_url: 抖音短链接，如 https://v.douyin.com/xxxxx/
    
    返回:
        真实的直播间URL，或None
    """
    try:
        # 抖音短链接通常需要重定向
        headers = {
            'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.0 Mobile/15E148 Safari/604.1'
        }
        
        # 跟随重定向
        response = requests.head(short_url, headers=headers, allow_redirects=True, timeout=10)
        
        real_url = response.url
        print(f"✅ 解析成功: {real_url}")
        
        return real_url
        
    except Exception as e:
        print(f"❌ 解析失败: {e}")
        return None


def extract_room_id_from_url(url: str) -> Optional[str]:
    """
    从URL中提取直播间ID
    
    参数:
        url: 直播间URL
    
    返回:
        直播间ID，或None
    """
    # 尝试多种模式匹配
    patterns = [
        # 模式1: webcast/room/7305234567890123456
        r'webcast/room/(\d+)',
        # 模式2: room_id=7305234567890123456
        r'room_id[=:](\d+)',
        # 模式3: /live/7305234567890123456
        r'/live/(\d+)',
        # 模式4: 纯数字ID (16-20位数字)
        r'(?<!\d)(\d{16,20})(?!\d)',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            room_id = match.group(1)
            print(f"✅ 提取到直播间ID: {room_id}")
            return room_id
    
    print(f"❌ 无法从URL中提取直播间ID")
    return None


def get_room_info_by_share_link(share_link: str) -> Tuple[Optional[str], Optional[str]]:
    """
    通过分享链接获取直播间信息
    
    参数:
        share_link: 直播间分享链接
    
    返回:
        (真实URL, 直播间ID)
    """
    print("=" * 60)
    print("🔍 开始解析直播间链接")
    print("=" * 60)
    print(f"输入链接: {share_link}")
    print()
    
    # 1. 解析短链接
    real_url = resolve_douyin_short_url(share_link)
    if not real_url:
        print("⚠️ 无法解析短链接，尝试直接从输入提取...")
        real_url = share_link
    
    print()
    
    # 2. 提取直播间ID
    room_id = extract_room_id_from_url(real_url)
    
    print()
    print("=" * 60)
    
    if room_id:
        print("✅ 解析成功！")
        print(f"真实URL: {real_url}")
        print(f"直播间ID: {room_id}")
    else:
        print("❌ 解析失败")
        print("请尝试以下方法手动获取：")
        print("1. 打开直播间")
        print("2. 点击分享")
        print("3. 复制完整链接")
        print("4. 在链接中查找 room_id 参数或纯数字ID")
    
    print("=" * 60)
    
    return real_url, room_id


def manual_extraction_guide():
    """
    手动提取指南
    """
    print("\n" + "=" * 60)
    print("📖 手动获取直播间ID指南")
    print("=" * 60)
    print()
    print("方法1: 从分享链接提取")
    print("  1. 在抖音APP中打开直播间")
    print("  2. 点击右下角的分享按钮")
    print("  3. 选择'复制链接'")
    print("  4. 将链接粘贴到浏览器")
    print("  5. 在地址栏中查找 room_id= 后面的数字")
    print()
    print("方法2: 从主播后台查看")
    print("  1. 打开抖音主播后台")
    print("  2. 进入直播间管理")
    print("  3. 查看直播间详情")
    print("  4. 找到直播间ID")
    print()
    print("方法3: 使用开发者工具")
    print("  1. 在网页版抖音打开直播间")
    print("  2. 按F12打开开发者工具")
    print("  3. 在Network标签中查找请求")
    print("  4. 查找包含 room_id 的请求")
    print()
    print("=" * 60)


def main():
    """主函数"""
    import sys
    
    if len(sys.argv) > 1:
        share_link = sys.argv[1]
        get_room_info_by_share_link(share_link)
    else:
        print("抖音直播间链接解析工具")
        print("=" * 60)
        print()
        print("使用方法:")
        print("  python room_link_parser.py <直播间分享链接>")
        print()
        print("示例:")
        print("  python room_link_parser.py https://v.douyin.com/xxxxx/")
        print()
        manual_extraction_guide()


if __name__ == "__main__":
    main()
