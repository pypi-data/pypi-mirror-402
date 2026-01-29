"""
测试 MCP Search - 完整输出
"""
import asyncio
import sys
sys.path.insert(0, ".")

from server import do_search


async def main():
    query = "华侃如 Kanru Hua"
    
    print("=" * 80)
    print(f"搜索: {query}")
    print("=" * 80)
    
    result = await do_search(
        query=query,
        max_results=10,
        model="gemini-3-flash"
    )
    
    # 写入文件以便完整查看
    with open("search_result.txt", "w", encoding="utf-8") as f:
        f.write(result)
    
    print(result)
    print()
    print("=" * 80)
    print("完整结果已保存到 search_result.txt")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(main())
