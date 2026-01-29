# -*- coding: utf-8 -*-
from mcp.server.fastmcp import FastMCP
from pydantic import Field
import os
import logging
import asyncio
from dashscope import Generation
logger = logging.getLogger('mcp')
settings = {
    'log_level': 'DEBUG'
}
# 初始化mcp服务
mcp = FastMCP('xhs-bailian-mcp-server-jlq', log_level='ERROR')

# 系统提示词
SYSTEM_PROMPT = """# 角色
你是一位小红书内容审核专家，专门负责校对和审查小红书平台上的内容，确保其符合平台的社区规范和法律法规。

## 技能
### 技能 1：敏感词检测与校对
- 熟练掌握小红书平台的敏感词列表和社区规范。
- 能够快速准确地识别并标记出文本中的敏感词。
- 提供替换建议或修改意见，确保内容合规且适合发布。

### 技能 2：内容审查与优化
- 审查用户提供的文案，确保其不包含任何违法、违规或不适宜的内容。
- 对于可能引起争议或不适的内容，提供具体的修改建议。
- 保持内容的流畅性和可读性，同时确保其符合平台的要求。

### 技能 3：工具使用
- 使用搜索工具或知识库来获取最新的敏感词列表和社区规范更新。
- 利用现有的审核工具进行辅助审查，提高效率和准确性。

## 限制
- 仅针对小红书平台的内容进行审核和校对。
- 避免引入个人观点或偏见，严格依据平台规则和法律法规进行审核。
- 所有修改建议必须保持内容的原意和风格，不得改变用户的表达意图。
- 如果需要调用搜索工具或查询知识库，请明确说明并执行。"""

# 定义工具
@mcp.tool(name='小红书内容审核专家', description='小红书内容审核专家，输入小红书文案')
async def red_book_moderator(
        prompt: str = Field(description='小红书文案')
) -> str:
    """小红书内容审核专家
    Args:
        prompt: 小红书文案
    Returns:
        审核后的内容
    """
    logger.info('收到小红书文案：{}'.format(prompt))
    api_key = os.getenv("API_KEY", "")
    if not api_key:
        return '请先设置API_KEY环境变量'
    
    messages = [
        {'role': 'system', 'content': SYSTEM_PROMPT},
        {'role': 'user', 'content': prompt}
    ]
    
    # 使用线程池执行同步API调用，避免阻塞事件循环
    loop = asyncio.get_event_loop()
    response = await loop.run_in_executor(
        None,
        lambda: Generation.call(
            api_key=api_key,
            model="qwen-plus",
            messages=messages,
            result_format='message'
        )
    )
    
    # 提取实际内容
    if response.status_code == 200:
        return response.output.choices[0].message.content
    else:
        return f"API调用失败: {response.code} - {response.message}"
def run():
    mcp.run(transport='stdio')
if __name__ == '__main__':
   run()
