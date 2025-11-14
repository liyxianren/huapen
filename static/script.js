// 全局变量
let chart;
let sensorData = [];
let previousData = {};
let currentQuery = null; // 当前查询状态
let isLogPaused = false; // 日志暂停状态
let maxLogEntries = 100; // 最大日志条数

// 初始化
document.addEventListener('DOMContentLoaded', function() {
    initializeChart();
    initializeLog(); // 初始化日志系统
    loadData(); // 初始加载一次数据
    // 移除自动轮询，改为手动点击按钮更新

    // 刷新按钮事件
    document.getElementById('refreshBtn').addEventListener('click', loadData);

    // 查询按钮事件
    document.getElementById('queryByDateBtn').addEventListener('click', queryByDate);
    document.getElementById('queryByHourBtn').addEventListener('click', queryByHour);
    document.getElementById('resetQueryBtn').addEventListener('click', resetQuery);

    // 日志控制按钮事件
    document.getElementById('clearLogBtn').addEventListener('click', clearLog);
    document.getElementById('toggleLogBtn').addEventListener('click', toggleLog);
});

// 初始化图表
function initializeChart() {
    const ctx = document.getElementById('sensorChart').getContext('2d');
    chart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: [],
            datasets: [
                {
                    label: '湿度 (%)',
                    data: [],
                    borderColor: '#3498db',
                    backgroundColor: 'rgba(52, 152, 219, 0.1)',
                    tension: 0.4,
                    fill: true
                },
                {
                    label: '温度 (°C)',
                    data: [],
                    borderColor: '#e74c3c',
                    backgroundColor: 'rgba(231, 76, 60, 0.1)',
                    tension: 0.4,
                    fill: true
                },
                {
                    label: '光照 (lux)',
                    data: [],
                    borderColor: '#f39c12',
                    backgroundColor: 'rgba(243, 156, 18, 0.1)',
                    tension: 0.4,
                    fill: true,
                    yAxisID: 'y1'
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'top',
                },
                title: {
                    display: false
                }
            },
            scales: {
                x: {
                    display: true,
                    title: {
                        display: true,
                        text: '时间'
                    }
                },
                y: {
                    type: 'linear',
                    display: true,
                    position: 'left',
                    title: {
                        display: true,
                        text: '湿度(%) / 温度(°C)'
                    }
                },
                y1: {
                    type: 'linear',
                    display: true,
                    position: 'right',
                    title: {
                        display: true,
                        text: '光照强度 (lux)'
                    },
                    grid: {
                        drawOnChartArea: false,
                    },
                }
            },
            animation: {
                duration: 750,
                easing: 'easeInOutQuart'
            }
        }
    });
}

// 加载数据
async function loadData() {
    // 如果处于查询状态，不自动刷新
    if (currentQuery) {
        return;
    }

    try {
        updateStatus('loading');
        addLog('info', '📡 开始获取ESP8266转发的Arduino Nano传感器数据');

        const response = await fetch('/sensor-data');
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const result = await response.json();
        sensorData = result.data || [];

        // 显示接收到的传感器数据
        if (sensorData.length > 0) {
            const latestData = sensorData[sensorData.length - 1];
            addLog('receive', `📥 成功接收到Arduino Nano通过ESP8266发送的传感器数据`, {
                数据流程: 'Arduino Nano (读取传感器) → ESP8266 (WiFi转发) → 网站 (显示)',
                最新传感器数据: latestData,
                数据库总记录数: sensorData.length,
                数据接收时间: new Date().toLocaleString('zh-CN')
            });
        } else {
            addLog('warning', '⚠️ 暂无传感器数据，可能Arduino Nano还未通过ESP8266发送数据');
        }

        updateCards();
        updateChart();
        updateTable();
        updateStatus('online');

    } catch (error) {
        console.error('Error loading data:', error);
        addLog('error', `❌ 获取传感器数据失败: ${error.message}`);
        updateStatus('offline');
    }
}

// 更新状态指示器
function updateStatus(status) {
    const statusDot = document.getElementById('statusDot');
    const statusText = document.getElementById('statusText');

    statusDot.className = 'status-dot';

    switch(status) {
        case 'online':
            statusDot.classList.add('online');
            statusText.textContent = '在线';
            break;
        case 'offline':
            statusDot.classList.add('offline');
            statusText.textContent = '离线';
            break;
        case 'loading':
            statusText.textContent = '加载中...';
            break;
    }
}

// 更新卡片数据
function updateCards() {
    if (sensorData.length === 0) return;

    const latestData = sensorData[sensorData.length - 1];

    // 更新数值
    document.getElementById('humidity').textContent = latestData.humidity;
    document.getElementById('temperature').textContent = latestData.temperature;
    document.getElementById('lightIntensity').textContent = latestData.light_intensity;

    // 更新统计信息
    document.getElementById('totalRecords').textContent = sensorData.length;
    document.getElementById('lastUpdate').textContent = formatTime(latestData.timestamp);

    // 更新趋势指示器
    updateTrends(latestData);

    previousData = latestData;
}

// 更新趋势指示器
function updateTrends(currentData) {
    if (!previousData.humidity) return;

    const trends = [
        { id: 'humidityTrend', current: currentData.humidity, previous: previousData.humidity },
        { id: 'temperatureTrend', current: currentData.temperature, previous: previousData.temperature },
        { id: 'lightTrend', current: currentData.light_intensity, previous: previousData.light_intensity }
    ];

    trends.forEach(trend => {
        const element = document.getElementById(trend.id);
        const diff = trend.current - trend.previous;

        if (diff > 0) {
            element.innerHTML = '↗';
            element.className = 'card-trend trend-up';
        } else if (diff < 0) {
            element.innerHTML = '↘';
            element.className = 'card-trend trend-down';
        } else {
            element.innerHTML = '→';
            element.className = 'card-trend trend-stable';
        }
    });
}

// 更新图表
function updateChart() {
    if (!chart || sensorData.length === 0) return;

    // 限制显示最近20个数据点
    const displayData = sensorData.slice(-20);

    chart.data.labels = displayData.map(item => formatTime(item.timestamp, true));
    chart.data.datasets[0].data = displayData.map(item => item.humidity);
    chart.data.datasets[1].data = displayData.map(item => item.temperature);
    chart.data.datasets[2].data = displayData.map(item => item.light_intensity);

    chart.update('none'); // 无动画更新以提高性能
}

// 更新表格
function updateTable() {
    const tableBody = document.getElementById('tableBody');
    tableBody.innerHTML = '';

    // 显示最近10条记录，倒序显示
    const recentData = sensorData.slice(-10).reverse();

    recentData.forEach(item => {
        const row = document.createElement('tr');
        row.innerHTML = `
            <td>${formatTime(item.timestamp)}</td>
            <td>${item.humidity}</td>
            <td>${item.temperature}</td>
            <td>${item.light_intensity}</td>
        `;
        tableBody.appendChild(row);
    });
}

// 格式化时间
function formatTime(timestamp, shortFormat = false) {
    const date = new Date(timestamp);

    if (shortFormat) {
        return date.toLocaleTimeString('zh-CN', {
            hour: '2-digit',
            minute: '2-digit',
            second: '2-digit'
        });
    }

    return date.toLocaleString('zh-CN', {
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit'
    });
}

// 错误处理
window.addEventListener('error', function(event) {
    console.error('JavaScript Error:', event.error);
    updateStatus('offline');
});

// 网络状态监测
window.addEventListener('online', function() {
    updateStatus('online');
    loadData();
});

window.addEventListener('offline', function() {
    updateStatus('offline');
});

// 按日期查询数据
async function queryByDate() {
    const year = document.getElementById('queryYear').value;
    const month = document.getElementById('queryMonth').value;
    const day = document.getElementById('queryDay').value;

    if (!year || !month || !day) {
        alert('请输入完整的年月日信息');
        return;
    }

    try {
        updateQueryStatus('loading');
        addLog('info', `开始按日期查询: ${year}年${month}月${day}日`);

        // 使用通用API获取所有数据，然后在前端过滤
        const response = await fetch('/sensor-data');
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const result = await response.json();
        const allData = result.data || [];

        // 构建目标日期字符串 (YYYY-MM-DD)
        const targetDate = `${year}-${month.padStart(2, '0')}-${day.padStart(2, '0')}`;

        // 在前端过滤指定日期的数据
        const filteredData = allData.filter(item => {
            const itemDate = new Date(item.timestamp).toISOString().split('T')[0];
            return itemDate === targetDate;
        });

        sensorData = filteredData;

        currentQuery = {
            type: 'date',
            year: year,
            month: month,
            day: day
        };

        addLog('success', `日期查询完成，找到 ${filteredData.length} 条记录`);
        updateQueryResultInfo(`${year}年${month}月${day}日`, filteredData.length);
        updateCards();
        updateChart();
        updateTable();
        updateStatus('online');

        if (filteredData.length === 0) {
            addLog('warning', `没有找到 ${year}年${month}月${day}日 的数据`);
            alert(`没有找到 ${year}年${month}月${day}日 的数据`);
        }

    } catch (error) {
        console.error('Error querying data by date:', error);
        addLog('error', `日期查询失败: ${error.message}`);
        updateStatus('offline');
        updateQueryResultInfo('查询失败', 0);
    }
}

// 按小时查询数据
async function queryByHour() {
    const year = document.getElementById('queryYear').value;
    const month = document.getElementById('queryMonth').value;
    const day = document.getElementById('queryDay').value;
    const hour = document.getElementById('queryHour').value;

    if (!year || !month || !day || hour === '') {
        alert('请输入完整的年月日时信息');
        return;
    }

    try {
        updateQueryStatus('loading');

        // 使用通用API获取所有数据，然后在前端过滤
        const response = await fetch('/sensor-data');
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const result = await response.json();
        const allData = result.data || [];

        // 构建目标日期和小时字符串
        const targetDate = `${year}-${month.padStart(2, '0')}-${day.padStart(2, '0')}`;
        const targetHour = parseInt(hour);

        // 在前端过滤指定日期和小时的数据
        const filteredData = allData.filter(item => {
            const itemDateTime = new Date(item.timestamp);
            const itemDate = itemDateTime.toISOString().split('T')[0];
            const itemHour = itemDateTime.getHours();
            return itemDate === targetDate && itemHour === targetHour;
        });

        sensorData = filteredData;

        currentQuery = {
            type: 'hour',
            year: year,
            month: month,
            day: day,
            hour: hour
        };

        updateQueryResultInfo(`${year}年${month}月${day}日${hour}时`, filteredData.length);
        updateCards();
        updateChart();
        updateTable();
        updateStatus('online');

        if (filteredData.length === 0) {
            alert(`没有找到 ${year}年${month}月${day}日${hour}时 的数据`);
        }

    } catch (error) {
        console.error('Error querying data by hour:', error);
        updateStatus('offline');
        updateQueryResultInfo('查询失败', 0);
    }
}

// 重置查询，显示所有数据
async function resetQuery() {
    currentQuery = null;
    addLog('info', '重置查询，显示所有数据');

    // 设置为当前日期
    const today = new Date();
    document.getElementById('queryYear').value = today.getFullYear();
    document.getElementById('queryMonth').value = today.getMonth() + 1;
    document.getElementById('queryDay').value = today.getDate();
    document.getElementById('queryHour').value = '';

    // 重新加载所有数据
    updateQueryResultInfo('显示所有数据', '');
    await loadData();
}

// 更新查询结果信息
function updateQueryResultInfo(queryText, count) {
    document.getElementById('queryResultText').textContent = queryText;
    document.getElementById('queryResultCount').textContent = count ? `(${count} 条记录)` : '';
}

// 更新查询状态
function updateQueryStatus(status) {
    const resultInfo = document.getElementById('queryResultInfo');

    switch(status) {
        case 'loading':
            document.getElementById('queryResultText').textContent = '查询中...';
            document.getElementById('queryResultCount').textContent = '';
            break;
    }
}

// 请求传感器数据更新
async function requestSensorUpdate() {
    const btn = document.getElementById('updateDataBtn');
    const originalText = btn.innerHTML;

    try {
        // 更新按钮状态
        btn.classList.add('updating');
        btn.innerHTML = '📡 发送指令中...';
        btn.disabled = true;

        // 发送更新请求到ESP8266
        const commandData = {
            command: 'Dataup_0'
        };

        addLog('send', '🚀 网站发送指令给ESP8266', commandData);

        const response = await fetch('/sensor-command', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(commandData)
        });

        const result = await response.json();

        if (result.status === 'success') {
            // 指令发送成功
            addLog('success', '✅ 指令发送成功，ESP8266将转发给Arduino Nano', result);
            btn.innerHTML = '⏳ 等待传感器数据...';

            // 等待一段时间让传感器读取新数据
            setTimeout(async () => {
                try {
                    addLog('info', '🔄 开始检查Arduino Nano通过ESP8266发送的传感器数据');
                    // 获取ESP8266转发的传感器数据
                    await loadData();

                    btn.classList.remove('updating');
                    btn.innerHTML = '✅ 数据已更新';
                    btn.disabled = false;
                    addLog('success', '🎉 传感器数据更新完成');

                    // 3秒后恢复按钮状态
                    setTimeout(() => {
                        btn.innerHTML = originalText;
                    }, 3000);

                } catch (error) {
                    console.error('刷新数据失败:', error);
                    addLog('error', `❌ 刷新数据失败: ${error.message}`);
                    btn.classList.remove('updating');
                    btn.innerHTML = '❌ 刷新失败';
                    btn.disabled = false;

                    setTimeout(() => {
                        btn.innerHTML = originalText;
                    }, 3000);
                }
            }, 3000); // 等待3秒让传感器读取数据

        } else {
            throw new Error(result.message || '指令发送失败');
        }

    } catch (error) {
        console.error('请求传感器更新失败:', error);
        addLog('error', `❌ 发送更新指令失败: ${error.message}`);
        btn.classList.remove('updating');
        btn.innerHTML = '❌ 发送失败';
        btn.disabled = false;

        // 3秒后恢复按钮状态
        setTimeout(() => {
            btn.innerHTML = originalText;
        }, 3000);

        // 显示错误提示
        alert('无法发送更新指令，请检查ESP8266连接状态');
    }
}

// 开始灌溉功能
async function startWatering() {
    const durationInput = document.getElementById('wateringDuration');
    const btn = document.getElementById('startWateringBtn');
    const duration = parseInt(durationInput.value);

    // 验证输入
    if (!duration || duration <= 0 || duration > 3600) {
        addLog('error', '❌ 请输入有效的灌溉时长（1-3600秒）');
        alert('请输入有效的灌溉时长（1-3600秒）');
        return;
    }

    const originalText = btn.innerHTML;

    try {
        // 更新按钮状态
        btn.disabled = true;
        btn.innerHTML = '⏳ 发送灌溉指令...';

        // 构造灌溉指令
        const commandData = {
            command: `Watering_${duration}`
        };

        addLog('send', `🚀 网站发送灌溉指令给ESP8266`, {
            command: commandData.command,
            duration: `${duration}秒`
        });

        // 发送灌溉指令到ESP8266
        const response = await fetch('/sensor-command', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(commandData)
        });

        const result = await response.json();

        if (result.status === 'success') {
            // 指令发送成功
            addLog('success', `✅ 灌溉指令发送成功，水阀将开启${duration}秒`, result);
            btn.innerHTML = `💧 灌溉中... (${duration}秒)`;

            // 显示灌溉进行中状态
            let remainingTime = duration;
            const countdownInterval = setInterval(() => {
                remainingTime--;
                if (remainingTime > 0) {
                    btn.innerHTML = `💧 灌溉中... (${remainingTime}秒)`;
                } else {
                    clearInterval(countdownInterval);
                    btn.innerHTML = '✅ 灌溉完成';
                    addLog('success', '🎉 灌溉完成，水阀已关闭');

                    // 3秒后恢复按钮状态
                    setTimeout(() => {
                        btn.innerHTML = originalText;
                        btn.disabled = false;
                    }, 3000);
                }
            }, 1000);

        } else {
            throw new Error(result.message || '灌溉指令发送失败');
        }

    } catch (error) {
        console.error('发送灌溉指令失败:', error);
        addLog('error', `❌ 发送灌溉指令失败: ${error.message}`);
        btn.innerHTML = '❌ 发送失败';
        btn.disabled = false;

        // 3秒后恢复按钮状态
        setTimeout(() => {
            btn.innerHTML = originalText;
        }, 3000);

        alert('无法发送灌溉指令，请检查ESP8266连接状态');
    }
}

// ==================== 日志系统功能 ====================

// 初始化日志系统
function initializeLog() {
    addLog('info', '🔧 日志系统初始化完成');
    addLog('info', '📊 数据流程说明:');
    addLog('info', '  1. 网站 → ESP8266: 发送控制指令 (如 Dataup_0)');
    addLog('info', '  2. ESP8266 → Arduino Nano: 转发控制指令');
    addLog('info', '  3. Arduino Nano → ESP8266: 返回传感器数据');
    addLog('info', '  4. ESP8266 → 网站: 转发传感器数据到云端');
    addLog('info', '🚀 开始初始化网站功能...');
}

// 添加日志条目
function addLog(type, message, data = null) {
    if (isLogPaused) return;

    const logContent = document.getElementById('logContent');
    const logEntry = document.createElement('div');
    logEntry.className = `log-entry log-${type}`;

    const timestamp = new Date().toLocaleTimeString('zh-CN');
    let messageHtml = `
        <span class="log-time">[${timestamp}]</span>
        <span class="log-message">${message}</span>
    `;

    // 如果有数据包内容，格式化显示
    if (data) {
        messageHtml += formatDataPacket(data);
    }

    logEntry.innerHTML = messageHtml;
    logContent.appendChild(logEntry);

    // 限制日志条数
    const logEntries = logContent.querySelectorAll('.log-entry');
    if (logEntries.length > maxLogEntries) {
        logEntries[0].remove();
    }

    // 自动滚动到底部
    const logContainer = document.getElementById('logContainer');
    logContainer.scrollTop = logContainer.scrollHeight;
}

// 格式化数据包显示
function formatDataPacket(data) {
    if (!data) return '';

    let formattedHtml = '<div class="data-packet">';

    if (typeof data === 'string') {
        // 检测是否是JSON
        try {
            const jsonData = JSON.parse(data);
            formattedHtml += '<div class="packet-label">📦 数据包内容 (JSON):</div>';
            formattedHtml += '<pre class="packet-content json-content">' +
                           syntaxHighlightJson(jsonData) + '</pre>';
        } catch (e) {
            // 不是JSON，作为纯文本显示
            formattedHtml += '<div class="packet-label">📦 数据包内容 (文本):</div>';
            formattedHtml += '<pre class="packet-content text-content">' +
                           escapeHtml(data) + '</pre>';
        }
    } else if (typeof data === 'object') {
        formattedHtml += '<div class="packet-label">📦 数据包内容 (对象):</div>';
        formattedHtml += '<pre class="packet-content json-content">' +
                       syntaxHighlightJson(data) + '</pre>';
    }

    formattedHtml += '</div>';
    return formattedHtml;
}

// JSON语法高亮
function syntaxHighlightJson(json) {
    if (typeof json !== 'object') {
        return escapeHtml(String(json));
    }

    const jsonStr = JSON.stringify(json, null, 2);
    let html = jsonStr
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#39;');

    // 语法高亮
    html = html.replace(/("([^"\\]|\\.)*")\s*:/g, '<span class="json-key">$1</span>:'); // 键
    html = html.replace(/:\s*(true|false|null)/g, ': <span class="json-literal">$1</span>'); // 布尔值和null
    html = html.replace(/:\s*(-?\d+\.?\d*)/g, ': <span class="json-number">$1</span>'); // 数字
    html = html.replace(/:\s*"([^"]*)"/g, ': <span class="json-string">"$1"</span>'); // 字符串值

    return html;
}

// HTML转义
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// 清空日志
function clearLog() {
    const logContent = document.getElementById('logContent');
    logContent.innerHTML = `
        <div class="log-entry log-info">
            <span class="log-time">[${new Date().toLocaleTimeString('zh-CN')}]</span>
            <span class="log-message">日志已清空</span>
        </div>
    `;
    addLog('info', '日志窗口已重置');
}

// 暂停/恢复日志
function toggleLog() {
    isLogPaused = !isLogPaused;
    const toggleBtn = document.getElementById('toggleLogBtn');

    if (isLogPaused) {
        toggleBtn.textContent = '恢复';
        toggleBtn.style.background = 'linear-gradient(135deg, #27ae60, #229954)';
        addLog('warning', '日志记录已暂停');
    } else {
        toggleBtn.textContent = '暂停';
        toggleBtn.style.background = 'linear-gradient(135deg, #e74c3c, #c0392b)';
        addLog('info', '日志记录已恢复');
    }
}

// 请求/响应日志包装函数
const originalFetch = window.fetch;
window.fetch = async function(...args) {
    const url = args[0];
    const options = args[1] || {};
    const method = options.method || 'GET';

    // 生成唯一请求ID用于追踪
    const requestId = 'REQ_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);

    // 记录请求开始
    addLog('request', `📤 发送请求 ${requestId}`, {
        method: method,
        url: url,
        headers: options.headers || {},
        timestamp: new Date().toISOString()
    });

    // 记录请求数据包
    if (options.body) {
        let requestData;
        try {
            requestData = typeof options.body === 'string' ? JSON.parse(options.body) : options.body;
        } catch (e) {
            requestData = options.body;
        }

        addLog('request', `📦 请求数据包 ${requestId}`, requestData);
    } else if (method !== 'GET') {
        addLog('request', `📦 请求数据包 ${requestId}`, { body: '[空请求体]' });
    }

    const startTime = Date.now();

    try {
        const response = await originalFetch.apply(this, args);
        const endTime = Date.now();
        const duration = endTime - startTime;

        // 记录响应基础信息
        const responseInfo = {
            requestId: requestId,
            status: response.status,
            statusText: response.statusText,
            headers: Object.fromEntries(response.headers.entries()),
            duration: `${duration}ms`,
            timestamp: new Date().toISOString()
        };

        addLog('response', `📥 接收响应 ${requestId}`, responseInfo);

        // 克隆响应以避免消费原始响应
        const clonedResponse = response.clone();

        // 尝试解析响应数据
        try {
            const contentType = clonedResponse.headers.get('content-type');

            if (contentType && contentType.includes('application/json')) {
                const responseData = await clonedResponse.json();
                addLog('response', `📦 响应数据包 ${requestId}`, responseData);
            } else {
                const responseText = await clonedResponse.text();
                if (responseText.length > 0) {
                    if (responseText.length < 500) {
                        addLog('response', `📦 响应数据包 ${requestId}`, {
                            type: 'text',
                            contentType: contentType,
                            content: responseText
                        });
                    } else {
                        addLog('response', `📦 响应数据包 ${requestId}`, {
                            type: 'text',
                            contentType: contentType,
                            content: `[内容过长，长度: ${responseText.length} 字符]`,
                            preview: responseText.substring(0, 200) + '...'
                        });
                    }
                } else {
                    addLog('response', `📦 响应数据包 ${requestId}`, {
                        type: 'empty',
                        content: '[空响应体]'
                    });
                }
            }
        } catch (parseError) {
            addLog('warning', `⚠️ 解析响应数据失败 ${requestId}`, {
                error: parseError.message,
                headers: Object.fromEntries(clonedResponse.headers.entries())
            });
        }

        // 请求完成总结
        addLog('success', `✅ 请求完成 ${requestId}`, {
            method: method,
            url: url,
            status: response.status,
            duration: `${duration}ms`,
            success: response.ok
        });

        return response;

    } catch (error) {
        const endTime = Date.now();
        const duration = endTime - startTime;

        // 记录错误详情
        addLog('error', `❌ 请求失败 ${requestId}`, {
            method: method,
            url: url,
            error: error.message,
            duration: `${duration}ms`,
            timestamp: new Date().toISOString()
        });

        throw error;
    }
};