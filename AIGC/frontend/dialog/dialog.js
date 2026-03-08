// 硬编码数据（后续替换为后端接口返回数据）
const spotDialogData = {
  "西安-兵马俑": {
    topics: [
      { id: 1, question: "兵马俑怎么建造的？", answer: "兵马俑由陶土烧制，采用模塑结合、分段制作，再彩绘，耗时约39年，动用数十万工匠。" },
      { id: 2, question: "兵马俑有多少个？", answer: "已发掘兵马俑约8000件，包括士兵、战马、战车，阵型完整，模拟秦军作战编制。" },
      { id: 3, question: "兵马俑为何被称为‘世界第八大奇迹’？", answer: "因规模宏大、工艺精湛，真实还原秦代军事文化，1987年被列入世界文化遗产，获此称号。" }
    ],
    // 自定义提问的关键词匹配（简化逻辑，避免AI模型，降低难度）
    customAnswers: [
      { keywords: ["建造时间", "耗时"], answer: "兵马俑始建于公元前246年，至秦始皇去世（前210年）完工，耗时约39年。" },
      { keywords: ["材质", "材料"], answer: "兵马俑主要由细腻陶土烧制，表面原涂有彩绘，但出土后因环境变化多数脱落。" }
    ]
  },
  // 其他景点数据按此格式补充...
};


// 获取当前选中的景点（需与任务3的地图模块联动，接收景点名称，如“西安-兵马俑”）
let currentSpot = ""; // 初始为空，后续由地图模块传递值

// 预设话题按钮点击事件
const topicBtns = document.querySelectorAll(".topic-btn");
topicBtns.forEach(btn => {
  btn.addEventListener("click", () => {
    if (!currentSpot) {
      alert("请先在左侧地图选择景点！");
      return;
    }
    // 获取话题ID，匹配对应回答
    const topicId = parseInt(btn.dataset.topic);
    const topic = spotDialogData[currentSpot].topics.find(t => t.id === topicId);
    // 插入对话区（调用工具函数addDialog，见common/utils.js）
    addDialog("user", topic.question); // 用户提问
    addDialog("system", topic.answer); // 系统回答
  });
});


const questionInput = document.getElementById("questionInput");
const sendBtn = document.getElementById("sendBtn");

// 发送按钮点击事件
sendBtn.addEventListener("click", handleCustomQuestion);
// 输入框回车触发发送
questionInput.addEventListener("keydown", (e) => {
  if (e.key === "Enter") handleCustomQuestion();
});

// 自定义提问处理函数
function handleCustomQuestion() {
  const question = questionInput.value.trim();
  if (!question) {
    alert("请输入你的问题！");
    return;
  }
  if (!currentSpot) {
    alert("请先在左侧地图选择景点！");
    return;
  }
  // 清空输入框
  questionInput.value = "";
  // 插入用户提问到对话区
  addDialog("user", question);
  // 关键词匹配回答
  const customAnswers = spotDialogData[currentSpot].customAnswers;
  let answer = "抱歉，我暂时无法回答这个问题，你可以尝试其他提问~";
  for (const item of customAnswers) {
    // 只要问题包含任一关键词，就返回对应回答
    if (item.keywords.some(keyword => question.includes(keyword))) {
      answer = item.answer;
      break;
    }
  }
  // 模拟“思考”延迟（提升用户体验），1秒后插入系统回答
  setTimeout(() => {
    addDialog("system", answer);
  }, 1000);
}


// 添加对话到内容区
function addDialog(role, content) {
  const dialogContent = document.getElementById("dialogContent");
  const dialogItem = document.createElement("div");
  // 按角色添加样式类
  dialogItem.className = `dialog-item ${role === "user" ? "user-dialog" : "system-dialog"}`;
  // 设置对话内容（避免XSS风险，用textContent而非innerHTML）
  dialogItem.textContent = content;
  // 插入对话区，并滚动到底部（显示最新内容）
  dialogContent.appendChild(dialogItem);
  dialogContent.scrollTop = dialogContent.scrollHeight;
}