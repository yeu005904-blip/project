import pandas as pd
import sqlite3
import json

excel_path = "8城25景文化总表.xlsx"
df = pd.read_excel(excel_path)

conn = sqlite3.connect('scenic_spots.db')
cursor = conn.cursor()

for _, row in df.iterrows():
    dialog = json.dumps({
        "q1": row["对话话题1"],
        "a1": row["回答1"],
        "q2": row["对话话题2"],
        "a2": row["回答2"],
        "q3": row["对话话题3"],
        "a3": row["回答3"]
    }, ensure_ascii=False)
    guide = json.dumps({
        "open_time": row["开放时间"],
        "ticket_price": row.get("门票价格", "暂无信息"),
        "tip": row["避坑提醒"]
    }, ensure_ascii=False)
    cursor.execute('''
    INSERT INTO spots (city, spot_name, figure, reason, dialog, guide)
    VALUES (?, ?, ?, ?, ?, ?)
    ''', (row["城市"], row["景点"], row["历史人物"], row["关联理由"], dialog, guide))

conn.commit()
conn.close()
print("数据导入成功")