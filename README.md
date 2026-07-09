# “悟已往之不谏，知来者之可追”

这里是我**核心技术栈复习体系**与**长期学习记录**。

<!-- 技术栈徽章（Shields.io） -->
<p align="left">
  <img src="https://img.shields.io/badge/Language-C-blue.svg?style=flat-square&logo=c" alt="C">
  <img src="https://img.shields.io/badge/RTOS-FreeRTOS-green.svg?style=flat-square" alt="FreeRTOS">
  <img src="https://img.shields.io/badge/RTOS-RT--Thread-orange.svg?style=flat-square" alt="RT-Thread">
  <img src="https://img.shields.io/badge/GUI-LVGL-red.svg?style=flat-square" alt="LVGL">
  <img src="https://img.shields.io/badge/Hardware-ARM--Cortex-blue?style=flat-square" alt="ARM">
</p>


---

## 🎯 核心技术看板

根据我的技能树与项目经历，当前知识库划分为了以下四大技术主线，点击可快速跳转复习：

| 技术大类 | 包含的核心专题（点击直接跳转） | 复习进度 / 状态 |
| :--- | :--- | :--- |
| **🔌 1. 硬件外设与底层** | [🔘 GPIO](hardware-drivers/peripherals/gpio.md) \| [📈 ADC 模数](hardware-drivers/peripherals/adc.md) \| [⏱️ PWM 控制](hardware-drivers/peripherals/pwm.md) \| [🌐 串口/I2C/SPI](hardware-drivers/protocols/protocols.md) | 🟢 核心外设已完备，持续刷题中 |
| **🐧 2. 实时操作系统** | [🚀 FreeRTOS 机制](rtos/freertos/freertos.md) \| [⚓ RT-Thread 系统](rtos/rt-thread/rt-thread.md) | 🟡 正在梳理线程同步（锁与信号量） |
| **🧠 3. 中间件与算法** | [🎨 LVGL 开发](middleware-algorithm/ui.md) \| [📶 蓝牙无线(BLE)](middleware-algorithm/ble/basic.md) \| [📊 滤波/姿态解算](middleware-algorithm/algorithms.md) | 🟢 智能手表/跌倒检测算法已整理 |
| **🛠️ 4. 工程与工具链** | [🔬 示波器/逻辑分析仪](tools/toolchains/scope.md) \| [💾 内存优化](tools/memory-opt.md) \| [📂 Git 规范](tools/git-workflow.md) | 🟡 正在补充 .map 内存布局分析 |

---

## 🧭 备战面试快速指引

1. **多维检索**：点击左上角的 **“搜索框”**，输入如“指针”、“DMA”、“互斥锁”等，可瞬间跨学科检索。
2. **主动回忆（卡片复习法）**：在阅读外设和协议专题时，先看 **“🙋‍♂️ 面试高频问题”**，在大脑中尝试作答后再展开看答案。
3. **最新学习日志**：

<!-- 动态今日日志按钮 -->
<p align="left">
  <a id="today-log-btn" href="javascript:void(0);" style="display: inline-block; background-color: #2f54eb; color: white; padding: 10px 20px; border-radius: 4px; text-decoration: none; font-weight: bold; box-shadow: 0 2px 8px rgba(47, 84, 235, 0.2);">📅 一键进入今日日志</a>
</p>

<script>
  (function() {
    function updateTodayLink() {
      const today = new Date();
      const year = today.getFullYear();
      // 月份和日期如果小于10，自动补0（符合您 2026-07-09 的命名规范）
      const month = String(today.getMonth() + 1).padStart(2, '0');
      const day = String(today.getDate()).padStart(2, '0');
      const dateStr = year + '-' + month + '-' + day;
      
      const btn = document.getElementById('today-log-btn');
      if (btn) {
        // 动态修改跳转链接为：#/daily/YYYY-MM-DD
        btn.href = '#/daily/' + dateStr;
      }
    }
    // 延迟 100 毫秒确保页面渲染完毕后再执行脚本
    setTimeout(updateTodayLink, 100);
  })();
</script>