# 📝 临时速记与灵感草稿箱

> **💡 使用法则**：白天随手记，晚上随手清。不要让这里的草稿堆过夜！

---

## ⚡ 今日速记区（在此处直接粘贴/敲代码）

*   *(在此处输入您白天的临时灵感、未排版的C语言代码、面试官提到的某个词...)*

   

 21ok


*文档编写日期：2026年7月21日*  
*作者：基于给定源代码分析整理*

---

## 🧹 晚间整理清单
在睡觉前，将上面的内容剪切并整理到以下专题中：
- [ ] 属于 **C 语言** 吗？👉 [进入 C 语言专题](c-language/pointer.md)
- [ ] 属于 **RTOS** 核心吗？👉 [进入 RT-Thread 专题](rtos/rt-thread/rt-thread.md)
- [ ] 属于 **硬件外设** 吗？👉 [进入 硬件驱动专题](hardware-drivers/peripherals/gpio.md)


它不是 Linux 智能终端，也不适合本地大模型，但已经明显超过普通传感器开发板。
已经有依据的能力
能力	现有实现依据	实际边界
图形界面	官方 LVGL v8/v9、Watch 蜂窝菜单、表盘、3D 动画	屏幕/触摸扩展板需要另配；512×512、60fps 是显示流水线上限，不代表所有复杂页面都稳定 60fps
运动传感	官方例程已读取光照、三轴磁力、加速度、陀螺仪、计步	可做计步、姿态、指南针、抬腕；指南针必须校准，跌倒检测不能作为医疗功能
本地音频	官方有黄山派专用 TF 卡 MP3/WAV 播放例程	需要外接匹配功率/阻抗的喇叭；录音例程需要从通用 52x 工程移植到该板
双模蓝牙	SDK 已有 A2DP、AVRCP、HFP、SPP、PAN、BLE HID、ANCS、文件传输、OTA	不建议让所有协议同时常驻；HFP 全双工通话还要调麦克风、功放、SCO 和回声消除
在线视频	官方 streaming_media 明确支持黄山派	通过手机蓝牙 PAN 上网，不是板载 Wi-Fi；分辨率、码率必须控制
存储/升级	16MB NOR、8MB PSRAM、TF 卡、DFU/BLE/PAN OTA	官方分区中主程序约 8MB、文件系统约 4MB；大型图片、音乐、录像放 TF 卡
低功耗	双核、PM、充电管理、电池 ADC、RTC	宣传的 7µA 是特定 BLE 链路条件，不是整块开发板开屏运行功耗


我建议做的“极致成品”
做一个“黄山派腕式/桌面蓝牙多媒体终端”，按运行模式切换资源：
日常模式：表盘、日期、电量、环境光自动亮度、计步、活动量、电子罗盘。
运动模式：记录加速度、陀螺仪、步数、方向到 TF 卡；手机通过 BLE 提供 GPS、天气和时间。
音频模式：TF 卡 MP3/WAV 播放、录音备忘、蓝牙 A2DP 音箱、手机音乐控制。
通话模式：来电状态、接听/挂断、音量控制；最后再接入 SCO 语音和 AEC。
联网模式：手机开启蓝牙 PAN，设备显示天气、同步数据、OTA，或运行官方在线视频示例。
工具模式：蓝牙 HID 拍照遥控器、久坐提醒、寻找手机、指南针、传感器曲线。
在线视频、音乐、通话属于高负载模式，进入时暂停不需要的服务并释放解码缓存，不要试图让它们同时运行。
推荐软件结构
HCPU 240MHz：RT-Thread、LVGL、文件系统、传感算法、音视频解码、应用状态机。
LCPU 24MHz：沿用 SDK 的蓝牙协议栈和低功耗机制，不自行重写协议栈。
8MB PSRAM：帧缓冲、LVGL 图片缓存、音视频缓冲。512×512 RGB565 单帧约 512KB，双缓冲约 1MB。
片外 NOR：固件、配置、字体、小型资源、DFU 分区。
TF 卡：歌曲、录音、运动日志、视频缓存。
服务层：sensor_service、audio_service、bt_service、storage_service、power_manager，界面只通过消息调用服务。
落地流程
准备主板、匹配的屏幕/触摸扩展板、TF 卡、锂电池、喇叭；振动马达需要接预留焊点。
固定使用官方稳定版 SDK v2.5.0，不要直接以持续变化的 main 分支作为产品基线。
分别跑通四个官方基准：sensor、lvgl/watch、mp3_sd_player、streaming_media。
以 lvgl/watch 为主工程，先接入传感器、电池、TF 日志，完成基本终端。
再加入本地音乐和录音，先解决音频卡顿、TF 读写和功放噪声。
加入 BLE 同步、HID 和 OTA。iOS 通知可参考 ANCS；Android 通知需要一个带通知读取权限的配套 App。
最后加入 A2DP、HFP 和 PAN 视频，每增加一个协议都进行内存、蓝牙重连、音频欠载和长时间运行测试。
用电流表分别测量待机、亮屏、传感记录、音乐和视频功耗，再决定电池容量，不能用芯片宣传电流直接估算续航。
明确做不到或不能直接承诺的
没有板载 Wi-Fi、GPS、心率、血氧、气压、摄像头；Watch 示例里的心率、天气、相机图标不代表硬件存在。
Type-C 主要用于供电和 CH340N 串口，不能直接假定它能作为芯片原生 USB 设备口。
不能运行 Android/Linux 应用，也不适合语音大模型、视觉模型或高清视频。
在线功能默认依赖手机蓝牙 PAN；脱离手机要外接 Wi-Fi/4G 模块。
社区已有黄山派 Nofrendo NES 模拟器，但其 README 仍把音频和全屏列为待办，适合作为性能证明，不宜直接算完整产品功能。

当前音乐模块本质上是“蓝牙音乐接收状态页 + 手机播放器遥控器”，不是独立的本地音乐播放器。A2DP 音频播放由 SiFli SDK 处理，项目代码负责界面、AVRCP 控制、元数据、歌词、封面和音量同步。

**整体链路**

```text
手机音乐播放器
  ├─ A2DP：音频流、播放/暂停状态
  ├─ AVRCP：歌名/歌手/专辑、控制、音量、兜底封面
  └─ BLE 伴侣协议：同步歌词、优先传输封面
                ↓
          music_app 快照
                ↓ 每 300 ms
          LVGL 音乐界面
```

**一、图片元素与当前 UI 代码**

音乐页面由 [music_ui.c](/mnt/d/iotproject/lcHspEc800m/lcHsp/watch_pro/lchspi-development-learning/src/ui/music/music_ui.c:277) 创建，尺寸固定为 `390 × 450`，黑色底板。

- 顶部 `♫ MUSIC`：[music_ui.c:300](/mnt/d/iotproject/lcHspEc800m/lcHsp/watch_pro/lchspi-development-learning/src/ui/music/music_ui.c:300)
- 左上角返回按钮：42 × 42，点击返回上一页
- 封面区域：128 × 128，顶部 Y=58，圆角 8
- 第一行文字：Y=194，目前显示 `artist`
- 第二行文字：Y=222，目前显示 `album`
- 第三行文字：Y=250，目前显示歌词；没有歌词时显示 `title`
- 播放状态：Y=312，显示 `PLAYING`、`PAUSED` 或 `NOT CONNECTED`
- 音量文字和进度条：Y=332 附近
- 上一首、播放/暂停、下一首：底部三个圆形按钮

这里与参考图有一个明显的字段差异：参考图第一行是歌曲名，但当前代码第一行显示歌手。`snapshot.title` 没有独立的标题控件，只会在没有歌词时显示到第三行，见 [music_ui.c:97](/mnt/d/iotproject/lcHspEc800m/lcHsp/watch_pro/lchspi-development-learning/src/ui/music/music_ui.c:97)。

因此当前实际顺序是：

```text
歌手
专辑
歌词，或歌曲名兜底
```

而参考图更接近：

```text
歌曲名
专辑或歌手
作曲/歌词
```

**二、界面刷新机制**

页面不是由蓝牙回调直接更新，而是创建一个 300 ms 的 LVGL 定时器：[music_ui.c:404](/mnt/d/iotproject/lcHspEc800m/lcHsp/watch_pro/lchspi-development-learning/src/ui/music/music_ui.c:404)。

定时器每次调用 `music_app_get_snapshot()`，然后比较：

- `metadata_generation`：歌名、歌手、专辑是否变化
- `lyric_generation`：歌词是否变化
- `cover_generation`：封面是否变化
- `connected`：蓝牙音乐是否连接
- `playing`：是否正在播放
- `volume`：AVRCP 音量，范围 0～127

这种设计是合理的：蓝牙线程只改数据，LVGL 线程只改界面，通过互斥锁避免跨线程操作 LVGL。

但音乐页在系统启动时就被创建，所以这个 300 ms 定时器即使音乐页没有显示也会持续工作、请求封面和刷新快照。

**三、音乐状态数据**

所有 UI 数据集中在 [music_app.h](/mnt/d/iotproject/lcHspEc800m/lcHsp/watch_pro/lchspi-development-learning/src/bluetooth/music_app.h:14) 的 `music_app_snapshot_t`：

- `title[128]`
- `artist[128]`
- `album[128]`
- `lyric[193]`
- 三个 generation 版本号
- 连接、播放、封面、音量状态

状态由 [music_app.c](/mnt/d/iotproject/lcHspEc800m/lcHsp/watch_pro/lchspi-development-learning/src/bluetooth/music_app.c:36) 管理，并用 `music_state_lock` 保护。

AVRCP 元数据支持 UTF-8、UCS-2、UTF-16BE、UTF-16LE，并统一转换成 UTF-8，中文歌名可以正常进入 LVGL 字体系统。四字节 Unicode 字符，例如部分 emoji，目前会退化成 `?`。

歌曲变化时会：

1. 更新歌名、歌手、专辑。
2. 增加 `metadata_generation`。
3. 清空旧歌词。
4. 取消旧封面接收。
5. 开始请求新封面。

对应代码在 [music_app.c:360](/mnt/d/iotproject/lcHspEc800m/lcHsp/watch_pro/lchspi-development-learning/src/bluetooth/music_app.c:360)。

**四、播放控制**

三个按钮只是发送 AVRCP 命令：

- 上一首：`bt_interface_avrcp_previous_ext`
- 播放：`bt_interface_avrcp_play_ext`
- 暂停：`bt_interface_avrcp_pause_ext`
- 下一首：`bt_interface_avrcp_next_ext`

实现位于 [music_app.c:940](/mnt/d/iotproject/lcHspEc800m/lcHsp/watch_pro/lchspi-development-learning/src/bluetooth/music_app.c:940)。

点击播放按钮后不会立即修改 UI，而是等待手机返回 A2DP/AVRCP 播放状态，再把按钮切换成播放或暂停图标。因此蓝牙延迟时，按钮状态会稍晚变化。没有远端蓝牙地址时，按钮点击直接无效，但当前 UI 不会禁用按钮或给出提示。

**五、封面链路**

封面最终保存为根文件系统的 `/cover.jpg`，LVGL 使用 SJPG 解码：[music_ui.c:172](/mnt/d/iotproject/lcHspEc800m/lcHsp/watch_pro/lchspi-development-learning/src/ui/music/music_ui.c:172)。

有两条封面来源：

1. BLE 伴侣通道，优先使用  
   先写 `cvphone.tmp`，检查 generation、连续 offset、总长度和 CRC32；成功后通过备份文件替换 `cover.jpg`。最大只允许 8 KiB，超出会拒绝。见 [music_app.c:584](/mnt/d/iotproject/lcHspEc800m/lcHsp/watch_pro/lchspi-development-learning/src/bluetooth/music_app.c:584)。

2. AVRCP Cover Art，作为兜底  
   每 800 ms 最多请求 10 次，数据直接写入 `cover.jpg`。伴侣通道启用时会忽略晚到的 AVRCP 封面，避免覆盖手机 App 发来的新封面。见 [music_app.c:819](/mnt/d/iotproject/lcHspEc800m/lcHsp/watch_pro/lchspi-development-learning/src/bluetooth/music_app.c:819)。

UI 期望封面是 128 × 128。其他尺寸不会缩放，只会居中显示并受 128 × 128 容器裁剪，所以伴侣 App 最好统一发送 128 × 128 JPEG。

文件系统在 [main.c](/mnt/d/iotproject/lcHspEc800m/lcHsp/watch_pro/lchspi-development-learning/src/app/main.c:31) 中挂载。挂载失败时音乐控制仍可用，但封面无法保存和显示。

**六、歌词同步**

歌词不是 AVRCP 标准数据，而是 Android 伴侣通过自定义 BLE 协议发送：

- `0x41`：歌词开始包，包含 generation 和总长度
- `0x42`：歌词数据包，包含 generation、offset 和分片内容

手表按顺序重组，最大 192 字节，完成后写入音乐快照：[find_phone_ble.c](/mnt/d/iotproject/lcHspEc800m/lcHsp/watch_pro/lchspi-development-learning/src/bluetooth/find_phone_ble.c:365)。

当前只显示一段歌词，没有时间戳解析、逐行滚动或卡拉 OK 式同步。三种占位文字会被识别为“无有效歌词”，随后改为显示歌曲名。

**七、音量和静音**

AVRCP 音量范围是 0～127，UI 转成 0～100%：

```c
(volume * 100 + 63) / 127
```

物理按键在音乐页中直接调节本地 `BT_MUSIC` 音量，并同步给手机：[watch_key_router.c](/mnt/d/iotproject/lcHspEc800m/lcHsp/watch_pro/lchspi-development-learning/src/services/watch_key_router.c:117)。

控制中心的音量滑块也使用同一套接口，静音按钮控制公共扬声器静音：[home_gestures.c](/mnt/d/iotproject/lcHspEc800m/lcHsp/watch_pro/lchspi-development-learning/src/ui/generated/home_gestures.c:734)。

代码还维护 4 条、1.5 秒有效的“音量回声记录”，避免手表设置音量后，手机回传相同音量再次触发循环更新。

**八、音乐页面导航**

主页、音乐和蜂窝都嵌入 `home_pager` 的 tileview：

```text
主页侧音乐 (0,1) ← 主页 (1,1) → 蜂窝 (2,1) → 蜂窝侧音乐 (3,1)
```

从主页进入音乐使用左侧固定 tile；从蜂窝进入时，把同一个 `ui_ScreenMusic` 重新挂到蜂窝右侧的音乐 tile，避免创建两份音乐 UI，见 [home_pager.c](/mnt/d/iotproject/lcHspEc800m/lcHsp/watch_pro/lchspi-development-learning/src/ui/generated/home_pager.c:221)。

从蜂窝进入时右滑返回蜂窝；从主页进入时返回主页。蜂窝音乐入口由 [ui.c](/mnt/d/iotproject/lcHspEc800m/lcHsp/watch_pro/lchspi-development-learning/src/ui/generated/ui.c:56) 分发。

最后，`image/number/music.jpg` 是一张设备实拍图，不是界面资源；当前构建没有打包它。蜂窝音乐图标实际来自 `image/app_grid/img_music.png`。