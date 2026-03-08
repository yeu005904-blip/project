
import urllib.request
import urllib.parse
import json

def get_deepseek_response(question, max_tokens=50):
    """
    使用urllib调用DeepSeek API获取回答
    """
    API_KEY = "sk-1b34874712f4465daba7a9bfcc2b1f6d"
    
    if API_KEY == "你的DeepSeek_API_KEY":
        return {
            "status": "error",
            "answer": "请先配置DeepSeek API密钥"
        }
    
    # DeepSeek API地址
    url = "https://api.deepseek.com/v1/chat/completions"

    data = {
        "model": "deepseek-chat",
        "messages": [
            {
                "role": "system",
                "content": "You are a professional Chinese history and culture assistant. Answer questions about Chinese historical figures and scenic spots concisely and accurately, within 50 characters."
            },
            {
                "role": "user",
                "content": question
            }
        ],
        "max_tokens": max_tokens,
        "temperature": 0.7,
        "stream": False
    }
    
    try:
        # 构建请求
        json_data = json.dumps(data, ensure_ascii=False).encode('utf-8')
        
        req = urllib.request.Request(
            url,
            data=json_data,
            headers={
                'Content-Type': 'application/json; charset=utf-8',
                'Authorization': f'Bearer {API_KEY}'
            }
        )

        with urllib.request.urlopen(req, timeout=30) as response:
            result = json.loads(response.read().decode('utf-8'))
            
            if "choices" in result and len(result["choices"]) > 0:
                answer = result["choices"][0]["message"]["content"]
                return {
                    "status": "success",
                    "answer": answer
                }
            else:
                return {
                    "status": "error",
                    "answer": "API返回格式异常"
                }
                
    except Exception as e:
        return {
            "status": "error",
            "answer": f"请求异常: {str(e)}"
        }


# 预设话题问答库
PRESET_QUESTIONS = {
    "兵马俑怎么建造的？": "兵马俑采用陶土烧制工艺，先用泥条盘筑法制作陶俑胎体，然后雕刻细节，最后入窑烧制。每个陶俑都是手工制作，工艺精湛，体现了秦代高超的制陶技术。",
    "兵马俑有多少个？": "兵马俑坑内已发现陶俑、陶马约8000件，其中兵马俑约6000件。这些陶俑按军阵排列，包括步兵、骑兵、车兵等不同兵种，规模宏大。",
    "兵马俑为什么没有重复的？": "兵马俑虽然数量众多，但每个陶俑的面部表情、发型、服饰都各不相同，体现了秦代工匠的精湛技艺和对细节的追求。"
}


def get_preset_answer(question):
    """获取预设问题的答案"""
    return PRESET_QUESTIONS.get(question, "抱歉，这个问题暂未收录。")

