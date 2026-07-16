# 实时音视频（RTC）中的回声消除（AEC）技术详解

本篇文档系统地介绍了实时音视频（RTC）中**回声消除（AEC, Acoustic Echo Cancellation）**的基本原理、代码层面的控制流设计、工程落地面临的挑战以及最佳实践。

---

## 1. 什么是回声消除（AEC）？

### 1.1 物理模型与回声的产生
在双向语音通话中，回声通常是由声学反馈引起的。其物理过程如下：
1. **远端信号（Far-end Signal）**：对方说话的声音通过网络传到本地。
2. **播放与采集**：本地扬声器播放出该声音，声音在空气中传播，直接或经过墙壁反射后，被本地麦克风重新录制进去。
3. **回传**：被录入的远端声音随着本地说话人的声音一起，通过网络再次传回给对方。
4. **结果**：对方会在耳机或喇叭里听到自己刚才说话的延迟重音。

```
[远端用户说话] ──(网络)──> [本地扬声器播放]
                                 │
                          (空气传播与反射) -> 产生回声
                                 ▼
[远端听到自己的回声] <──(网络)── [本地麦克风录音]
```

### 1.2 AEC 的核心作用
AEC（Acoustic Echo Cancellation）是一种音频信号处理技术。它通过算法将“即将播放的参考信号”与“麦克风采集到的混合信号”进行对比，从麦克风信号中精准“减去”扬声器播放的声音，从而实现只保留本地人声、消除回声的目的。

---

## 2. 典型控制代码分析

以下是一个典型的 RTC 应用层控制 AEC 模式切换的 C++ 代码片断：

```cpp
void Application::SetAecMode(AecMode mode) {
    aec_mode_ = mode;
    Schedule([this]() {
        auto& board = Board::GetInstance();
        auto display = board.GetDisplay();
        switch (aec_mode_) {
        case kAecOff:
            audio_service_.EnableDeviceAec(false);
            display->ShowNotification(Lang::Strings::RTC_MODE_OFF);
            break;
        case kAecOnServerSide:
            audio_service_.EnableDeviceAec(false);
            display->ShowNotification(Lang::Strings::RTC_MODE_ON);
            break;
        case kAecOnDeviceSide:
            audio_service_.EnableDeviceAec(true);
            display->ShowNotification(Lang::Strings::RTC_MODE_ON);
            break;
        }

        // 如果 AEC 模式发生改变，主动关闭音频通道
        if (protocol_ && protocol_->IsAudioChannelOpened()) {
            protocol_->CloseAudioChannel();
        }
    });
}
```

### 2.1 三种 AEC 模式的设计意图

| 模式名称 | `audio_service_` 行为 | 适用场景与运行逻辑 |
| :--- | :--- | :--- |
| **`kAecOff`** (关闭) | `EnableDeviceAec(false)` | 关闭所有回声消除。通常用于戴耳机通话（物理隔离，无回声）或测试。 |
| **`kAecOnServerSide`** (服务器端) | `EnableDeviceAec(false)` | 本地设备不开启 AEC，节省本地 CPU 算力。回声消除算法运行在云端服务器。 |
| **`kAecOnDeviceSide`** (设备端) | `EnableDeviceAec(true)` | 启用本地硬件 DSP 或客户端软件算法进行回声消除。效果通常最为直接。 |

### 2.2 异步调度与通道重置
* **异步调度 (`Schedule`)**：切换模式往往涉及底层硬件驱动的读写，通过异步队列执行可以避免阻塞主线程（UI 线程）。
* **通道重置 (`CloseAudioChannel`)**：AEC 的启用/禁用通常涉及音频输入输出流参数（如采样率、缓冲区大小、单双声道）的变更。当模式发生改变时，主动关闭并重新初始化音频通道，能够确保底层音频驱动和硬件状态被正确刷新。

---

## 3. AEC 的核心技术指标与算法环节

一个优秀的 AEC 模块通常包含以下几个核心算法步骤：

1. **延迟估计（Delay Estimation）**：计算声音从扬声器输出到被麦克风录入之间的时间差。如果延迟对齐不准，滤波器就无法正常工作。
2. **自适应滤波（Adaptive Filter）**：使用 LMS（最小均方）或 NLMS（归一化最小均方）等算法，建立声学传输路径的数学模型，模拟出回声信号并将其减去。
3. **双讲检测（DTD, Double-Talk Detection）**：判断当前是单方说话还是双方同时说话。在双讲（双方同时说话）时，需要避免自适应滤波器发散，防止本地人声被误当成回声抹去。
4. **非线性处理（NLP, Non-Linear Processing）**：自适应滤波器只能消除线性回声，残留的非线性回声（如喇叭过载失真、房间杂乱反射）需要通过 NLP 或抑制（Suppression）技术做进一步平滑抹除。

---

## 4. 实际工程落地中的避坑指南

### 4.1 设备碎片化与兼容性
* **现象**：在 iOS 设备上，系统自带的 VoiceProcessing 硬件 AEC 表现非常稳定。但在 Android 或各种定制的嵌入式 Linux 板卡上，不同厂商的芯片和驱动实现的硬件 AEC 质量参差不齐，有时甚至会导致声音严重失真或忽大忽小。
* **对策**：建议在客户端设计**设备白名单/黑名单机制**。对于硬件 AEC 表现不佳的设备，强制降级使用软件算法（如 WebRTC 内置的 AEC3）。

### 4.2 服务器端 AEC 的技术局限性
* **挑战**：代码中的 `kAecOnServerSide` 在实际应用中难度极大。因为网络抖动（Jitter）和传输延迟的存在，服务器很难精准对齐“麦克风采集信号”与“远端参考信号”。
* **适用场景**：通常仅在多路混音服务器、性能极其受限的低端物联网设备，或者有成熟 AI 降噪/回声消除大模型支持的特定网关中才会采用。

### 4.3 切换模式时的“听觉瑕疵”
* **现象**：在调用 `CloseAudioChannel()` 关闭并重新打开通道的瞬间，用户可能会听到明显的“啪嗒”（Pop）噪声或短暂的静音。
* **对策**：在关闭通道前，对音频输出进行微秒级的**淡出（Fade-out）**处理；在重新开启通道时实施**淡入（Fade-in）**。如果底层音频框架支持，尽量使用不销毁通道的热切换（Hot-swap）方案。

### 4.4 3A 协同与处理顺序
音频信号在发送前通常需要经过 3A 算法处理。这三者的协同顺序非常关键，错误的顺序会导致算法相互干扰。

```
[麦克风采集] ──> [1. AEC (回声消除)] ──> [2. ANS (降噪)] ──> [3. AGC (自动增益控制)] ──> [编码并发送]
```
* **原因**：必须先消除回声（AEC）。如果在 AEC 之前进行了噪声抑制（ANS）或增益放大（AGC），回声信号的线性特征会被破坏，导致自适应滤波器无法准确建模，从而遗留难以消除的非线性残余回声。

## Citations
[https://github.com/78/xiaozhi-esp32](https://github.com/78/xiaozhi-esp32)

