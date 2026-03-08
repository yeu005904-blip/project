const spotDialogData = {
  "西安-兵马俑": {
    // 原有对话数据...
    guide: {
      openTime: "8:30-17:00（16:30停止入园，冬季16:00停止入园）",
      tip: "节假日游客多，建议早9点前入园；景区内讲解器需单独租赁（约90元/台），可拼团共享"
    }
  },
  // 其他景点数据按此格式补充...
};
const guideBtn = document.getElementById("guideBtn");
const guideModal = document.getElementById("guideModal");
const closeGuideBtn = document.getElementById("closeGuideBtn");
const guideTitle = document.getElementById("guideTitle");
const openTimeEl = document.getElementById("openTime");
const tipEl = document.getElementById("tip");

// 查看指南按钮点击事件
guideBtn.addEventListener("click", () => {
  if (!currentSpot) { // currentSpot与对话模块共用，需确保值同步
    alert("请先在左侧地图选择景点！");
    return;
  }
  // 加载当前景点的指南数据
  const guideData = spotDialogData[currentSpot].guide;
  guideTitle.textContent = `${currentSpot}实用指南`;
  openTimeEl.textContent = guideData.openTime;
  tipEl.textContent = guideData.tip;
  // 显示弹窗（移除hidden类）
  guideModal.classList.remove("hidden");
});

// 关闭弹窗事件（点击关闭按钮或遮罩层）
closeGuideBtn.addEventListener("click", () => {
  guideModal.classList.add("hidden");
});
guideModal.addEventListener("click", (e) => {
  // 点击遮罩层（modal本身）时关闭，点击内容区不关闭
  if (e.target === guideModal) {
    guideModal.classList.add("hidden");
  }
});