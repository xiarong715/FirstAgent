import requests
import json
import os
import urllib3
from tavily import TavilyClient

# 禁用SSL警告
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def get_weather(city: str) -> str:
    """
    通过调用风和天气(QWeather) API查询真实的天气信息。
    """
    # 从环境变量中读取API密钥
    api_key = os.environ.get("QWEATHER_API_KEY")
    if not api_key:
        return "错误:未配置QWEATHER_API_KEY环境变量。"

    # 城市查询API端点
    location_url = "https://m44ky49pd3.re.qweatherapi.com/geo/v2/city/lookup"
    # 天气查询API端点
    weather_url = "https://m44ky49pd3.re.qweatherapi.com/v7/weather/now"

    try:
        # 1. 先查询城市ID
        location_params = {
            "location": city,
            "key": api_key
        }
        location_response = requests.get(location_url, params=location_params, timeout=10)
        location_response.raise_for_status()
        location_data = location_response.json()

        # 检查是否找到城市
        if location_data.get("code") != "200" or not location_data.get("location"):
            return f"错误:未找到城市 '{city}'"

        # 获取城市ID（使用第一个匹配的城市）
        location_id = location_data["location"][0]["id"]

        # 2. 使用城市ID查询天气
        weather_params = {
            "location": location_id,
            "key": api_key
        }
        weather_response = requests.get(weather_url, params=weather_params, timeout=10)
        weather_response.raise_for_status()
        weather_data = weather_response.json()

        # 检查天气查询是否成功
        if weather_data.get("code") != "200":
            return f"错误:天气查询失败，错误码: {weather_data.get('code')}"

        # 提取天气信息
        now = weather_data["now"]
        text = now.get("text", "")
        temp = now.get("temp", "")
        wind_dir = now.get("windDir", "")
        wind_scale = now.get("windScale", "")
        humidity = now.get("humidity", "")

        # 格式化成自然语言返回
        result = f"{city}当前天气: {text}，气温{temp}摄氏度"
        if wind_dir and wind_scale:
            result += f"，{wind_dir}风{wind_scale}级"
        if humidity:
            result += f"，湿度{humidity}%"

        return result

    except requests.exceptions.RequestException as e:
        # 处理网络错误
        return f"错误:无法连接到风和天气服务，请检查网络连接或稍后重试。详细错误: {str(e)}"
    except (KeyError, IndexError) as e:
        # 处理数据解析错误
        return f"错误:解析天气数据失败 - {e}"



def get_attraction(city: str, weather: str) -> str:
    """
    根据城市和天气，使用Tavily Search API搜索并返回优化后的景点推荐。
    """
    # 1. 从环境变量中读取API密钥
    api_key = os.environ.get("TAVILY_API_KEY")
    if not api_key:
        return "错误:未配置TAVILY_API_KEY环境变量。"

    # 2. 初始化Tavily客户端
    tavily = TavilyClient(api_key=api_key)
    
    # 3. 构造一个精确的查询
    query = f"'{city}' 在'{weather}'天气下最值得去的旅游景点推荐及理由"
    
    try:
        # 4. 调用API，include_answer=True会返回一个综合性的回答
        response = tavily.search(query=query, search_depth="basic", include_answer=True)
        
        # 5. Tavily返回的结果已经非常干净，可以直接使用
        # response['answer'] 是一个基于所有搜索结果的总结性回答
        if response.get("answer"):
            return response["answer"]
        
        # 如果没有综合性回答，则格式化原始结果
        formatted_results = []
        for result in response.get("results", []):
            formatted_results.append(f"- {result['title']}: {result['content']}")
        
        if not formatted_results:
             return "抱歉，没有找到相关的旅游景点推荐。"

        return "根据搜索，为您找到以下信息:\n" + "\n".join(formatted_results)

    except Exception as e:
        return f"错误:执行Tavily搜索时出现问题 - {e}"

# 将所有工具函数放入一个字典，方便后续调用
available_tools = {
    "get_weather": get_weather,
    "get_attraction": get_attraction,
}