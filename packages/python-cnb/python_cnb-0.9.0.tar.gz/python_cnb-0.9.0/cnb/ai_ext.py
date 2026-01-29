# AI Service Extensions - Manual implementation for streaming and additional AI features
# This file extends the AiService class with streaming support

import json
from typing import Generator, Union
from .ai import AiService
from .models import dto

class AiService(AiService):
    """
    扩展的 AiService 类，添加流式输出支持
    Extended AiService class with streaming support
    """
    
    def request_stream(self, method: str, endpoint: str, **kwargs) -> Generator[str, None, None]:
        """
        发送流式请求并逐行返回数据
        Send streaming request and yield data line by line
        """
        response = self._client.session.request(
            method=method,
            url=f"{self._client.base_url}{endpoint}",
            stream=True,  # 启用流式响应
            **kwargs
        )
        response.raise_for_status()
        response.encoding = 'utf-8'  # 强制使用 UTF-8 解码
        
        # 逐行读取流式响应
        for line in response.iter_lines(decode_unicode=True):
            if line:
                # 处理 Server-Sent Events 格式
                if line.startswith('data: '):
                    data = line[6:]  # 移除 'data: ' 前缀
                    if data.strip() == '[DONE]':
                        break
                    yield data
                elif line.strip():
                    # 处理其他格式的流式数据
                    yield line

    # AI 对话。调用者需有代码写权限（CI 中使用 CNB_TOKEN 不检查写权限）。AI chat completions. Requires caller to have repo write permission (except when using CNB_TOKEN in CI).
    def ai_chat_completions(self,
                          repo: str,
                          body_params: dto.AiChatCompletionsReq,
                          ) -> Union[dto.AiChatCompletionsResult, Generator[str, None, None]]:
        u = "/%s/-/ai/chat/completions" % (repo,)
        
        # 根据 stream 参数决定输出格式
        if body_params.stream:
            # 流式输出：返回生成器
            return self.request_stream(
                method="POST",
                endpoint=u,
                json=body_params.to_dict(),
            )
        else:
            # 非流式输出：使用标准请求
            data = self._client.request(
                method="POST", 
                endpoint=u,
                json=body_params.to_dict(),
            )
            return dto.AiChatCompletionsResult.safe_parse(data)

    def ai_chat_completions_stream(self,
                                 repo: str,
                                 body_params: dto.AiChatCompletionsReq,
                                 ) -> Generator[str, None, None]:
        # 强制启用流式输出
        body_params.stream = True
        
        # 直接调用优化后的 ai_chat_completions 方法
        return self.ai_chat_completions(repo, body_params)

    def ai_chat_completions_stream_parsed(self,
                                        repo: str,
                                        body_params: dto.AiChatCompletionsReq,
                                        ) -> Generator[dict, None, None]:
        stream_generator = self.ai_chat_completions_stream(repo, body_params)
        
        for chunk in stream_generator:
            try:
                # 尝试解析 JSON 数据
                parsed_data = json.loads(chunk)
                yield parsed_data
            except json.JSONDecodeError:
                # 如果不是有效的 JSON，跳过或记录错误
                continue

    def ai_chat_completions_stream_content(self,
                                       repo: str,
                                       body_params: dto.AiChatCompletionsReq,
                                       ) -> Generator[str, None, None]:
        for parsed_data in self.ai_chat_completions_stream_parsed(repo, body_params):
            # 提取 choices[0].delta.content 或类似字段
            if isinstance(parsed_data, dict):
                choices = parsed_data.get('choices', [])
                if choices and len(choices) > 0:
                    delta = choices[0].get('delta', {})
                    content = delta.get('content')
                    if content:
                        yield content
