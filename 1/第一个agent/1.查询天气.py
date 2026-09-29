from locale import currency
from urllib import response

import requests

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
print(get_weather(''))
