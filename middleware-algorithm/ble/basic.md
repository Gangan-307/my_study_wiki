# BLE 基础：GAP、GATT、Service 与 Characteristic

低功耗蓝牙（Bluetooth Low Energy，BLE）可以先记成两件事：

1. **GAP 负责让设备被发现、建立连接并管理连接。**
2. **GATT 负责连接建立后，双方按约定读写哪些数据。**

以“手机读取智能手环当前电量”为例：手环先通过 GAP 广播“我在这里”，手机扫描到后建立连接；随后手机通过 GATT 找到“电量服务”，读取“电量特征值”，得到 `80%`。

---

## 一、先建立正确的整体模型

BLE 的数据层次可以这样理解：

```text
Profile（规范/功能组合，通常不是设备中的一个实际对象）
  └── Service（一个业务能力，例如电量）
        └── Characteristic（一个可读、可写或可订阅的数据点）
              ├── Value（真正的数据，例如 80）
              └── Descriptor（对该数据点的附加说明或配置）
```

设备中真正维护的是 **GATT 数据库（Attribute Table）**。Profile 更像蓝牙 SIG 或产品设计者写出的“功能说明书”：它规定某类产品应包含哪些 Service、Characteristic，以及它们怎样协作。

例如，心率 Profile 可以规定设备组合使用心率服务和设备信息服务；而手环实际的 GATT 数据库中会存放这些服务和数据值。

### 1. Profile：功能规范或功能组合

Profile 不是“从机里一个叫 Profile 的数据包”。它描述的是一组可互操作的 GATT 功能组合。

- **标准 Profile**：由 Bluetooth SIG 定义，例如心率、HID over GATT（HOGP）。
- **自定义 Profile**：产品自己约定的 Service 与 Characteristic 组合，例如一个自定义串口服务。

Profile 的价值是让不同厂商的软件理解相同业务。若手机和设备都遵循电量相关标准，手机就知道去哪里读取电量；若使用自定义 UUID，则通常只有配套 App 知道其含义。

### 2. Service：一组相关业务数据

Service 将一个完整业务能力的相关数据归在一起。例如：

- **Battery Service（电量服务）**：设备电量。
- **Device Information Service（设备信息服务）**：厂商名、型号、序列号等。
- **Heart Rate Service（心率服务）**：心率测量、传感器位置、控制点等。

每个 Service 由 UUID 标识，内部至少包含一个 Characteristic。

### 3. Characteristic：BLE 通信最常操作的数据点

Characteristic 是应用层读、写、订阅的基本对象。它包含：

- **Value**：实际字节数据，例如电量 `80`、温度 `0xFED4`。
- **Properties（属性）**：允许什么操作，例如可读、可写、可通知。
- **Descriptors（描述符，可选）**：对 Characteristic 的补充信息或配置。

不要将 Characteristic 只理解成“标签”。它更接近“带权限的数据接口”。同一个值能否读取、写入或主动推送，取决于它声明的 Properties。

### 4. UUID 与 Handle：不要混淆

| 名称 | 作用 | 例子 | 是否跨设备固定 |
| :--- | :--- | :--- |
| UUID | 标识“这是什么类型的服务或特征值” | 电量服务 `0x180F`，电量值 `0x2A19` | 是，标准 UUID 的业务含义固定 |
| Handle | 标识“这条属性在当前设备数据库中的位置” | `0x0025` | 否，数据库调整后可能变化 |

UUID 有两类常用形式：

- **16 位标准 UUID**：由 Bluetooth SIG 分配，例如心率服务 `0x180D`、电量服务 `0x180F`。不能把标准 UUID 当作任意自定义用途使用。
- **128 位自定义 UUID**：产品自行生成，用于私有 Service 和 Characteristic。

Handle 是 ATT 层的 16 位索引。客户端通常先做服务发现，得到目标 Characteristic 的 Handle，再按 Handle 读、写或订阅。

---

## 二、GAP：发现、广播与连接

GAP（Generic Access Profile）负责设备如何被发现、是否可连接、连接角色和基本安全能力。它不定义“电量值怎样读取”，那是 GATT 的职责。

### 1. GAP 角色

| 角色 | 主要行为 | 常见设备 |
| :--- | :--- | :--- |
| Broadcaster（广播者） | 只发广播，不接受连接 | Beacon、广播温湿度标签 |
| Observer（观察者） | 只扫描，不发起连接 | 网关的被动扫描模式 |
| Peripheral（外围设备） | 广播并接受连接 | 手环、传感器、蓝牙锁 |
| Central（中心设备） | 扫描并发起连接 | 手机、网关、平板 |

“主机/从机（Master/Slave）”是旧称；新代码和文档优先使用 Central/Peripheral。角色是 GAP 概念，与后面的 GATT Client/Server 不是同一件事。

### 2. 广播数据与扫描响应

外围设备通常周期性发送 Advertising Data（广播数据），让中心设备发现自己。若广告类型支持扫描，中心设备可发出 Scan Request，设备再返回 Scan Response（扫描响应）。

```text
外围设备                         中心设备
   | ---- Advertising Data ----> |  发现设备
   | <---- Scan Request -------- |  可选
   | ---- Scan Response ------> |  可选，补充名称等信息
   | <---- Connect Request ----- |  建立连接
```

在**传统广播（Legacy Advertising）**中，广播数据与扫描响应各最多 31 字节。Bluetooth 5 的扩展广播可以承载更大数据，但手机兼容性、芯片能力和实际项目配置都需要单独确认。

广播间隔越短，发现速度通常越快，但平均功耗越高。广播包内常放：Flags、设备名、Service UUID、厂商自定义数据等；不要把持续变化的大量业务数据长期塞进传统广播包。

### 3. 广播与连接的关系

广播不等于已连接。Beacon 可以只广播，让多个观察者接收信息；需要可靠双向通信、读取服务或订阅数据时，通常要建立连接。

常见的小型外围设备一次只维持一个连接，但这不是 BLE 规范的绝对限制。一个 Central 能管理多少 Peripheral、一个 Peripheral 能接受多少 Central，取决于芯片、协议栈、内存和产品设计。

---

## 三、GATT 与 ATT：连接后的数据通信

GATT（Generic Attribute Profile）定义应用如何通过 Service、Characteristic 和 Descriptor 组织、发现与访问数据。它建立在 ATT（Attribute Protocol）之上。

ATT 可以理解为“带 Handle 的属性表访问协议”：每个属性有 Handle、类型 UUID、权限和值。GATT 在 ATT 的基础上规定了 Service、Characteristic 等结构和操作流程。

### 1. GATT Client 与 GATT Server

| 角色 | 职责 | 手环读取电量时的例子 |
| :--- | :--- | :--- |
| GATT Server | 保存 GATT 数据库，提供数据和响应 | 手环保存电量服务与当前电量 |
| GATT Client | 发现服务，并发起读、写、订阅请求 | 手机查找电量服务并读取数值 |

典型情况下，手机是 Central + GATT Client，手环是 Peripheral + GATT Server；但二者不是强制绑定。一个设备可以同时承担不同连接中的多种角色。

### 2. 从广播到读到电量的完整流程

```text
1. 手环广播设备名、可连接标志和服务信息                    （GAP）
2. 手机扫描到手环并发起连接                                  （GAP）
3. 双方协商连接参数，建立定期的 Connection Event            （链路层）
4. 手机发现 Service / Characteristic，获得对应 Handle        （GATT/ATT）
5. 手机读取电量 Characteristic 的 Value                      （GATT Read）
6. 手环返回当前值，例如 0x50，即十进制 80                    （ATT Response）
```

连接间隔（Connection Interval）定义连接事件的时间间距，不是“中心设备每隔一段时间重新连接一次”。较短的连接间隔通常延迟更低、功耗更高；较长间隔更省电、响应更慢。

常见连接参数还包括：

- **Peripheral Latency**：外围设备可跳过若干连接事件以节能。
- **Supervision Timeout**：连续一段时间未收到有效通信后，连接被判定断开。
- **ATT MTU**：单个 ATT PDU 的最大传输单元。默认 MTU 为 23 字节，常见读写/通知的 Value 载荷最多为 `MTU - 3`，即 20 字节。

MTU 协商、Data Length Extension 和应用分包是不同层的概念。需要发送较长数据时，先确认协商结果，再设计分包、序号和重传策略。

---

## 四、Characteristic 的五种核心通信方式

| Property | 发起方 | 是否有 ATT 响应/确认 | 典型用途 |
| :--- | :--- | :--- |
| Read | Client | Server 返回 Read Response | 读取电量、版本号、配置 |
| Write | Client | 有 Write Response | 写入重要配置，需要知道请求是否被接受 |
| Write Without Response | Client | 无 ATT Response | 高频控制数据，减少往返等待 |
| Notify | Server | 无 ATT 层确认 | 连续传感器数据、实时状态 |
| Indicate | Server | Client 必须确认 | 重要状态变化，可靠性优先 |

读取和写入由 Client 发起。**但 Notify/Indicate 是 Server 在客户端订阅后主动发送的**，不需要客户端每次轮询读取。这是 BLE 实时数据传输最常用的方式。

### CCCD：订阅通知/指示的开关

一个可 Notify 或 Indicate 的 Characteristic 通常带有 CCCD（Client Characteristic Configuration Descriptor，UUID `0x2902`）。客户端向 CCCD 写入配置，表示“我希望接收通知”或“我希望接收指示”。

```text
手机 Client                         手环 Server
    | --- 写 CCCD，开启 Notify ---> |
    | <------ Notification -------- |  心率或步数变化时主动推送
    | <------ Notification -------- |
```

Notify 更快，但 ATT 层不要求客户端确认每一包；Indicate 必须收到客户端确认后才能继续发送下一条 Indication，吞吐量更低但应用层交付确认更强。两者都仍依赖 BLE 链路层的可靠传输机制。

---

## 五、两个可直接理解的 GATT 数据库例子

### 1. 标准电量服务

```text
Service: Battery Service                UUID: 0x180F
  └── Characteristic: Battery Level     UUID: 0x2A19
        ├── Properties: Read, Notify（具体是否支持由设备决定）
        ├── Value: 0x50  -> 80%
        └── Descriptor: CCCD（只有支持 Notify/Indicate 时才需要）
```

手机发现 `0x180F` 后，继续发现其中的 `0x2A19`，然后根据 Properties 决定读取或订阅。

### 2. 自定义 UART 风格服务

BLE 没有真正的 UART 物理串口；所谓“BLE UART”通常是自定义 Service，模仿串口的收发体验。

```text
Custom UART Service                    UUID: 自定义 128 位 UUID
  ├── RX Characteristic                Properties: Write / Write Without Response
  │     手机写入 -> 设备接收
  └── TX Characteristic                Properties: Notify
        设备发送 -> 手机订阅后接收
```

`RX`、`TX` 的命名取决于站在谁的视角，不能只凭名称判断方向。设计协议时必须明确：谁写入、谁通知、单包最大长度、分包格式、校验方式和超时策略。

---

## 六、常见误区速查

| 容易误解 | 正确理解 |
| :--- | :--- |
| Profile 存在于从机中，是通信数据结构 | Profile 是功能规范；设备实际维护的是 GATT 数据库 |
| 一个 Peripheral 永远只能连接一个 Central | 常见小设备如此，但连接数由协议栈和资源决定，不是绝对规范 |
| GATT 所有数据都必须由 Client 轮询 | Read/Write 由 Client 发起；订阅后 Server 可通过 Notify/Indicate 主动发送 |
| 连接间隔表示设备会重新连接 | 连接已建立；连接间隔表示连接事件的时间间距 |
| 标准 16 位 UUID 可以随意自定义 | 标准 UUID 有固定含义；私有业务应使用自定义 128 位 UUID |
| UUID 就是访问地址 | UUID 说明属性类型；实际 ATT 访问通常依赖当前设备中的 Handle |
| 写特征值一定有响应 | `Write Without Response` 没有 ATT 响应，适合对吞吐/延迟敏感的场景 |

---

## 七、学习与实战检查

完成本专题后，应能独立回答并实现：

- [ ] 画出一个“手机读取手环电量”的 GAP 与 GATT 时序。
- [ ] 为温湿度传感器设计一个 Service 和两个 Characteristic，并说明各自 UUID、数据格式和 Properties。
- [ ] 解释 Client 写 CCCD 后，Server 如何通过 Notify 主动上传数据。
- [ ] 说明默认 ATT MTU 为何会让单包常见有效载荷只有 20 字节。
- [ ] 设计自定义 UART 服务的分包格式，至少包含长度、命令字与校验字段。

相关进阶专题：[BLE 低功耗设计](lowpower.md) 与 [BLE OTA 固件升级](ota.md)。
