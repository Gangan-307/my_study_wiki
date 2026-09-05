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
| **🔌 1. 硬件外设与底层** | [🔘 GPIO](hardware-drivers/peripherals/gpio.md) \| [📈 ADC 模数](hardware-drivers/peripherals/adc.md) \| [⏱️ PWM 控制](hardware-drivers/peripherals/pwm.md) \| [📟 UART](hardware-drivers/protocols/uart.md) / [I2C](hardware-drivers/protocols/i2c.md) / [SPI](hardware-drivers/protocols/spi.md) | 🟡 已建立学习纲要，待逐项实验完善 |
| **🐧 2. 实时操作系统** | [🚀 FreeRTOS 机制](rtos/freertos/freertos.md) \| [⚓ RT-Thread 系统](rtos/rt-thread/rt-thread.md) | 🟡 正在梳理线程同步（锁与信号量） |
| **🧠 3. 中间件、应用与网络** | [🎨 LVGL 开发](middleware-algorithm/lvgl.md) \| [📶 蓝牙无线(BLE)](middleware-algorithm/ble/basic.md) \| [🌐 MQTT](middleware-algorithm/wireless-network/mqtt.md) \| [🔈 回声消除 AEC](middleware-algorithm/aec.md) | 🟡 基础笔记与待实践纲要并行完善 |
| **🛠️ 4. 工程与工具链** | [🔬 示波器/逻辑分析仪](tools/toolchains/scope.md) \| [💾 内存优化](tools/debugging/memory-opt.md) \| [📂 Git 规范](tools/git-workflow.md) | 🟡 正在补充 .map 内存布局分析 |

---

## 🧭 备战面试快速指引

1. **多维检索**：点击左上角的 **“搜索框”**，输入如“指针”、“DMA”、“互斥锁”等，可瞬间跨学科检索。
2. **主动回忆（卡片复习法）**：在阅读外设和协议专题时，先看 **“🙋‍♂️ 面试高频问题”**，在大脑中尝试作答后再展开看答案。
3. **学习记录**：每日学习日志与阶段周报仅保存在本地，不随公开知识库同步。
