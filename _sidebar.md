* [🏠 首页](README.md)
* [📝 临时速记 (草稿箱)](scratchpad.md)

* 💻 C 语言与底层
  * [C 语言-运算符专题](c-language/operators.md)
  * [C 语言-枚举专题](c-language/enums.md)
  * [C 语言-数组专题](c-language/arrays.md)
  * [C 语言-指针专题](c-language/pointer.md)
  * [C 语言-结构体专题](c-language/struct.md)
  * [回调函数](c-language/callback.md) 
  * [C 语言-数据类型与类型转换专题](c-language/types-and-conversions.md)
  * [C 语言-位运算与寄存器操作专题](c-language/bitwise-registers.md)
  * [C 语言-存储期、作用域与模块化专题](c-language/storage-modules.md)
  * [C 语言-字符串与缓冲区专题](c-language/strings-buffers.md)
  * [C 语言-预处理、编译与链接专题](c-language/preprocess-build-link.md)
  * [C 语言-内存布局与未定义行为专题](c-language/memory-undefined-behavior.md)
  * [C 语言-中断、并发与 volatile 专题](c-language/isr-concurrency.md)
  * [C 语言-嵌入式可靠性与测试专题](c-language/reliability-testing.md)

* 💾 芯片平台与开发 (MCU)
  * [📶 ESP32 架构与 ESP-IDF](esp/esp32env.md)

* 🔌 硬件与底层驱动
  * 核心外设 (Peripherals)
    * [🔘 GPIO 输入输出](hardware-drivers/peripherals/gpio.md)
    * [📈 ADC 模数转换](hardware-drivers/peripherals/adc.md)
    * [⏱️ PWM 定时器控制](hardware-drivers/peripherals/pwm.md)
  * 通信协议 (Protocols)
    * [📟 UART 串口通信](hardware-drivers/protocols/uart.md)
    * [🤝 I2C 总线协议](hardware-drivers/protocols/i2c.md)
    * [⚡ SPI 总线协议](hardware-drivers/protocols/spi.md)

* 🐧  实时操作系统 (RTOS)
  * [🚀 FreeRTOS 核心机制](rtos/freertos/freertos.md)
  * [⚓ RT-Thread 构建系统](rtos/rt-thread/rt-thread.md)

* 🧠 中间件、应用与网络
  * [🎨 LVGL 界面开发](middleware-algorithm/lvgl.md)
  * 📶 蓝牙无线 (BLE)
    * [基础：BLE 协议栈基础](middleware-algorithm/ble/basic.md)
    * [进阶：智能手表低功耗设计](middleware-algorithm/ble/lowpower.md)
    * [实战：BLE OTA 固件升级](middleware-algorithm/ble/ota.md)
  * 🛜 Wi-Fi 与物联网通信
    * [📦 Wi-Fi 硬件与 AT 模组](middleware-algorithm/wifi/module.md)
    * [📑 802.11 协议与连接机制](middleware-algorithm/wifi/protocol.md)
    * [⚙️ 一键配网技术 (SmartConfig)](middleware-algorithm/wifi/provisioning.md) 
  * [🔈回声消除 (AEC)](middleware-algorithm/aec.md)

  * 🌐网络与物联网
    * [ MQTT 物联网协议](middleware-algorithm/wireless-network/mqtt.md)
    * [TCP/UDP 网络套接字](middleware-algorithm/wireless-network/tcp-udp.md)

* 🛠️  工程实践与工具链
  * 💻 开发环境搭建 (Environment)
    * [🐧 WSL (Ubuntu) 与 VS Code 远程开发](tools/env-setup/wsl-ubuntu.md)
    * [📶 WSL 下 ESP-IDF 搭建与串口烧录](tools/env-setup/esp-idf-wsl.md)
  * 🔧 嵌入式工具链与调试
    * [🐞 GDB 调试完整学习流程](tools/debugging/gdb.md)
    * [💾 内存优化与 .map 分析](tools/debugging/memory-opt.md)
  * 调试仪器使用
    * [🔬 示波器波形分析](tools/toolchains/scope.md)
    * [📟 逻辑分析仪时序抓取](tools/toolchains/logic-analyzer.md)
  * 软件工程 
    * [🛠️ Docsify 搭建指南](tools/docsify-guide.md)
    * [📂 Git 下载安装与规范化 Code Review](tools/git-workflow.md)
