// 等待DOM加载完成
document.addEventListener('DOMContentLoaded', function() {
    // 获取生成旅忆按钮
    const generateBtn = document.getElementById('generateMemoryBtn');
    
    // 为按钮添加点击事件
    generateBtn.addEventListener('click', generateMemoryDocument);
    
    // 初始化旅忆模块状态
    initMemoryModule();
});

/**
 * 初始化旅忆模块
 */
function initMemoryModule() {
    // 检查是否有对话内容
    const hasDialogContent = checkForDialogContent();
    
    // 根据是否有对话内容更新按钮状态
    const generateBtn = document.getElementById('generateMemoryBtn');
    if (!hasDialogContent) {
        generateBtn.disabled = true;
        generateBtn.title = "请先进行对话再生成旅忆文档";
        generateBtn.style.opacity = "0.7";
        generateBtn.style.cursor = "not-allowed";
    } else {
        generateBtn.disabled = false;
        generateBtn.title = "生成旅忆文档";
        generateBtn.style.opacity = "1";
        generateBtn.style.cursor = "pointer";
    }
}

/**
 * 检查是否有对话内容
 * @returns {boolean} 是否存在对话内容
 */
function checkForDialogContent() {
    const dialogMessages = document.querySelectorAll('.dialog-messages .system-message, .dialog-messages .user-message');
    // 排除初始提示消息
    return dialogMessages.length > (document.querySelector('.initial-message') ? 1 : 0);
}

/**
 * 生成旅忆文档
 */
function generateMemoryDocument() {
    // 再次检查是否有对话内容
    if (!checkForDialogContent()) {
        showNotification('请先进行一些对话再生成旅忆文档', 'warning');
        return;
    }
    
    // 显示加载状态
    showLoadingState(true);
    
    // 模拟生成延迟，增强用户体验
    setTimeout(() => {
        // 收集文档所需信息
        const memoryData = collectMemoryData();
        
        // 生成文档HTML
        const documentHtml = createMemoryDocument(memoryData);
        
        // 创建并下载文档
        downloadMemoryDocument(documentHtml, memoryData.filename);
        
        // 隐藏加载状态
        showLoadingState(false);
        
        // 显示成功提示
        showNotification('旅忆文档生成成功！', 'success');
    }, 1500);
}

/**
 * 收集生成旅忆文档所需的数据
 * @returns {Object} 旅忆文档数据
 */
function collectMemoryData() {
    // 获取当前景点和人物信息
    const currentSpot = document.getElementById('current-spot').textContent || '未知景点';
    const currentFigure = document.getElementById('current-figure').textContent || '未知人物';
    
    // 获取当前日期作为文档一部分
    const today = new Date();
    const dateStr = `${today.getFullYear()}年${today.getMonth() + 1}月${today.getDate()}日`;
    
    // 收集对话内容
    const dialogs = [];
    const messageElements = document.querySelectorAll('.dialog-messages .system-message, .dialog-messages .user-message');
    
    messageElements.forEach(el => {
        if (!el.classList.contains('initial-message')) {
            dialogs.push({
                type: el.classList.contains('user-message') ? 'user' : 'system',
                content: el.textContent.trim(),
                speaker: el.classList.contains('user-message') ? '我' : currentFigure
            });
        }
    });
    
    return {
        spot: currentSpot,
        figure: currentFigure,
        date: dateStr,
        dialogs: dialogs,
        filename: `${currentSpot}_${currentFigure}_旅忆_${today.getFullYear()}${(today.getMonth() + 1).toString().padStart(2, '0')}${today.getDate().toString().padStart(2, '0')}`
    };
}

/**
 * 创建旅忆文档HTML内容
 * @param {Object} data - 旅忆数据
 * @returns {string} 文档HTML
 */
function createMemoryDocument(data) {
    // 构建对话HTML
    let dialogsHtml = '';
    data.dialogs.forEach(dialog => {
        dialogsHtml += `
            <div class="memory-dialog ${dialog.type}-dialog">
                <div class="dialog-speaker">${dialog.speaker}：</div>
                <div class="dialog-content">${dialog.content}</div>
            </div>
        `;
    });
    
    // 完整文档HTML
    return `
    <!DOCTYPE html>
    <html lang="zh-CN">
    <head>
        <meta charset="UTF-8">
        <title>${data.spot}旅忆</title>
        <style>
            body {
                font-family: "Microsoft YaHei", "SimSun", sans-serif;
                line-height: 1.8;
                padding: 40px;
                max-width: 800px;
                margin: 0 auto;
                color: #333;
                background-color: #f9f9f9;
            }
            .memory-header {
                text-align: center;
                margin-bottom: 40px;
                padding-bottom: 20px;
                border-bottom: 2px solid #6366f1;
            }
            .memory-title {
                color: #3b4cb8;
                margin: 0 0 10px 0;
                font-size: 2rem;
            }
            .memory-meta {
                color: #64748b;
                font-size: 0.9rem;
            }
            .memory-content {
                background-color: white;
                padding: 30px;
                border-radius: 8px;
                box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            }
            .dialog-section-title {
                color: #1e293b;
                border-bottom: 1px dashed #e2e8f0;
                padding-bottom: 10px;
                margin: 30px 0 20px 0;
            }
            .memory-dialog {
                margin-bottom: 20px;
                padding: 15px;
                border-radius: 8px;
                max-width: 90%;
            }
            .user-dialog {
                background-color: #dbeafe;
                margin-left: auto;
            }
            .system-dialog {
                background-color: #eef2ff;
                margin-right: auto;
            }
            .dialog-speaker {
                font-weight: bold;
                margin-bottom: 5px;
                color: #1e40af;
            }
            .memory-footer {
                margin-top: 40px;
                text-align: center;
                color: #64748b;
                font-size: 0.8rem;
                padding-top: 20px;
                border-top: 1px solid #e2e8f0;
            }
        </style>
    </head>
    <body>
        <div class="memory-header">
            <h1 class="memory-title">${data.spot}旅忆</h1>
            <div class="memory-meta">
                与${data.figure}的对话记录 | ${data.date}
            </div>
        </div>
        
        <div class="memory-content">
            <h2 class="dialog-section-title">对话记录</h2>
            ${dialogsHtml}
        </div>
        
        <div class="memory-footer">
            旅忆文档由历史景点对话系统自动生成
        </div>
    </body>
    </html>
    `;
}

/**
 * 下载旅忆文档
 * @param {string} html - 文档HTML内容
 * @param {string} filename - 文件名
 */
function downloadMemoryDocument(html, filename) {
    // 创建Blob对象
    const blob = new Blob(['\ufeff', html], { type: 'text/html;charset=utf-8' });
    
    // 创建下载链接
    const a = document.createElement('a');
    const url = URL.createObjectURL(blob);
    
    a.href = url;
    a.download = `${filename}.html`;
    document.body.appendChild(a);
    
    // 触发下载
    a.click();
    
    // 清理
    setTimeout(() => {
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
    }, 0);
}

/**
 * 显示或隐藏加载状态
 * @param {boolean} show - 是否显示加载状态
 */
function showLoadingState(show) {
    const generateBtn = document.getElementById('generateMemoryBtn');
    const originalContent = generateBtn.innerHTML;
    
    if (show) {
        generateBtn.disabled = true;
        generateBtn.innerHTML = '<i class="icon">⏳</i> 生成中...';
    } else {
        generateBtn.disabled = false;
        generateBtn.innerHTML = originalContent;
    }
}

/**
 * 显示通知消息
 * @param {string} message - 消息内容
 * @param {string} type - 消息类型：success, warning, error
 */
function showNotification(message, type = 'info') {
    // 检查是否已存在通知，如有则移除
    const existingNote = document.querySelector('.memory-notification');
    if (existingNote) {
        existingNote.remove();
    }
    
    // 创建通知元素
    const notification = document.createElement('div');
    notification.className = `memory-notification ${type}`;
    notification.textContent = message;
    
    // 设置样式
    notification.style.position = 'fixed';
    notification.style.bottom = '20px';
    notification.style.right = '20px';
    notification.style.padding = '12px 20px';
    notification.style.borderRadius = '4px';
    notification.style.color = 'white';
    notification.style.zIndex = '1000';
    notification.style.boxShadow = '0 4px 12px rgba(0,0,0,0.15)';
    notification.style.transition = 'all 0.3s ease';
    
    // 根据类型设置背景色
    switch(type) {
        case 'success':
            notification.style.backgroundColor = '#10b981';
            break;
        case 'warning':
            notification.style.backgroundColor = '#f59e0b';
            break;
        case 'error':
            notification.style.backgroundColor = '#ef4444';
            break;
        default:
            notification.style.backgroundColor = '#6366f1';
    }
    
    // 添加到页面
    document.body.appendChild(notification);
    
    // 3秒后自动消失
    setTimeout(() => {
        notification.style.opacity = '0';
        setTimeout(() => {
            notification.remove();
        }, 300);
    }, 3000);
}

// 导出函数供其他模块调用（如对话模块新增内容后更新状态）
window.updateMemoryModule = initMemoryModule;
