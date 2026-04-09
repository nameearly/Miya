"""
网络搜索工具 - web_agent专用
"""

from typing import Dict, Any
import logging
import httpx
import os

logger = logging.getLogger(__name__)


async def execute(args: Dict[str, Any], context: Dict[str, Any]) -> str:
    """执行网络搜索"""
    query = args.get("query", "")
    count = args.get("count", 5)

    if not query:
        return "请提供搜索关键词"

    try:
        # 优先使用配置的API
        from core.system_config import get_api_url

        bing_key = os.getenv("BING_API_KEY", "")
        search_url = (
            get_api_url("bing_search") or "https://api.bing.microsoft.com/v7.0/search"
        )

        if bing_key:
            headers = {"Ocp-Apim-Subscription-Key": bing_key}
            params = {"q": query, "count": count, "mkt": "zh-CN"}

            async with httpx.AsyncClient(timeout=15, headers=headers) as client:
                resp = await client.get(search_url, params=params)

                if resp.status_code == 200:
                    data = resp.json()
                    web_pages = data.get("webPages", {}).get("value", [])

                    if not web_pages:
                        return f"未找到与'{query}'相关的搜索结果"

                    result = f"【搜索结果: {query}】\n\n"

                    for i, item in enumerate(web_pages[:count], 1):
                        title = item.get("name", "")
                        snippet = item.get("snippet", "")
                        url = item.get("url", "")

                        if title:
                            result += f"{i}. {title}\n"
                            if snippet:
                                result += f"   {snippet[:100]}...\n"
                            result += f"   链接: {url}\n\n"

                    return result
                else:
                    return f"搜索失败: HTTP {resp.status_code}"
        else:
            # 无API key时使用备用方案
            return f"网络搜索需要配置BING_API_KEY\n当前搜索关键词: {query}\n\n(搜索功能暂时不可用，请配置API后重试)"

    except Exception as e:
        logger.error(f"网络搜索失败: {e}")
        return f"搜索失败: {str(e)[:50]}"
