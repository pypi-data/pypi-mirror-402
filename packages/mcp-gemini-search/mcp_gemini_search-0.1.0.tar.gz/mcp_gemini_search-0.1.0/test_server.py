"""
测试 MCP Search Server - 直接测试搜索功能（链接模式）
"""
import asyncio
import sys
sys.path.insert(0, ".")

from server import do_search


async def main():
    print("=" * 60)
    print("测试 MCP Search 服务 - 链接返回模式")
    print("=" * 60)
    print()
    
    # 测试搜索
    query = "华侃如 Kanru Hua 相关信息"
    print(f"搜索: {query}")
    print("-" * 40)
    
    result = await do_search(
        query=query,
        max_results=10,
        model="gemini-3-pro-high"
    )
    
    print(result)
    print()
    


if __name__ == "__main__":
    asyncio.run(main())
