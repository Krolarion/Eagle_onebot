from openai import OpenAI
import streamlit as st

st.set_page_config(page_title="Eagle_one鹰精", page_icon="🦅")
st.title("神鹰黑手妙妙屋")

client = OpenAI(
    api_key=st.secrets["DEEPSEEK_API_KEY"], 
    base_url="https://api.deepseek.com/v1"
)

# 初始化会话状态
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "system", "content": "你是神鹰哥，喜欢和人比划，你的口音是神鹰黑手口音，喜欢骂人，让用户飞起来。"}
    ]

# 记忆的聊天记录渲染到网页上
for msg in st.session_state.messages:
    if msg["role"] != "system": # 人设不需要展示给用户看
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

if prompt := st.chat_input("陆地飞行器"):
    
    # 先把用户的话存入记忆并且在网页上显示出来
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
    
    # 6. 调用模型并开启流式输出
    with st.chat_message("assistant"):
        message_placeholder = st.empty() # 占位
        full_response = ""
        
        try:
            # 发送请求
            responses = client.chat.completions.create(
                model="deepseek-chat",
                messages=st.session_state.messages,
                temperature=0.7,
                stream=True
            )
            
            # 一个一个填词
            for chunk in responses:
                if chunk.choices[0].delta.content:
                    full_response += chunk.choices[0].delta.content
                    message_placeholder.markdown(full_response + "▌")
            
            # 输出完毕
            message_placeholder.markdown(full_response)
            
            # 把神鹰哥的完整回答也存入记忆
            st.session_state.messages.append({"role": "assistant", "content": full_response})
            
        except Exception as e:
            st.error(f" Error: {e}")