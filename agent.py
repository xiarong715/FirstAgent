import re
import os
from llm import OpenAICompatibleClient
from tools import available_tools

# --- 1. 配置LLM客户端 ---
# 请根据您使用的服务，将这里替换成对应的凭证和地址
API_KEY = "sk-d8d18875bb554537bed80fec4df8bccc"
BASE_URL = "https://api.deepseek.com"
MODEL_ID = "deepseek-chat"
TAVILY_API_KEY = "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"
QWEATHER_API_KEY = "fbb13c559f9341b18eb494dfcb7e6f98"
os.environ['TAVILY_API_KEY'] = TAVILY_API_KEY
os.environ['QWEATHER_API_KEY'] = QWEATHER_API_KEY

# Agent 的系统提示词
AGENT_SYSTEM_PROMPT = """你是一个智能助手，可以使用以下工具来帮助用户：

可用工具：
1. get_weather(city): 查询指定城市的天气信息
2. get_attraction(city, weather): 根据城市和天气推荐合适的旅游景点

请按照以下格式进行思考和行动：
Thought: 你的思考过程
Action: 工具名称(参数1="值1", 参数2="值2")

当你完成所有任务后，使用：
Action: finish(answer="最终答案")

注意：每次只能执行一个工具，执行完成后会给你观察结果，然后再进行下一步。"""

llm = OpenAICompatibleClient(
    model=MODEL_ID,
    api_key=API_KEY,
    base_url=BASE_URL
)

# --- 2. 初始化 ---
user_prompt = "你好，请帮我查询一下今天武汉的天气，然后根据天气推荐一个合适的旅游景点。"
prompt_history = [f"用户请求: {user_prompt}"]

print(f"用户输入: {user_prompt}\n" + "="*40)

# --- 3. 运行主循环 ---
for i in range(5): # 设置最大循环次数
    print(f"--- 循环 {i+1} ---\n")
    
    # 3.1. 构建Prompt
    full_prompt = "\n".join(prompt_history)
    
    # 3.2. 调用LLM进行思考
    llm_output = llm.generate(full_prompt, system_prompt=AGENT_SYSTEM_PROMPT)
    # 模型可能会输出多余的Thought-Action，需要截断
    match = re.search(r'(Thought:.*?Action:.*?)(?=\n\s*(?:Thought:|Action:|Observation:)|\Z)', llm_output, re.DOTALL)
    if match:
        truncated = match.group(1).strip()
        if truncated != llm_output.strip():
            llm_output = truncated
            print("已截断多余的 Thought-Action 对")
    print(f"模型输出:\n{llm_output}\n")
    prompt_history.append(llm_output)
    
    # 3.3. 解析并执行行动
    action_match = re.search(r"Action: (.*)", llm_output, re.DOTALL)
    if not action_match:
        print("解析错误:模型输出中未找到 Action。")
        break
    action_str = action_match.group(1).strip()

    if action_str.startswith("finish"):
        finish_match = re.search(r'finish\(answer="(.*)"\)', action_str)
        if finish_match:
            final_answer = finish_match.group(1)
            print(f"任务完成，最终答案: {final_answer}")
        break

    tool_name_match = re.search(r"(\w+)\(", action_str)
    args_str_match = re.search(r"\((.*)\)", action_str)
    if not tool_name_match or not args_str_match:
        print("解析错误:无法解析工具名称或参数。")
        break

    tool_name = tool_name_match.group(1)
    args_str = args_str_match.group(1)
    kwargs: dict[str, str] = dict(re.findall(r'(\w+)="([^"]*)"', args_str))

    if tool_name in available_tools:
        observation = available_tools[tool_name](**kwargs)
    else:
        observation = f"错误:未定义的工具 '{tool_name}'"

    # 3.4. 记录观察结果
    observation_str = f"Observation: {observation}"
    print(f"{observation_str}\n" + "="*40)
    prompt_history.append(observation_str)
