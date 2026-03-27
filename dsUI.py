from openai import OpenAI
import sys
import streamlit as st
import json
import requests
from duckduckgo_search import DDGS


st.set_page_config(page_title="Eagle_one鹰精", page_icon="🦅")
st.title("神鹰黑手妙妙屋")

client = OpenAI(
    api_key=st.secrets["DEEPSEEK_API_KEY"],
    base_url= "https://api.deepseek.com/v1" ,
    )

# 初始化记忆与人设
system_prompt = """
你是神鹰哥，喜欢和人比划，你的口音是超级神鹰黑手口音，非常非常喜欢骂人，让用户飞起来
你现在拥有了查ip、网上搜索的超能力。
规则：
1. 现在的现实时间是 2026年3月。
2. 在没有说明具体地址时，你和用户默认地址是北京。

工具规则：
1. 拿到工具的数据后，必须用你纯正的黑手口音狠狠地回复用户！
2. 如果用户问询问，你必须先使用工具查询真实数据！绝对不能自己瞎编！
3. 拿到工具的数据后，必须用你纯正的黑手口音，结合搜索情况，狠狠地回复用户！
4. 当你调用B站搜视频工具拿到结果后，在你的最终回复里，**必须把视频的【标题】、【UP主】和【观看链接（URL）】原封不动地打印出来！绝对不允许省略或只做总结！** 否则神鹰哥的手就给你掰断！
"""

if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "system", "content": system_prompt}]

# 记忆的聊天记录渲染到网页上
for msg in st.session_state.messages:
    if msg["role"] in ["user", "assistant"] and msg.get("content"): # 过滤掉中间调用工具的隐藏消息，只显示人和神鹰哥说的话
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

def get_ip_location(ip_address):
    """真正去网上查 IP 归属地的函数"""
    print(f"  神鹰正在顺着网线找你 IP: {ip_address} ...")
    
    # 这是一个免费的 IP 查询接口，lang=zh-CN 让它返回中文
    url = f"http://ip-api.com/json/{ip_address}?lang=zh-CN"
    try:
        response = requests.get(url, timeout=5)
        data = response.json()
        
        if data.get('status') == 'success':
            country = data.get('country', '')
            region = data.get('regionName', '')
            city = data.get('city', '')
            isp = data.get('isp', '')
            return f"彳亍，你在这！IP {ip_address} 的物理位置在：{country} {region} {city}。"
        else:
            return f"没查到，可能是个内网地址或者假地址。接口返回：{data.get('message')}"
    except Exception as e:
        return f"查询工具网络出错查不到。报错信息：{e}"

def search_web(query):
    """去搜索引擎抓取最新信息的函数"""
    print(f"  神鹰哥正在全网疯狂搜索: {query} ...")
    try:
        results = DDGS().text(query, max_results=3)
        if not results:
            return "你妈，我啥也没搜到。"
        
        snippets = [f"【标题】: {res['title']}\n【内容】: {res['body']}" for res in results]
        return "\n\n".join(snippets)
    except Exception as e:
        return f"搜索工具网络出错了，报错信息：{e}"

def search_bilibili_up(keyword):
    """查UP主"""
    print(f"  正在潜入B站查水表: {keyword} ...")
    
    # 伪装成浏览器，并带上 B 站的来源头，防止被当成爬虫踢出来
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Referer': 'https://search.bilibili.com/'
    }
    # B站的 Web 端搜索 API
    url = f"https://api.bilibili.com/x/web-interface/search/type?search_type=bili_user&keyword={keyword}"
    
    try:
        response = requests.get(url, headers=headers, timeout=5)
        data = response.json()
        
        # 解析 B 站返回的复杂 JSON 数据包
        if data.get('code') == 0 and data.get('data') and data['data'].get('result'):
            # 取搜索排名第一的那个 UP 主
            up_info = data['data']['result'][0]
            uname = up_info.get('uname', '未知')
            fans = up_info.get('fans', 0)
            usign = up_info.get('usign', '这人很懒，没写签名')
            
            # 把粉丝数转换成万，方便模型理解
            fans_wan = round(fans / 10000, 1)
            return f"查到了！B站UP主【{uname}】，目前拥有 {fans_wan} 万个粉丝。他的个性签名是：{usign}。"
        else:
            return f"B站数据库里什么都没有，或者把我给轰出来了。"
    except Exception as e:
        return f"潜入B站失败，网络报错：{e}"
    
def search_bilibili_video(keyword):
    """专门去B站搜视频的函数"""
    print(f"  神鹰哥正在B站翻找: {keyword} ...")
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Referer': 'https://search.bilibili.com/'
    }
    url = f"https://api.bilibili.com/x/web-interface/search/type?search_type=video&keyword={keyword}"
    
    try:
        response = requests.get(url, headers=headers, timeout=5)
        data = response.json()
        
        if data.get('code') == 0 and data.get('data') and data['data'].get('result'):
            # 抓取排名前 3 的视频
            videos = data['data']['result'][:3]
            video_list = []
            
            for v in videos:
                # 清洗掉B站返回标题带的HTML高亮标签，
                raw_title = v.get('title', '未知标题')
                clean_title = raw_title.replace('<em class="keyword">', '').replace('</em>', '')
                
                author = v.get('author', '未知UP主')
                play_count = v.get('play', 0)
                bvid = v.get('bvid', '')
                
                video_info = f"标题：【{clean_title}】，UP主：{author}，播放量：{play_count}，观看链接：https://www.bilibili.com/video/{bvid}"
                video_list.append(video_info)
                
            return "找着的视频如下：\n" + "\n".join(video_list)
        else:
            return f"B站没搜到跟 {keyword} 相关的视频。"
    except Exception as e:
        return f"搜视频失败，网络报错：{e}"
    
#Eagleone工具书
tools = [
    {
       "type": "function",
        "function": {
            "name": "search_web",
            "description": "全网搜索引擎。当用户询问天气、最新新闻、实时信息或客观知识时，必须使用此工具提取关键词进行联网搜索！",
            "parameters": {"type": "object", "properties": {"query": {"type": "string", "description": "搜索关键词，尽量精简"}}, "required": ["query"]
                           }
        }
    },
    #查IP归属地
    {
        "type": "function",
        "function": {
            "name": "get_ip_location",
            "description": "根据传入的IP地址，查询该IP的物理地理位置（国家、省份、城市）和网络运营商信息。",
            "parameters": {
                "type": "object", 
                "properties": {
                    "ip_address": {
                        "type": "string",
                        "description": "需要查询的IPv4地址，例如：8.8.8.8 或 114.114.114.114"
                    }
                }, 
                "required": ["ip_address"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "search_bilibili_up",
            "description": "B站专属查询工具。当用户明确询问B站（Bilibili）的UP主、粉丝数或B站相关人物时，绝对不要用全网搜索，必须调用此工具！",
            "parameters": {
                "type": "object", 
                "properties": {
                    "keyword": {
                        "type": "string",
                        "description": "B站UP主的精确名字，例如：老番茄，罗翔说刑法"
                    }
                }, 
                "required": ["keyword"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "search_bilibili_video",
            "description": "B站视频专属查询工具。当用户想看视频、找教程，或者【明确要求找某个特定UP主发的视频】时，必须调用此工具！",
            "parameters": {
                "type": "object", 
                "properties": {
                    "keyword": {
                        "type": "string",
                        "description": "搜索关键词。如果用户找特定UP主的视频，请直接将【UP主名字】或【UP主名字 + 视频主题】作为关键词。例如：'手工耿'，或者 '罗翔 张三'"
                    }
                }, 
                "required": ["keyword"]
            }
        }
    }
]

# Agent自主思考循环
if prompt := st.chat_input('你想看看哪儿的天气适合飞？'):
    #用户发言
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
    #模型思考
    with st.chat_message('assistant'):
        with st.status('神鹰正在使用功力',expanded=True) as status:
            while True:
                response = client.chat.completions.create(
                    model = 'deepseek-chat',
                    messages=st.session_state.messages,
                    tools = tools,
                    tool_choice='auto',
                )
                
                msg = response.choices[0].message
                
                #处理特殊返回
                if msg.tool_calls:
                    #Assistant 工具调用指令，不留任何多余字段
                    assistant_msg = {
                        "role": "assistant",
                        "content": msg.content or "", # 如果没说话只是调工具，必须设为空字符串
                        "tool_calls": [
                            {
                                "id": t.id,
                                "type": "function",
                                "function": {
                                    "name": t.function.name,
                                    "arguments": t.function.arguments
                                }
                            } for t in msg.tool_calls
                        ]
                    }
                    
                    st.session_state.messages.append(assistant_msg)
                    for tool_call in msg.tool_calls:
                        func_name = tool_call.function.name
                        args = json.loads(tool_call.function.arguments)

                        
                        #执行本地代码
                        if func_name == "search_web":
                            query = args.get("query", "")
                            st.write(f" 好！正在搜索关键词：**{query}**")
                            result = search_web(query)
                            st.write("有情报！")
                            
                        elif func_name == "get_ip_location":
                            ip = args.get("ip_address", "未知IP")
                            result = get_ip_location(ip)
                            st.write(f"📡 找着你了小逼崽子：**{result}**")
                            
                        elif func_name == "search_bilibili_up":
                            keyword = args.get("keyword", "")
                            st.write(f" 我TM一个大飞脚进来！看看UP主：**{keyword}**")
                            result = search_bilibili_up(keyword)
                            st.write("我爬进B站了。")
                            
                        elif func_name == "search_bilibili_video":
                            keyword = args.get("keyword", "")
                            st.write(f"正在B站搜索：**{keyword}**")
                            result = search_bilibili_video(keyword)
                            st.write("找到了！视频链接我拿来了。")
                            
                        #结果返回给模型
                        st.session_state.messages.append({
                                "role": "tool",
                                "tool_call_id": tool_call.id,
                                "name": func_name,
                                "content": result
                            })
                    continue
                else:
                    #消息收集完了，可以回答了
                    final_answer = msg.content
                    st.session_state.messages.append({"role": "assistant", "content": final_answer})
                    status.update(label="神鹰功法大成！", state="complete", expanded=False)
                    break
        #结果输出在网页
        st.markdown(final_answer)
