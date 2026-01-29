from mcp.server.fastmcp import FastMCP

from rednote_mcp_plus.write import publish
from rednote_mcp_plus.auth import login
from typing import Annotated, List
import asyncio

mcp = FastMCP()

@mcp.tool()
async def manualLogin():
    """登录小红书账号，获取登录Cookies"""
    result = await login.manualLogin()
    return result

@mcp.tool()
async def publishText(
    image_urls: Annotated[List[str], "图片URL列表"],
    title: Annotated[str, "笔记标题"],
    content: Annotated[str, "笔记内容"],
    tags: Annotated[List[str], "标签列表"]
) -> str:
    """
    发布小红书图文笔记
    :param image_urls: 图片URL列表
    :param title: 笔记标题
    :param content: 笔记内容
    :param tags: 标签列表
    :return: 发布结果
    """
    result = await publish.publishText(image_urls, title, content, tags)
    return result

if __name__ == "__main__":
    mcp.run(transport='stdio') 
    # result = asyncio.run(publish.publishText(
    #     image_urls=["src/rednote_mcp_plus/static/images/ball.png"],
    #     title="这是一个测试标题",
    #     content="这是一个测试内容",
    #     tags=["测试", "小红书"]
    # ))
    # print(result) 
