import os
from tkinter.scrolledtext import example

from openai import OpenAI
from dotenv import load_dotenv
from typing import List,Dict

#加载.env中的环境变量
load_dotenv()

class HelloAgentsLLM:
    """
    适用于所有兼容openai接口的服务 默认使用流式响应
    """
    def __init__(self,model:str = None, apikey: str = None,baseurl: str = None,timeout: int =None):
        """
        初始化LLM客户端 优先使用传入参数 未传入从.env文件加载
        """
        self.model = model or os.getenv("LLM_MODEL_ID")
        self.apikey = apikey or os.getenv("LLM_API_KEY")
        self.baseurl = baseurl or os.getenv("llm_base_url")
        self.timeout = timeout or int(os.getenv("LLM_TIMEOUT",30))

        if not all([self.model,self.apikey,self.timeout]):
            raise ValueError

        self.client = OpenAI(api_key=self.apikey,base_url=self.baseurl,timeout=self.timeout)

    def think(self,messages: List[Dict[str,str]] ,temperature:float =0 ) ->str :
        print(f"正在调用模型:{self.model}")
        try:
            response = self.client.chat.completions.create(
                model = self.model,
                messages = messages,
                temperature= temperature,
                stream= True,
            )

            #处理流式相应
            print("大语言模型响应成功:")
            collected_content=[]
            for chunk in response:
                if not chunk.choices:
                    continue
                content = chunk.choices[0].delta.content or ""
                print(content, end="", flush= True)
                collected_content.append(content)
            print()
            return "".join(collected_content)

        except Exception as e:
            print("大模型调用API时发生错误")
            return None
#客户端使用示例
if __name__ == '__main__':
    try:
        llmClient = HelloAgentsLLM()

        exampleMessages = [
            {"role":"system","content":"You are a helpful assistant that writes Python code"},
            {"role":"user","content":"帮我写一个冒泡排序算法和快速排序算法"}
        ]

        print("调用LLM")
        responseText = llmClient.think(exampleMessages)
        if responseText:
            print("\n\n--- 完整模型响应")
            print(responseText)

    except ValueError as e:
        print(e)