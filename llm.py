from openai import OpenAI
from openai.types.chat import ChatCompletion, ChatCompletionMessageParam

class OpenAICompatibleClient:
    """
    一个用于调用任何兼容OpenAI接口的LLM服务的客户端。
    """
    def __init__(self, model: str, api_key: str, base_url: str) -> None:
        self.model: str = model
        self.client: OpenAI = OpenAI(api_key=api_key, base_url=base_url)

    def generate(self, prompt: str, system_prompt: str) -> str:
        """调用LLM API来生成回应。"""
        print("正在调用大语言模型...")
        try:
            messages: list[ChatCompletionMessageParam] = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ]
            response: ChatCompletion = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                stream=False
            )
            answer: str = response.choices[0].message.content or ""
            print("大语言模型响应成功。")
            return answer
        except Exception as e:
            print(f"调用LLM API时发生错误: {e}")
            return "错误:调用语言模型服务时出错。"
