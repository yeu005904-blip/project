from flask import Flask, jsonify, request, Response, render_template_string, send_from_directory
import sqlite3
import json
import os
from flask_cors import CORS
from deepseek_urllib import get_deepseek_response as get_spark_response, get_preset_answer

app = Flask(__name__)
# 配置CORS，允许前端跨域访问
CORS(app, resources={
    r"/*": {
        "origins": "*",
        "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization", "Accept"]
    }
})

app.config['JSON_AS_ASCII'] = False
app.config['JSONIFY_PRETTYPRINT_REGULAR'] = True

# 统一响应格式
def make_response(code, data=None, msg="", status="success"):
    """统一的API响应格式"""
    response = {
        "code": code,
        "status": status,
        "msg": msg
    }
    if data is not None:
        response["data"] = data
    return jsonify(response)

# 数据验证函数
def validate_city(city):
    """验证城市名"""
    if not city or len(city.strip()) == 0:
        return False
    return True

def validate_spot_name(spot_name):
    """验证景点名"""
    if not spot_name or len(spot_name.strip()) == 0:
        return False
    return True

def validate_figure_name(figure_name):
    """验证历史人物姓名"""
    if not figure_name or len(figure_name.strip()) == 0:
        return False
    return True

@app.route('/api/health', methods=['GET'])
def health_check():
    """健康检查接口"""
    return make_response(200, {"status": "healthy"}, "后端服务正常运行")


@app.route('/api/get_spot_list', methods=['GET'])
def get_spot_list():
    # 兼容前端可能使用的不同参数名
    city = request.args.get('city') or request.args.get('cityName')
    if not validate_city(city):
        return make_response(400, None, "请传入有效的城市名", "error")

    try:
        conn = sqlite3.connect('scenic_spots.db')
        cursor = conn.cursor()
        cursor.execute('SELECT spot_name FROM spots WHERE city =?', (city,))
        spots = [row[0] for row in cursor.fetchall()]
        conn.close()
        
        return make_response(200, spots, "获取景点列表成功")
    except Exception as e:
        return make_response(500, None, f"数据库查询失败: {str(e)}", "error")


@app.route('/api/get_spot_detail', methods=['GET'])
def get_spot_detail():
    # 兼容前端可能使用的不同参数名
    spot_name = request.args.get('spot_name') or request.args.get('spotName')
    if not validate_spot_name(spot_name):
        return make_response(400, None, "请传入有效的景点名", "error")

    try:
        conn = sqlite3.connect('scenic_spots.db')
        cursor = conn.cursor()
        cursor.execute('''
            SELECT city, figure, reason, dialog, guide 
            FROM spots 
            WHERE spot_name =?
        ''', (spot_name,))
        result = cursor.fetchone()
        conn.close()

        if not result:
            return make_response(404, None, "该景点不存在", "error")

        dialog = json.loads(result[3]) if result[3] else {}
        guide = json.loads(result[4]) if result[4] else {}

        # 确保dialog包含前端需要的q1, a1, q2, a2, q3, a3字段
        if not dialog.get('q1'):
            dialog['q1'] = f"关于{spot_name}的历史背景是什么？"
        if not dialog.get('a1'):
            dialog['a1'] = f"{spot_name}有着深厚的历史文化底蕴，承载着丰富的历史故事。"
        if not dialog.get('q2'):
            dialog['q2'] = f"{spot_name}有什么特色？"
        if not dialog.get('a2'):
            dialog['a2'] = f"{spot_name}以其独特的文化特色和建筑风格而闻名。"
        if not dialog.get('q3'):
            dialog['q3'] = f"参观{spot_name}需要注意什么？"
        if not dialog.get('a3'):
            dialog['a3'] = f"参观{spot_name}时请保持安静，尊重历史文化。"

        spot_data = {
            "name": spot_name,
            "city": result[0],
            "figure": result[1],
            "person": result[1],
            "reason": result[2],
            "dialog": dialog,
            "guide": guide,
            # 添加前端需要的字段
            "spotImg": f"https://picsum.photos/400/300?random={hash(spot_name) % 1000}",  # 随机图片
            "guideImg": f"https://picsum.photos/200/200?random={hash(result[1]) % 1000}",  # 随机图片
            "initialMessage": f"你好！我是{result[1]}，很高兴为你介绍{spot_name}的历史文化。"
        }
        
        return make_response(200, spot_data, "获取景点详情成功")
        
    except Exception as e:
        return make_response(500, None, f"数据库查询失败: {str(e)}", "error")


@app.route('/api/get_historical_figures', methods=['GET'])
def get_historical_figures():
    """获取所有历史人物列表"""
    try:
        conn = sqlite3.connect('scenic_spots.db')
        cursor = conn.cursor()
        cursor.execute('SELECT DISTINCT figure, spot_name FROM spots WHERE figure IS NOT NULL AND figure != ""')
        figures = [{"figure": row[0], "spot_name": row[1]} for row in cursor.fetchall()]
        conn.close()
        
        return make_response(200, figures, "获取历史人物列表成功")
    except Exception as e:
        return make_response(500, None, f"数据库查询失败: {str(e)}", "error")


@app.route('/api/get_figure_info', methods=['GET'])
def get_figure_info():
    """获取指定历史人物的详细信息"""
    figure_name = request.args.get('figure_name')
    if not validate_figure_name(figure_name):
        return make_response(400, None, "请传入有效的历史人物姓名", "error")
    
    try:
        conn = sqlite3.connect('scenic_spots.db')
        cursor = conn.cursor()
        cursor.execute('''
            SELECT spot_name, reason, dialog, guide 
            FROM spots 
            WHERE figure = ?
        ''', (figure_name,))
        result = cursor.fetchone()
        conn.close()
        
        if not result:
            return make_response(404, None, "该历史人物不存在", "error")
        
        dialog = json.loads(result[2]) if result[2] else []
        guide = json.loads(result[3]) if result[3] else []
        
        figure_data = {
            "figure_name": figure_name,
            "spot_name": result[0],
            "reason": result[1],
            "dialog": dialog,
            "guide": guide
        }
        
        return make_response(200, figure_data, "获取历史人物信息成功")
        
    except Exception as e:
        return make_response(500, None, f"数据库查询失败: {str(e)}", "error")


@app.route('/api/preset_question', methods=['POST'])
def preset_question():
    try:
        data = request.get_json()
        if not data:
            return make_response(400, None, "请求体不能为空", "error")
            
        question = data.get('question')
        figure_name = data.get('figure_name')
        
        if not question or not figure_name:
            return make_response(400, None, "请传入问题和历史人物姓名", "error")

        answer = get_preset_answer(question)
        
        response_data = {
            "question": question,
            "answer": answer,
            "figure_name": figure_name
        }
        
        return make_response(200, response_data, "预设问题回答成功")
        
    except Exception as e:
        return make_response(500, None, f"处理预设问题失败: {str(e)}", "error")



@app.route('/api/custom_question', methods=['POST'])
def custom_question():
    """自定义文字提问接口"""
    try:
        data = request.get_json()
        if not data:
            return make_response(400, None, "请求体不能为空", "error")
            
        question = data.get('question')
        figure_name = data.get('figure_name')
        
        if not question or not figure_name:
            return make_response(400, None, "请传入问题和历史人物姓名", "error")

        enhanced_question = f"请回答关于历史人物{figure_name}和相关文化景点的问题：{question}。请将回答控制在50字以内。"
        
        # 调用DeepSeek API
        result = get_spark_response(enhanced_question, max_tokens=50)
        
        if result["status"] == "success":
            answer = result["answer"]
        else:
            answer = f"抱歉，暂时无法回答这个问题。{result['answer']}"
        
        response_data = {
            "question": question,
            "answer": answer,
            "figure_name": figure_name
        }
        
        return make_response(200, response_data, "自定义问题回答成功")
        
    except Exception as e:
        return make_response(500, None, f"处理自定义问题失败: {str(e)}", "error")


@app.route('/api/get_practical_guide', methods=['GET'])
def get_practical_guide():
    """获取实用指南信息"""
    spot_name = request.args.get('spot_name')
    if not validate_spot_name(spot_name):
        return make_response(400, None, "请传入有效的景点名", "error")
    
    try:
        conn = sqlite3.connect('scenic_spots.db')
        cursor = conn.cursor()
        cursor.execute('''
            SELECT guide, spot_name 
            FROM spots 
            WHERE spot_name = ?
        ''', (spot_name,))
        result = cursor.fetchone()
        conn.close()
        
        if not result:
            return make_response(404, None, "该景点不存在", "error")
        
        guide_data = json.loads(result[0]) if result[0] else {}
        
        response_data = {
            "spot_name": result[1],
            "basic_info": {
                "open_time": guide_data.get("open_time", "暂无信息"),
                "ticket_price": guide_data.get("ticket_price", "暂无信息")
            },
            "tips": guide_data.get("tip", "暂无提醒")
        }
        
        return make_response(200, response_data, "获取实用指南成功")
        
    except Exception as e:
        return make_response(500, None, f"数据库查询失败: {str(e)}", "error")


@app.route('/api/generate_travel_memory', methods=['POST'])
def generate_travel_memory():
    """生成旅忆文档"""
    try:
        data = request.get_json()
        if not data:
            return make_response(400, None, "请求体不能为空", "error")
            
        spot_name = data.get('spot_name')
        figure_name = data.get('figure_name')
        conversation_history = data.get('conversation_history', [])
        
        if not spot_name or not figure_name:
            return make_response(400, None, "请传入景点名和历史人物姓名", "error")

        conn = sqlite3.connect('scenic_spots.db')
        cursor = conn.cursor()

        cursor.execute('''
            SELECT reason, guide 
            FROM spots 
            WHERE spot_name = ? AND figure = ?
        ''', (spot_name, figure_name))
        result = cursor.fetchone()

        if not result:
            cursor.execute('''
                SELECT reason, guide 
                FROM spots 
                WHERE spot_name = ?
            ''', (spot_name,))
            result = cursor.fetchone()
        
        conn.close()
        
        if not result:
            return make_response(404, None, "该景点不存在", "error")
        
        reason = result[0]
        guide_data = json.loads(result[1]) if result[1] else {}

        memory_content = f"""=== {spot_name} 旅忆文档 ===

【景点信息】
景点名称：{spot_name}
关联历史人物：{figure_name}
关联理由：{reason}

【对话记录】
"""

        for i, conv in enumerate(conversation_history, 1):
            memory_content += f"{i}. 问题：{conv.get('question', '')}\n"
            memory_content += f"   回答：{conv.get('answer', '')}\n\n"

        memory_content += f"""【实用指南】
开放时间：{guide_data.get('open_time', '暂无信息')}
门票价格：{guide_data.get('ticket_price', '暂无信息')}
避坑提醒：{guide_data.get('tip', '暂无提醒')}

【生成时间】
{__import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
        
        response_data = {
            "spot_name": spot_name,
            "figure_name": figure_name,
            "memory_content": memory_content,
            "filename": f"{spot_name}_{figure_name}_旅忆.txt"
        }
        
        return make_response(200, response_data, "旅忆文档生成成功")
        
    except Exception as e:
        return make_response(500, None, f"生成旅忆文档失败: {str(e)}", "error")


@app.route('/api/save_travel_memory', methods=['POST'])
def save_travel_memory():
    """保存旅忆文档到文件"""
    try:
        data = request.get_json()
        if not data:
            return make_response(400, None, "请求体不能为空", "error")
            
        memory_content = data.get('memory_content')
        filename = data.get('filename')
        
        if not memory_content or not filename:
            return make_response(400, None, "请传入文档内容和文件名", "error")
        
        safe_filename = "".join(c for c in filename if c.isalnum() or c in (' ', '-', '_', '.')).rstrip()
        if not safe_filename.endswith('.txt'):
            safe_filename += '.txt'

        file_path = os.path.join('memories', safe_filename)
        os.makedirs('memories', exist_ok=True)
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(memory_content)
        
        response_data = {
            "filename": safe_filename,
            "file_path": file_path,
            "message": "旅忆文档保存成功"
        }
        
        return make_response(200, response_data, "旅忆文档保存成功")
        
    except Exception as e:
        return make_response(500, None, f"保存文件失败: {str(e)}", "error")


# 根路径接口
@app.route('/', methods=['GET'])
def root():
    """根路径接口"""
    endpoints_info = {
        "service": "历史文化景点对话系统后端服务",
        "version": "1.0.0",
        "endpoints": [
            "/api/health - 健康检查",
            "/api/get_spot_list - 获取景点列表", 
            "/api/get_spot_detail - 获取景点详情",
            "/api/preset_question - 预设话题问答",
            "/api/custom_question - 自定义文字提问",
            "/api/get_practical_guide - 获取实用指南",
            "/api/generate_travel_memory - 生成旅忆文档",
            "/api/save_travel_memory - 保存旅忆文档"
        ]
    }
    return make_response(200, endpoints_info, "服务运行正常")



if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)