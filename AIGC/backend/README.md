
### 1. 安装依赖
```bash
pip install -r requirement.txt
```

### 2. 初始化数据库
```bash
python init_db.py
python excel_to_sqlite.py
```

### 3. 启动服务
```bash
python app.py
```

服务将在 http://127.0.0.1:5000 启动


### 基础接口
- `GET /api/health` - 健康检查
- `GET /` - 服务信息和接口列表

### 景点数据接口
- `GET /api/get_spot_list?city=城市名` - 获取指定城市的景点列表
- `GET /api/get_spot_detail?spot_name=景点名` - 获取景点详细信息
- `GET /api/get_historical_figures` - 获取所有历史人物列表
- `GET /api/get_figure_info?figure_name=人物名` - 获取历史人物详细信息

### 对话功能接口
- `POST /api/preset_question` - 预设话题问答
- `POST /api/custom_question` - 自定义文字提问

### 实用指南接口
- `GET /api/get_practical_guide?spot_name=景点名` - 获取景点实用指南

### 旅忆功能接口
- `POST /api/generate_travel_memory` - 生成旅忆文档
- `POST /api/save_travel_memory` - 保存旅忆文档到文件


### DeepSeek API配置
在 `deepseek_urllib.py` 中配置API密钥：
```python
API_KEY = "你的DeepSeek_API_KEY"
```

## 响应格式

所有API接口都使用统一的响应格式：
```json
{
  "code": 200,
  "status": "success",
  "msg": "操作成功",
  "data": {
    // 具体数据内容
  }
}
```


