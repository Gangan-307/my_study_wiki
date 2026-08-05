# MQTT 学习与复习笔记

> 目标：理解 MQTT 的通信模型与可靠性语义，能完成客户端接入、设备状态管理、安全配置和基础排障。

## 1. 学习路线

### 阶段 1：建立整体认识

1. 理解 MQTT 的适用场景：物联网、设备遥测、移动端推送、弱网通信。
2. 区分发布/订阅模型与 HTTP 请求/响应模型。
3. 认识 Client、Broker、Topic、发布者和订阅者。

### 阶段 2：掌握 MQTT 3.1.1 核心机制

1. Topic 层级与通配符：`+`、`#`。
2. QoS 0、1、2 的可靠性与适用边界。
3. 保留消息（Retained Message）、遗嘱消息（Will Message）。
4. 会话持久化、离线消息与 Keep Alive。
5. 客户端连接、订阅、发布、确认、断线重连的流程。

### 阶段 3：本地动手实践

1. 搭建一个 Broker：Mosquitto 适合入门，EMQX 适合学习生产能力。
2. 通过命令行完成发布、订阅、通配符订阅和不同 QoS 的实验。
3. 用一门常用语言实现发布端与订阅端。
4. 模拟网络断开、重复投递、客户端重启和 Broker 重启。

### 阶段 4：工程化与 MQTT 5.0

1. TLS、认证、ACL 授权与 Topic 隔离。
2. 消息幂等、重试、死信、限流、监控与告警。
3. MQTT 5.0 的消息过期、会话过期、共享订阅、请求/响应和原因码。
4. 完成一个设备遥测与远程控制小项目。

---

## 2. MQTT 是什么

MQTT（Message Queuing Telemetry Transport）是一种轻量级的发布/订阅消息协议。它通过 Broker 解耦消息生产者与消费者，报文小、连接开销低，适合带宽有限、网络不稳定或设备资源受限的环境。

### 2.1 核心角色

| 角色 | 职责 |
| --- | --- |
| Client（客户端） | 连接 Broker，可以发布、订阅，也可以同时做两者。 |
| Broker（代理服务器） | 接收消息，根据 Topic 与订阅关系转发，并负责认证、授权、会话等。 |
| Publisher（发布者） | 向指定 Topic 发送消息的客户端。 |
| Subscriber（订阅者） | 订阅 Topic 并接收匹配消息的客户端。 |
| Topic（主题） | 消息分类和路由依据，采用层级字符串。 |

通信关系：

```text
温度传感器 -- 发布 --> MQTT Broker -- 转发 --> App / 数据库服务 / 告警服务
```

发布者不需要知道谁会消费消息；订阅者也不需要知道消息来自哪个具体发布者。

### 2.2 MQTT 与 HTTP 对比

| 对比项 | MQTT | HTTP |
| --- | --- | --- |
| 通信模型 | 发布/订阅 | 请求/响应 |
| 连接关系 | 客户端与 Broker 保持长连接 | 常见为短连接或请求式长连接 |
| 消息分发 | 一对多、多对多 | 通常一对一 |
| 协议开销 | 小，适合嵌入式设备 | 相对较高 |
| 推送能力 | 原生支持 | 通常需轮询、SSE 或 WebSocket |
| 典型用途 | IoT、遥测、事件分发 | Web API、资源访问 |

MQTT 并不替代 HTTP：配置管理、查询历史数据等请求式交互常仍使用 HTTP；实时状态和事件分发则适合 MQTT。

---

## 3. Topic 设计与通配符

Topic 是 UTF-8 字符串，通常用 `/` 表示业务层级。`/` 没有文件系统语义，只是命名约定。

```text
home/bedroom/temperature
factory/shanghai/line-1/machine-3/status
```

推荐按稳定的领域结构设计：

```text
{业务}/{区域}/{设备类型}/{设备ID}/{消息类型}
```

例如：

```text
iot/shanghai/sensor/temp-001/telemetry
iot/shanghai/sensor/temp-001/command
iot/shanghai/sensor/temp-001/status
```

### 3.1 通配符

通配符仅能用于**订阅**，不能用于发布。

| 通配符 | 含义 | 示例 |
| --- | --- | --- |
| `+` | 匹配一个层级 | `home/+/temperature` 可匹配 `home/bedroom/temperature`。 |
| `#` | 匹配当前层级及任意后续层级，只能放在末尾 | `home/#` 可匹配 `home/bedroom/temperature`。 |

### 3.2 设计原则

- 区分数据类型：遥测 `telemetry`、状态 `status`、事件 `event`、命令 `command`。
- 标识符保持稳定，不把经常变化的内容放入层级结构。
- 不要把密码、令牌、用户隐私等敏感信息写入 Topic。
- 预先考虑 ACL；设备通常只能访问自身设备 ID 对应的 Topic。
- 避免使用过宽的 `#` 订阅，尤其在生产环境中。

---

## 4. QoS：消息交付等级

QoS（Quality of Service）控制发布者到 Broker、Broker 到订阅者两个方向的投递保证。端到端实际生效的等级受发布 QoS 和订阅 QoS 中较低者限制。

| QoS | 语义 | 特点 | 典型场景 |
| --- | --- | --- | --- |
| 0 | 至多一次（At most once） | 不确认、不重传，可能丢失 | 高频传感器数据、可容忍丢失的实时状态 |
| 1 | 至少一次（At least once） | 有确认和重传，可能重复 | 告警、业务事件、设备命令 |
| 2 | 恰好一次（Exactly once） | 多轮握手，开销最大 | 极少数不能丢也不应重复的消息 |

### 4.1 QoS 1 为什么会重复

QoS 1 的发送方未收到确认时会重发。可能出现“接收方已处理消息，但确认包在网络中丢失”的情况，此时接收方会再次收到同一消息。

因此：**QoS 1 不是业务层的恰好一次，消费端必须保证幂等。**

常见做法是在 Payload 中携带唯一消息 ID：

```json
{
  "messageId": "8c8f0d18-1f8a-4d18-a404-05f67601be5f",
  "deviceId": "temp-001",
  "timestamp": "2026-08-05T10:00:00+08:00",
  "temperature": 26.4
}
```

消费者以 `messageId` 去重，或将“写入数据”和“记录已消费 ID”置于同一事务中。

### 4.2 QoS 选择原则

- 优先选择满足业务要求的最低 QoS，QoS 越高，网络、存储和处理开销越大。
- QoS 0 接受丢失，适合下一条数据会覆盖上一条数据的场景。
- QoS 1 是多数关键事件的常用选择，但必须做好幂等。
- QoS 2 不应被当成解决全部可靠性问题的默认方案；它不能代替业务事务、去重和异常恢复设计。

---

## 5. Retain、Will 与设备状态

### 5.1 保留消息（Retained Message）

发布消息时设置 `retain=true`，Broker 会保存该 Topic 的最后一条保留消息。新的订阅者订阅该 Topic 后，会立即收到这条消息。

适合：当前温度、当前开关状态、设备在线状态、最新配置。

不适合：一次性命令、支付事件、聊天消息等历史事件。

示例：

```text
Topic: iot/devices/temp-001/status
Payload: {"online": true}
Retain: true
```

清除某个保留消息：向同一 Topic 发布**空 Payload**且 `retain=true`。

### 5.2 遗嘱消息（Will Message / LWT）

客户端连接时可预先告诉 Broker：如果我未经正常断开就失联，请代我发布某条消息。网络中断、断电或进程崩溃时，Broker 会在判定连接失效后发布它。

设备在线状态的常用模式：

```text
连接时设置 Will：
  Topic: iot/devices/temp-001/status
  Payload: {"online": false}
  Retain: true

设备成功上线后主动发布：
  Topic: iot/devices/temp-001/status
  Payload: {"online": true}
  Retain: true
```

这样无论设备正常工作还是异常失联，管理端订阅状态 Topic 都能获得当前状态。

---

## 6. 会话、离线消息与心跳

### 6.1 会话（Session）

持久会话可使客户端断线后保留订阅关系，并在其离线期间缓存符合条件的 QoS 1 / QoS 2 消息，待重连后继续投递。

需要注意：

- 持久会话不是无限容量的离线消息队列。
- Broker 往往配置会话过期、队列长度和缓存大小限制。
- 不再使用的设备应主动清理会话，否则会占用 Broker 资源。
- MQTT 3.1.1 常通过 `Clean Session` 控制；MQTT 5.0 使用 `Clean Start` 和会话过期时间，语义更灵活。

### 6.2 Keep Alive

Keep Alive 是客户端与 Broker 之间的保活间隔。客户端需要在该时间窗口内发送任意 MQTT 控制报文；空闲时会发送 `PINGREQ`，Broker 以 `PINGRESP` 回应。

作用：

- 发现断线。
- 防止 NAT 或防火墙回收空闲连接。
- 触发遗嘱消息的发布。

常见配置为 30 到 120 秒。间隔越短，断线发现越快，但耗电和网络开销越高。

---

## 7. 常见报文与通信流程

常用控制报文：

| 报文 | 作用 |
| --- | --- |
| `CONNECT` / `CONNACK` | 建立 MQTT 连接及返回连接结果。 |
| `PUBLISH` | 发布应用消息。 |
| `SUBSCRIBE` / `SUBACK` | 订阅主题及确认订阅结果。 |
| `UNSUBSCRIBE` / `UNSUBACK` | 取消订阅及确认。 |
| `PUBACK` | QoS 1 消息确认。 |
| `PUBREC`、`PUBREL`、`PUBCOMP` | QoS 2 的完整确认流程。 |
| `PINGREQ` / `PINGRESP` | 心跳保活。 |
| `DISCONNECT` | 正常断开连接。 |

QoS 1 发布流程：

```text
发布者                  Broker                  订阅者
  | ---- PUBLISH ----->   |                         |
  | <---- PUBACK -------  |                         |
  |                       | ---- PUBLISH ------->  |
  |                       | <---- PUBACK --------  |
```

QoS 2 会在每一段链路中使用 `PUBLISH -> PUBREC -> PUBREL -> PUBCOMP` 四步握手。

---

## 8. 客户端开发要点

一个完整 MQTT 客户端通常包含：

```text
加载配置 -> 建立 TLS 连接 -> 身份认证 -> 订阅主题
    -> 接收并校验消息 -> 业务处理/入队 -> 发布结果
    -> 断线重连 -> 恢复订阅或持久会话 -> 优雅退出
```

### 8.1 消费端原则

- 校验 Payload 格式、字段类型、设备 ID 和数据范围。
- QoS 1 消息按可能重复来处理，业务必须幂等。
- 回调函数应尽快返回；耗时数据库操作、文件操作或外部调用交给内部队列或异步任务。
- 记录 Topic、客户端 ID、消息 ID、时间和处理结果，方便排障。
- 对无法处理的异常消息设置告警或死信处理机制，避免无限重试。

### 8.2 发布端原则

- 使用稳定且唯一的 `clientId`；相同 `clientId` 的新连接通常会踢掉旧连接。
- 按业务重要性选择 QoS 与是否 Retain。
- 网络断开时采用退避重连，避免大量设备同时快速重连压垮 Broker。
- 命令类消息应包含命令 ID、时间戳和必要的有效期，设备应回复执行结果。

### 8.3 Payload 格式

入门常用 JSON，便于调试：

```json
{
  "messageId": "fca4db5e-9c7a-4f56-8996-5ec9d7eaf3d1",
  "timestamp": "2026-08-05T10:00:00+08:00",
  "type": "telemetry",
  "data": {
    "temperature": 26.4,
    "humidity": 58.2
  }
}
```

当带宽、存储或性能要求更高时，可评估 Protobuf、CBOR 等二进制编码。无论格式如何，都应定义版本策略，避免字段演进导致新旧设备互不兼容。

---

## 9. MQTT 5.0 重点

MQTT 5.0 在 MQTT 3.1.1 的基础上增强了可观测性、流控和消息生命周期管理。

| 能力 | 说明 |
| --- | --- |
| Reason Code | 为连接、订阅、发布失败提供明确原因。 |
| Session Expiry Interval | 精确控制会话保留多久。 |
| Message Expiry Interval | 消息过期后不再投递，适合有时效性的命令。 |
| User Properties | 携带自定义键值元数据。 |
| Response Topic + Correlation Data | 支持请求/响应关联。 |
| Shared Subscription | 多个消费者分摊同一订阅的消息。 |
| Topic Alias | 用短别名减少重复 Topic 名的传输量。 |
| Receive Maximum | 限制未确认消息数量，实现流控。 |

共享订阅格式：

```text
$share/{组名}/{实际过滤器}
$share/order-workers/orders/created
```

同一组内的多个消费者会分摊消息；一条消息通常只交给其中一个组成员。适合横向扩展订单处理、数据入库等服务。

---

## 10. 安全与生产实践

生产环境不要使用匿名、明文、全 Topic 可访问的 MQTT 服务。

### 10.1 基本安全要求

- 使用 TLS 加密传输，常见端口为 `8883`。
- 使用用户名密码、JWT 或双向 TLS 客户端证书进行认证。
- 通过 ACL 限制发布和订阅权限。
- 每个设备使用独立身份凭据，泄露后可单独吊销。
- 限制连接数、单客户端速率、报文大小和离线队列，防止资源耗尽。
- 不在 Topic 或 Payload 中传输密码、访问令牌等敏感信息。

设备 `temp-001` 的最小权限示例：

```text
允许发布：iot/devices/temp-001/telemetry
允许发布：iot/devices/temp-001/status
允许订阅：iot/devices/temp-001/command
拒绝访问：iot/devices/+/...
```

### 10.2 可观测性

至少监控：

- 在线连接数、连接失败数、认证失败数。
- 每秒发布/订阅吞吐、积压队列长度、丢弃消息数。
- 客户端频繁重连、Keep Alive 超时、遗嘱消息触发次数。
- 单个 Topic 或客户端的异常流量。
- Broker CPU、内存、磁盘与网络使用量。

---

## 11. 本地实验

以 Mosquitto 为例，先在一个终端订阅：

```bash
mosquitto_sub -h localhost -t 'study/mqtt/#' -v
```

在另一个终端发布：

```bash
mosquitto_pub -h localhost -t 'study/mqtt/hello' -m 'hello mqtt'
```

建议依次实验：

1. 将发布和订阅 QoS 分别改为 0、1、2，观察确认与重发。
2. 使用 `-r` 发布保留消息，重启订阅端后观察是否立即收到最后状态。
3. 让客户端异常退出，观察遗嘱消息是否发布。
4. 使用持久会话后让订阅端离线，再发布 QoS 1 消息，观察重连后的投递。
5. 使用 `+`、`#` 测试 Topic 匹配范围。

---

## 12. 练习项目：智能环境监控

### 12.1 Topic 约定

```text
iot/devices/{deviceId}/telemetry  # 温湿度等遥测数据
iot/devices/{deviceId}/status     # 在线、离线和当前状态，使用 Retain
iot/devices/{deviceId}/command    # 服务端下发命令
iot/devices/{deviceId}/event      # 告警与设备事件
```

### 12.2 功能拆分

| 组件 | 工作内容 |
| --- | --- |
| 模拟传感器 | 周期发布温湿度；连接时设置遗嘱；上线时发布 retained 状态。 |
| 数据服务 | 订阅 `telemetry`，校验并存储数据，按阈值生成告警。 |
| 命令服务 | 向 `command` 发布采样间隔等指令，关联命令 ID 与执行结果。 |
| 管理端 | 订阅 `status`、`telemetry`、`event`，展示实时数据和在线状态。 |

完成项目后应能解释：

- QoS 1 为什么仍需幂等？
- Retain 与离线消息有什么区别？
- 如何判断设备异常离线？
- 如何限制设备只能访问自己的 Topic？
- 如何让多个服务实例分摊消息？
- 为什么不能在消息回调中直接执行耗时任务？

---

## 13. 高频复习题

1. MQTT 中发布者与订阅者为什么不需要互相感知？
2. `+` 和 `#` 的匹配范围分别是什么？
3. QoS 0、1、2 的语义和代价是什么？
4. 为什么 QoS 1 下消费者必须做幂等？
5. 什么消息适合设置 Retain？什么消息不适合？
6. 遗嘱消息如何配合 Retain 实现在线状态？
7. 持久会话解决什么问题？为什么仍要限制其生命周期？
8. Keep Alive 的作用是什么？
9. MQTT 5.0 的共享订阅适用于什么场景？
10. 生产 MQTT 服务最低限度应具备哪些安全措施？

## 14. 一页速记

```text
MQTT = 轻量级发布/订阅协议，Broker 负责路由和解耦。
Topic = 分层消息路径；+ 匹配一层，# 匹配多层且只能在末尾。
QoS 0 = 至多一次；QoS 1 = 至少一次、可能重复；QoS 2 = 恰好一次、开销最大。
Retain = 给后来订阅者最后状态；Will = 异常掉线时 Broker 代发消息。
持久会话 = 保留订阅及部分离线消息；Keep Alive = 保活和断线检测。
生产环境 = TLS + 独立认证 + ACL + 限流 + 监控 + 业务幂等。
```
