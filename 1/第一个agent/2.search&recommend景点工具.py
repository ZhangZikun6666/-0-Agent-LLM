import os
from email import message
import re
import requests
from urllib import response
import tavily
from openai.lib.azure import API_KEY_SENTINEL
from openai.resources.chat.completions import messages
from pydantic_core.core_schema import arguments_schema
from tavily import TavilyClient
from openai import OpenAI

def get_weather(city:str) ->str:
    """
    通过调用 wttr.in API 查询真实的天气信息。
    :param city:
    :return:
    """
    #API端点 请求json格式的数据
    url=f"https://wttr.in/{city}?format=j1"

    try:
        #发起网络请求
        response = requests.get(url)
        #检查响应码是否为200(成功)
        response.raise_for_status()
        #解析返回的json数据 将json数据转换为字典
        data = response.json()

        #提取当前天气
        current_condition = data['current_condition'][0]
        """
         先取出列表 再取出列表里面的第一个字典
        """
        weather_desc = current_condition['weatherDesc'][0]['value']
        temp_c = current_condition['temp_C']
        area = data["nearest_area"][0]

        print("地点：", area["areaName"][0]["value"])
        print("地区：", area["region"][0]["value"])
        print("国家：", area["country"][0]["value"])
        #格式化成自然语言并返回
        return f"{city}当前天气:{weather_desc},气温:{temp_c}摄氏度"
    except requests.exceptions.RequestException as e:
        return f"错误 遇到网络问题 -{e}"
    except (KeyError,IndexError) as e:
        #处理数据解析错误
        return f"解析天气格式错误 可能是城市不存在 -{e}"

def get_attraction(city:str,weather:str)-> str:
    """
    根据城市和天气 使用Tavily Search API搜索并返回优化后的景点推荐。
    :param city:
    :param weather:
    :return:
    """
    #1.从环境变量读取API密钥
    api_key = os.environ.get("TAVILY_API_KEY")
    if not api_key:
        return "错误 未配置环境变量"

    #1.2.初始化客户端
    tavily=TavilyClient(api_key=api_key)

    #3.构造一个精确查询
    query = f"'{city}'在'{weather}'天气下最值得去的旅游景点以及理由"

    try:
        #4.调用API include_answer=True会返回一个综合性的回答
        response = tavily.search(query=query,search_depth='basic',include_answer=True)

        #5.tavily返回的结果可以直接使用
        if response.get("answer"):
            return response["answer"]

        #如果没有任何综合性回答则格式化原始结果
        formatted_results = []
        for result in response.get("results",[]):
            formatted_results.append(f"-{result['title']}:{result['content']}")
        if not formatted_results:
            return "抱歉 暂未查询到相关结果"

        return "根据搜索,为您查询到如下信息:\n"+"\n".join(formatted_results)
    except Exception as e:
        return f"错误:执行Tavily搜索时出现错误-{e}"

# 将所有工具函数放入一个字典，方便后续调用
available_tools = {
    "get_weather": get_weather,
    "get_attraction": get_attraction,
}

class OpenAICompatibleClient:
    """
    一个用于调用任何兼容OpenAI接口的LLM服务的客户端。
    """
    def __init__(self,model:str,api_key:str,base_url:str):
        self.model=model
        self.client=OpenAI(api_key=api_key,base_url=base_url)
    def generate(self,prompt:str,system_prompt:str) ->str:
        """调用LLM生成回应"""
        print("正在调用大预言模型")
        try:
            messages=[
                {'role':'system','content':system_prompt},
                {'role':'user','content':prompt}
            ]
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                stream=False
            )
            answer = response.choices[0].message.content
            print("大预言模型调用成功")
            return answer
        except Exception as e:
            print(f"调用大模型API时发生错误:{e}")
            return "错误：调用语言模型时错误"

#1. 配置LLM客户端
API_KEY="sk-53c7a2f264a847438b09050ab5f213d6"
BASE_URL="https://api.deepseek.com"
MODEL_ID="deepseek-flash"
os.environ['TAVILY_API_KEY']="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"


llm=OpenAICompatibleClient(model=MODEL_ID,api_key=API_KEY,base_url=BASE_URL)
#1.2.初始化
user_prompt = "你好，帮我查询一下Osaka的天气，然后根据天气推荐一个适合的旅游景点"
AGENT_SYSTEM_PROMPT = """你是一个智能助手，负责回答用户的问题。请用中文回答，保持简洁友好。
每次回复必须包含 Thought: 和 Action: 两行，Action: 后只能是以下格式之一：
get_weather(city="城市名")
get_attraction(city="城市名", weather="天气描述")
Finish[最终回答]
例如：
Thought: 先查询南京天气
Action: get_weather(city="南京")
收到 Observation 后，再决定下一步。"""
prompt_history = [f"用户请求:{user_prompt}"]

print(f"用户输入:{user_prompt}\n"+"="*40)#输出40个等号用作分隔符

#---3.运行主循环---
for i in range(5): #设置最大循环次数
    print(f"---循环{i+1}次---\n")

    #3.1构建prompt
    full_prompt="\n".join(prompt_history) #用换行符把数组里面的字符串拼接起来

    #3.2调用LLM
    llm_output=llm.generate(full_prompt,system_prompt=AGENT_SYSTEM_PROMPT)
    #模型可能会输出多余的Thought-Action需要截断 使用正则表达式
    match = re.search(r'(Thought:.*?Action:.*?)(?=\n\s*(?:Thought:|Action:|Observation:)|\Z)',llm_output,re.DOTALL)
    if match:
        truncated = match.group(1).strip()
        if truncated != llm_output.strip():
            llm_output=truncated
            print("已截断多余的Thought-Action对")
        print(f"模型输出:\n{llm_output}\n")
        prompt_history.append(llm_output)

    action_match = re.search(r"Action:(.*)",llm_output,re.DOTALL)
    if not action_match:
        observation = "错误 未能找到Action字段 请确保你的回复严格遵循 'Thought: ... Action: ...' 的格式。"
        observation_str = f"Observation:{observation}"
        print(f"{observation_str}\n"+"="*40)
        prompt_history.append(observation_str)
        continue
    action_str=action_match.group(1).strip()

    finish_match = re.fullmatch(r"Finish\[(.*)\]", action_str, re.DOTALL)
    if finish_match:
        final_answer = finish_match.group(1)
        print(f"任务完成 最终答案:{final_answer}")
        break
    tool_match = re.fullmatch(r"(\w+)\((.*)\)", action_str, re.DOTALL)
    if not tool_match:
        observation_str = "Observation:错误 Action 格式不正确，请使用 工具名(参数名=\"值\") 或 Finish[最终回答]。"
        print(f"{observation_str}\n"+"="*40)
        prompt_history.append(observation_str)
        continue
    tool_name, args_str = tool_match.groups()
    kwargs = dict(re.findall(r'(\w+)="([^"]*)"', args_str))

    if tool_name in available_tools:
        observation = available_tools[tool_name](**kwargs)
    else:
        observation = f"错误:未定义的工具'{tool_name}'"
    #3.4记录观察结果
    observation_str = f"Observation:{observation}"
    print(f"{observation_str}\n"+"="*40)
    prompt_history.append(observation_str)







