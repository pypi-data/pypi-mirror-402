"""
对比 Pro 和 Flash 模型的搜索质量
"""
import asyncio
import sys
sys.path.insert(0, ".")

from server import do_search


async def main():
    query = "华侃如 Kanru Hua"
    max_results = 10
    
    print("=" * 70)
    print(f"搜索对比测试: {query} (各返回 {max_results} 条)")
    print("=" * 70)
    
    # 测试 gemini-3-flash
    print("\n" + "=" * 70)
    print("🚀 gemini-3-flash 搜索结果:")
    print("=" * 70)
    
    result_flash = await do_search(
        query=query,
        max_results=max_results,
        model="gemini-3-flash"
    )
    print(result_flash)
    
    # 清除缓存以确保公平比较
    from server import _cache
    _cache.clear()
    
    # 测试 gemini-3-pro-high
    print("\n" + "=" * 70)
    print("🔥 gemini-3-pro-high 搜索结果:")
    print("=" * 70)
    
    result_pro = await do_search(
        query=query,
        max_results=max_results,
        model="gemini-3-pro-high"
    )
    print(result_pro)
    
    # 简单统计
    print("\n" + "=" * 70)
    print("📊 对比统计:")
    print("=" * 70)
    print(f"Flash 结果长度: {len(result_flash)} 字符")
    print(f"Pro 结果长度: {len(result_pro)} 字符")


if __name__ == "__main__":
    asyncio.run(main())
