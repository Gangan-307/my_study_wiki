# ESPC2-M1 PHY 校准现场操作指南

**版本**：V1.0

**日期**：2026-08-25

**适用对象**：ESPC2-M1 / ESP8684H（ESP32-C2）故障分析样品

## 1. 目的与结论边界

本指南用于对 ESPC2-M1（ESP8684H / ESP32-C2）弱信号 RSSI 异常样品进行：

1. 首份 Flash、NVS 和 PHY 校准数据留证；
2. 三板对照 RF 基线测试；
3. 多次冷启动后的 PHY 数据变化验证；
4. 更新后的稳定性和 RF 效果复测；
5. 判断是否需要进入受控强制重校准或硬件 FA。

本次 F1 镜像证据只证明：首份备份与操作人员记录的六次冷启动后快照之间，`phy:cal_data` 已发生变化；随后再冷启动一次取得的快照仍保持相同。现场初步观察为样品弱信号表现恢复至接近良品，RF 原始记录仍待归档。由于六次循环之间没有逐次回读，现有证据不能确定数据在第几次启动变化，也不能排除期间变化过多次。实验没有主动擦除 `phy` 命名空间，也没有抓到可读的 `phy_init` 启动日志，因此不能把本次操作写成“已经执行受控 FULL 重校准”。

第 4~10 节的 esptool 操作均为读取，不主动写 Flash；但第 8~10 节正常启动客户应用时，应用和 PHY 仍可能自行改写 NVS，所以首份双备份必须先完成。

正式结论应分三层：

| 层级 | 当前可写结论 |
|---|---|
| 现象 | 现场初步观察为故障随模组移动，原故障样品在弱信号下比良品低 20 dB 以上；待 RF 原始记录归档后才能升级为正式证据 |
| 直接原因 | 尚未确认；PHY 数据变化与弱信号表现改善同时出现，形成了相关性线索。要确认直接因果，仍需同一模组旧数据/新数据 A/B/A/B 可逆复现 |
| 根本原因 | 原异常数据为何形成尚未确认，需继续查首次校准时的 3V3/EN 时序、校准环境、OTA/PHY 版本变化和固件 NVS 处理逻辑 |

> RSSI 指示差异不自动等于实际射频链路衰减。必须同时比较丢包率、吞吐量或断开门限中的至少一项，才能判断实际通信性能是否同步下降。

---

## 2. 红线与停手条件

### 2.1 禁止作为现场常规操作

- 禁止执行 `erase-flash`；
- 禁止按固定地址擦除整个 NVS；
- 禁止擦除 `phy_init` 分区；`phy_init@0xF000` 与 NVS 内的 `phy` 命名空间不是一回事；
- 禁止修改 eFuse 或 MAC；
- 禁止手工翻转字节制造校验错误；
- 禁止把一块模组的完整镜像或 NVS 写入另一块模组；
- 禁止给基准良品烧写、擦除或重校准；
- 禁止在未取得原客户源码、补丁和 `sdkconfig` 时，用其他 IDF 版本编译的工装宣称“等效重校准”。

### 2.2 出现以下任一情况立即停止

- `SPI_BOOT_CRYPT_CNT` 非 `000` 或 `SECURE_BOOT_EN=True`；
- `DIS_DOWNLOAD_MODE=True`、`ENABLE_SECURITY_DOWNLOAD=True` 或 `RD_DIS` 非 `0`；
- 两次完整 Flash 备份大小不对、SHA256 不一致或逐字节比较不一致；
- NVS 无法通过完整性检查，或无法确认哪个分区是应用实际使用的 `nvs`；
- EN/FEN、GPIO8/IO9 启动状态或供电方式无法确认；
- 写后回读结果与预期镜像哈希不一致；
- PHY 数据每次冷启动都变化，或重校结果自身离散超过约 5 dB；
- 数据更新后 RF 无改善或变化无规律，应转入天线、匹配、焊点、LNA/PA/ESD 等硬件 FA。

### 2.3 未处理故障样品的保护

任何焊接、拆焊、按压、加热或写入前，先完成板号/外观/天线区域/接线状态照片和必要的 X-ray，保留原始物理状态。飞线优先接板端测试点或使用弹簧针，不在模组邮票孔反复焊接。

第二块尚未处理的故障样品，首次接电前先按住 BOOT，使其直接进入 ROM 下载模式并完成双备份。不要先正常启动应用，否则应用可能在取证前改写待留证的 PHY 数据。

完整 Flash/NVS 可能包含 Wi-Fi 密码、证书和设备密钥，只能存放在受控内部目录。对客户只提供 MAC、版本、长度和 SHA256 摘要，不提供原始镜像。

首次整片读取前必须取得客户或项目负责人书面授权，并登记样品编号、MAC、操作人、读取时间、两份备份的保管位置和访问权限。

### 2.4 失败重试与证据不覆盖

- G0、完整备份或首份切片一旦已经产生任何文件，后续命令又失败，不删除、不改名、不覆盖已有文件；将该目录登记为失败尝试，并以同一物理样品的新尝试号（例如 `F1-A02`）建立新工单；
- 快照在 MAC 校验通过前不会创建正式文件。MAC 通过后若 NVS 读取、完整性或摘要步骤失败，保留该 Tag 的全部文件，用新 Tag（例如 `S0-pre-attempt02`）重试，并在记录中说明最终采用哪一个成功 Tag；
- 不把失败尝试中的局部文件拼接到成功工单中，也不通过删除失败文件使目录看起来像一次通过。

---

## 3. 所需工具与接线

### 3.1 硬件

- 安装 Python 和 esptool 的 Windows 接线电脑；所有读写命令均在这台电脑执行，不是在仅连接模组热点的电脑上执行；
- 3.3 V 逻辑电平 USB-TTL；
- 产品原供电或稳定电源，按产品正常电源路径供电；
- 万用表；正式受控测试必须使用双通道示波器同时记录模组 3V3 和 EN/FEN；
- 非金属支架、固定位置标记、固定信道的 2.4 GHz AP；
- 相机或手机，用于接线、板号、位置及测试过程留证。

### 3.2 UART 接线

| ESPC2-M1 | USB-TTL |
|---|---|
| Pin14 TX0 | RXD |
| Pin13 RX0 | TXD |
| Pin8 GND | GND |

USB-TTL 必须选择 3.3 V 逻辑电平。不要连接 USB-TTL 的 `VCC` 或 `5V`；板子仍按产品正常方式供电，只与 USB-TTL 共地。

若设备管理器只看到板载 Infineon/EZ-USB（例如 VID `04B4`、PID `1004`、Class `FF`）而没有 COM 口，它不是本次 esptool 串口；本次 COM10 来自外接 USB-TTL。若板载控制器也连接 TX0/RX0，必须确认其 UART 输出为高阻或先隔离，禁止板载控制器与 USB-TTL 两个 TX 同时驱动模组 RX0。

### 3.3 进入下载模式

以下时序仅适用于已经确认 SW2 为 BOOT/IO9、SW3 为 EN/RST 的当前板。

**断电直进 ROM：所有备份和状态快照均使用此时序**

1. 板子保持断电；
2. 先按住 SW2；
3. 在 SW2 保持按下的状态接通产品电源；
4. 等待约 1 秒后松开 SW2；
5. 不按 SW3，立即执行 esptool 命令。

这样上电后直接进入 ROM 下载模式，不启动客户应用。首份备份、S0/S1 的 pre/post、P1-run 和 P1-check 等所有用于证明“启动前后状态”的快照，都必须使用这套时序。若底板不能用该方式进入下载模式，应在断电状态使用经确认的 IO9 下拉方案或自动下载电路；不能先让应用正常启动，再补做状态快照。

**运行中按键进入 ROM：仅用于连线调试，不用于状态快照**

1. 板子正常供电；
2. 按住 SW2；
3. 点按并松开 SW3；
4. 等待约 1 秒；
5. 松开 SW2；
6. 立即执行 esptool 命令。

这套时序会先让应用运行，可能改写 NVS，因此禁止用于首份备份以及任何 pre/post 快照。它只适合已经完成取证后的串口连接调试。

如果换了底板版本，必须重新确认 SW2/SW3 定义及 IO8 状态。ESP32-C2 下载模式要求 IO9 为低且 IO8 为高，不能把上述按键动作当成所有底板的通用接法。

退出下载模式：松开 SW2，在不按 SW2 的情况下断电重上电。需要“冷启动”时必须整板断电至少 5 秒，不用 SW3 软复位代替。

---

## 4. 建立工单目录和变量

在接线电脑上打开 Windows PowerShell。以下示例为已验证的 F1 样品；处理新样品时必须修改 `$Sample`、`$Port` 和 `$ExpectedMac`。`$ExpectedMac` 应来自收样记录或板上标签，第 5 节会与芯片实际基础 MAC 机读核对，不能使用 AP BSSID。

```powershell
Set-StrictMode -Version 3.0
$ErrorActionPreference = 'Stop'

$Sample = "F1"
$Port = "COM10"
$ExpectedMac = "8c:8c:29:55:5a:dc"
$CaseRoot = "C:\ESPC2_FA\$Sample"
$CaseRootWsl = "/mnt/c/ESPC2_FA/$Sample"
$CreateNewCase = $true  # 新工单用 $true；续作已存在工单时明确改为 $false
$ResumeManifestTag = 'G-PARSE'  # 续作时改为上一已完成阶段
$ResumeMirrorBase = 'E:\ESPC2_FA_MIRROR'  # 续作时改为批准的第二存储
$ApprovedResumeManifestSha256 = '填写工单系统中批准的64位SHA256'
$WslExe = "$env:SystemRoot\System32\wsl.exe"

$IdfRootWsl = "/home/lichen/.espressif/v5.5.5/esp-idf"
$GenPartWsl = "$IdfRootWsl/components/partition_table/gen_esp32part.py"
$NvsParserDirWsl = "$IdfRootWsl/components/nvs_flash/nvs_partition_tool"
$NvsToolWsl = "$NvsParserDirWsl/nvs_tool.py"
$PhySummaryWsl = "/mnt/d/用户/lichen/desktop/my_study_wiki/tools/espc2-fa/phy_nvs_summary.py"
$PhySummaryWin = "D:\用户\lichen\Desktop\my_study_wiki\tools\espc2-fa\phy_nvs_summary.py"
$PhyHelpersWin = "D:\用户\lichen\Desktop\my_study_wiki\tools\espc2-fa\PhyFaHelpers.ps1"

if ($CreateNewCase) {
  if (Test-Path -LiteralPath $CaseRoot) {
    throw "新工单目录已存在，禁止覆盖：$CaseRoot"
  }
  New-Item -ItemType Directory -Path @(
    "$CaseRoot\00_backup",
    "$CaseRoot\01_ptable",
    "$CaseRoot\02_idfver",
    "$CaseRoot\03_P1",
    "$CaseRoot\08_measure"
  ) | Out-Null
} elseif (-not (Test-Path -LiteralPath $CaseRoot)) {
  throw "续作工单不存在：$CaseRoot"
}

Set-Location "$CaseRoot\00_backup"
if (-not (Test-Path -LiteralPath $WslExe)) { throw "找不到 wsl.exe" }
py --version
py -m esptool version
Get-CimInstance Win32_SerialPort | Select-Object DeviceID,Name
& $WslExe python3 --version

& $WslExe test -f "$GenPartWsl"
if ($LASTEXITCODE -ne 0) { throw "找不到 gen_esp32part.py" }
& $WslExe test -f "$NvsToolWsl"
if ($LASTEXITCODE -ne 0) { throw "找不到 nvs_tool.py" }
& $WslExe test -f "$NvsParserDirWsl/nvs_parser.py"
if ($LASTEXITCODE -ne 0) { throw "找不到 nvs_parser.py" }
& $WslExe test -f "$NvsParserDirWsl/nvs_check.py"
if ($LASTEXITCODE -ne 0) { throw "找不到 nvs_check.py" }
& $WslExe test -f "$NvsParserDirWsl/nvs_logger.py"
if ($LASTEXITCODE -ne 0) { throw "找不到 nvs_logger.py" }
& $WslExe test -f "$PhySummaryWsl"
if ($LASTEXITCODE -ne 0) { throw "找不到 phy_nvs_summary.py" }
if (-not (Test-Path -LiteralPath $PhyHelpersWin)) {
  throw "找不到 PhyFaHelpers.ps1"
}
$ApprovedPhySummarySha256 = `
  "9B1EDA3159FF16C6C027DEC6C85FCDC15B627372E5E4C5931588766C73401C17"
$actualPhySummarySha256 = `
  (Get-FileHash -LiteralPath $PhySummaryWin -Algorithm SHA256).Hash
if ($actualPhySummarySha256 -ne $ApprovedPhySummarySha256) {
  throw "phy_nvs_summary.py 与本指南批准版本不一致，停止"
}
$ApprovedHelperSha256 = `
  "13E040C877FC009AD287E806CDD76789A56859C19B187829B16562E84B322382"
$actualHelperSha256 = `
  (Get-FileHash -LiteralPath $PhyHelpersWin -Algorithm SHA256).Hash
if ($actualHelperSha256 -ne $ApprovedHelperSha256) {
  throw "PhyFaHelpers.ps1 与本指南批准版本不一致，停止"
}
Get-ExecutionPolicy -List
. $PhyHelpersWin
```

预期为 `esptool v5.3.1`。本文统一使用 v5 的连字符命令，例如 `flash-id`、`read-mac`、`read-flash` 和 `image-info`。

后续步骤默认始终使用同一个 PowerShell 窗口。`PhyFaHelpers.ps1` 提供证据防覆盖、切片、NVS 检查、上下文恢复、身份确认和快照函数。若要续作已经存在的 F1 工单，将 `$CreateNewCase` 明确改为 `$false` 后执行本节，再按第 7.5 节用一条命令恢复全部样品变量。所有证据输出均设为同名文件存在即停止，续作时从尚未完成的新 Tag 继续。

如果点加载脚本时提示“系统禁止运行脚本”，不要修改 `LocalMachine` 或 `CurrentUser` 执行策略。先确认上面的 SHA256 校验已经通过并取得项目负责人/IT 批准；只有 `MachinePolicy` 和 `UserPolicy` 均为 `Undefined` 时，才可在当前 PowerShell 窗口临时放行，然后重新加载。关闭窗口后该设置自动失效：

```powershell
if ((Get-ExecutionPolicy -Scope MachinePolicy) -ne 'Undefined' -or
    (Get-ExecutionPolicy -Scope UserPolicy) -ne 'Undefined') {
  throw "存在组织级执行策略，停止并联系 IT"
}
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass -Force
if ((Get-ExecutionPolicy) -ne 'Bypass') { throw "当前进程未成功临时放行" }
. $PhyHelpersWin
```

若出现 `No module named esptool`，在接线电脑联网并获准安装后执行：

```powershell
py -m pip install esptool==5.3.1
```

依赖安装完成且助手已成功加载后，执行下列工具链锁定。它把 Windows/WSL Python、esptool、IDF commit，以及实际参与解析的 7 个脚本 SHA256 写入工单。新工单自动创建；续作时必须与原记录逐行一致。早期 F1 工单没有这份记录，只有在项目负责人完成现有证据人工复核并批准“遗留工单建锚”后，才可把 `$ApproveLegacyToolchainBootstrap` 改为 `$true`；批准编号和生成后的文件哈希必须记入工单系统。

```powershell
$ApproveLegacyToolchainBootstrap = $false
$toolchainPath = "$CaseRoot\00_backup\$Sample-toolchain.txt"

function Get-WslFileSha256 {
  param([Parameter(Mandatory=$true)][string]$Path)
  $output = @(& $WslExe sha256sum -- "$Path" 2>&1)
  $exitCode = $LASTEXITCODE
  if ($exitCode -ne 0) { throw "WSL SHA256 失败：$Path" }
  $hashes = @($output | ForEach-Object {
    $match = [regex]::Match($_.ToString(), '(?i)^([0-9a-f]{64})\s')
    if ($match.Success) { $match.Groups[1].Value.ToUpperInvariant() }
  })
  if ($hashes.Count -ne 1) { throw "无法唯一解析 WSL SHA256：$Path" }
  return $hashes[0]
}

$windowsPythonOutput = @(py --version 2>&1)
$windowsPythonExit = $LASTEXITCODE
if ($windowsPythonExit -ne 0) { throw "Windows Python 版本读取失败" }
$esptoolOutput = @(py -m esptool version 2>&1)
$esptoolExit = $LASTEXITCODE
if ($esptoolExit -ne 0) { throw "esptool 版本读取失败" }
$wslPythonOutput = @(& $WslExe python3 --version 2>&1)
$wslPythonExit = $LASTEXITCODE
if ($wslPythonExit -ne 0) { throw "WSL Python 版本读取失败" }
$idfCommitOutput = @(& $WslExe git -C "$IdfRootWsl" rev-parse HEAD 2>&1)
$idfCommitExit = $LASTEXITCODE
if ($idfCommitExit -ne 0) { throw "IDF commit 读取失败" }
$idfCommits = @($idfCommitOutput | ForEach-Object {
  if ($_.ToString().Trim() -match '^[0-9a-fA-F]{40}$') {
    $_.ToString().Trim().ToUpperInvariant()
  }
} | Sort-Object -Unique)
if ($idfCommits.Count -ne 1) { throw "无法唯一解析 IDF commit" }

$toolchainLines = @(
  "powershell=$($PSVersionTable.PSVersion.ToString())"
  "windows_python=$(($windowsPythonOutput -join ' ').Trim())"
  "esptool=$(($esptoolOutput -join ' ').Trim())"
  "wsl_python=$(($wslPythonOutput -join ' ').Trim())"
  "idf_commit=$($idfCommits[0])"
  "helper_sha256=$((Get-FileHash $PhyHelpersWin -Algorithm SHA256).Hash)"
  "phy_summary_sha256=$((Get-FileHash $PhySummaryWin -Algorithm SHA256).Hash)"
  "gen_esp32part_sha256=$(Get-WslFileSha256 $GenPartWsl)"
  "nvs_tool_sha256=$(Get-WslFileSha256 $NvsToolWsl)"
  "nvs_parser_sha256=$(Get-WslFileSha256 "$NvsParserDirWsl/nvs_parser.py")"
  "nvs_check_sha256=$(Get-WslFileSha256 "$NvsParserDirWsl/nvs_check.py")"
  "nvs_logger_sha256=$(Get-WslFileSha256 "$NvsParserDirWsl/nvs_logger.py")"
)

if (Test-Path -LiteralPath $toolchainPath) {
  $recordedToolchain = @(Get-Content -LiteralPath $toolchainPath -Encoding UTF8)
  if (@(Compare-Object $recordedToolchain $toolchainLines -SyncWindow 0).Count -ne 0) {
    throw "当前工具链与工单锁定记录不同，停止"
  }
} else {
  if ((-not $CreateNewCase) -and (-not $ApproveLegacyToolchainBootstrap)) {
    throw "遗留工单缺少工具链记录；未经批准不得建锚"
  }
  $utf8NoBom = New-Object -TypeName Text.UTF8Encoding -ArgumentList $false
  [IO.File]::WriteAllLines($toolchainPath,$toolchainLines,$utf8NoBom)
}
$toolchainLines
Get-FileHash -LiteralPath $toolchainPath -Algorithm SHA256
```

续作工单在执行第 5 节或任何样品读取前，还必须通过上一阶段锚点。正常续作保持 `$ApproveLegacyToolchainBootstrap=$false`，执行：

```powershell
if (-not $CreateNewCase) {
  if ($ApproveLegacyToolchainBootstrap) {
    Write-Warning "遗留工单处于获批建锚窗口；建立首个 G-PARSE 锚点后立即改回 false"
  } else {
    $resumeManifestRelativePath = `
      "00_backup\$Sample-$ResumeManifestTag-manifest.sha256"
    $resumeMirrorCase = `
      Join-Path $ResumeMirrorBase "$Sample-$ResumeManifestTag"
    Assert-CaseCheckpoint `
      -CaseRoot $CaseRoot `
      -MirrorCase $resumeMirrorCase `
      -ManifestRelativePath $resumeManifestRelativePath `
      -ApprovedManifestSha256 $ApprovedResumeManifestSha256 | Format-List
  }
}
```

正常续作未显示 `FilesVerified` 即不得继续。遗留建锚属于一次性例外，只允许完成已有证据复核、缺失派生文件生成和首个 `G-PARSE` 清单；期间禁止正常启动样品、写 Flash 或作根因结论。

> Windows PowerShell 5.1 的 `Tee-Object` 通常把文本保存为 UTF-16LE。WSL 中直接 `cat` 时看起来像乱码，但文件并未损坏；用记事本、PowerShell `Get-Content` 或 VS Code 打开即可。需要 UTF-8 副本时执行：`Get-Content .\原日志.txt | Set-Content .\UTF8日志.txt -Encoding UTF8`。

---

## 5. G0：身份和安全检查

按 3.3 节进入下载模式，然后执行：

```powershell
$g0Evidence = @(
  ".\efuse_summary.txt",
  ".\flash_id.txt",
  ".\read_mac.txt"
)
Assert-NewEvidencePaths -Paths $g0Evidence

py -m espefuse --chip esp32c2 --port $Port --baud 115200 `
  --before no-reset --after no-reset summary 2>&1 |
  Tee-Object ".\efuse_summary.txt"
if ($LASTEXITCODE -ne 0) { throw "eFuse 读取失败，停止" }

py -m esptool --chip esp32c2 --port $Port --baud 115200 `
  --before no-reset --after no-reset flash-id 2>&1 |
  Tee-Object ".\flash_id.txt"
if ($LASTEXITCODE -ne 0) { throw "flash-id 失败，停止" }

py -m esptool --chip esp32c2 --port $Port --baud 115200 `
  --before no-reset --after no-reset read-mac 2>&1 |
  Tee-Object ".\read_mac.txt"
if ($LASTEXITCODE -ne 0) { throw "read-mac 失败，停止" }
```

新工单完成上述读取后执行下列机读校验。续作工单不得重跑并覆盖 G0 日志，直接使用已有 `flash_id.txt`；当前早期 F1 工单没有单独的 `read_mac.txt`，下列代码会同时接受 `flash_id.txt` 中的基础 MAC。两个日志都存在时，其 MAC 必须一致。

```powershell
$flashIdText = Get-Content ".\flash_id.txt" -Raw
$flashMatch = [regex]::Match(
  $flashIdText,
  '(?im)^\s*Detected flash size:\s*(\d+)\s*(MB|KB)\s*$'
)
if (-not $flashMatch.Success) { throw "无法从 flash-id 解析容量，停止" }
$capacityNumber = [int64]$flashMatch.Groups[1].Value
$capacityUnit = $flashMatch.Groups[2].Value.ToUpperInvariant()
if ($capacityUnit -eq 'MB') {
  $FlashSize = $capacityNumber * 1MB
} else {
  $FlashSize = $capacityNumber * 1KB
}
if (($FlashSize % 1MB) -ne 0) { throw "Flash 容量不是整 MB，停止" }
$FlashSizeLabel = "$([int64]($FlashSize / 1MB))MB"
$supportedFlashLabels = @('1MB','2MB','4MB','8MB','16MB','32MB','64MB','128MB')
if ($FlashSizeLabel -notin $supportedFlashLabels) {
  throw "分区工具不支持容量 $FlashSizeLabel，停止"
}

$macEvidencePaths = @(@(".\read_mac.txt",".\flash_id.txt") |
  Where-Object { Test-Path -LiteralPath $_ })
if ($macEvidencePaths.Count -eq 0) { throw "没有可用的 MAC 证据日志，停止" }
$readMacText = ($macEvidencePaths | ForEach-Object {
  Get-Content -LiteralPath $_ -Raw
}) -join "`n"
$macMatches = [regex]::Matches(
  $readMacText,
  '(?im)^\s*MAC:\s*([0-9a-f]{2}(?::[0-9a-f]{2}){5})\s*$'
)
$actualMacs = @($macMatches | ForEach-Object {
  $_.Groups[1].Value.ToLowerInvariant()
} | Sort-Object -Unique)
if ($actualMacs.Count -ne 1) { throw "无法唯一解析芯片基础 MAC，停止" }
$ActualMac = $actualMacs[0]
if ($ExpectedMac -notmatch '^[0-9a-fA-F]{2}(?::[0-9a-fA-F]{2}){5}$') {
  throw "ExpectedMac 格式错误，停止"
}
if ($ActualMac -ne $ExpectedMac.ToLowerInvariant()) {
  throw "接入样品 MAC $ActualMac 与工单 MAC $ExpectedMac 不一致，停止"
}

"Detected Flash: $FlashSizeLabel ($FlashSize bytes)"
"Verified base MAC: $ActualMac"
```

任一命令提示无法连接时，先关闭占用 COM 口的串口助手，再重复 3.3 节的 SW2/SW3 时序重试；不要通过随意更换业务串口波特率解决 esptool 连接问题。

逐项确认：

| 项目 | 本次 F1 实测值 |
|---|---|
| 芯片 | ESP8684H / ESP32-C2 revision v2.0 |
| 晶振 | 26 MHz |
| Flash | 2 MB |
| MAC | `8c:8c:29:55:5a:dc` |
| `SPI_BOOT_CRYPT_CNT` | `000` / Disable |
| `SECURE_BOOT_EN` | `False` |
| `DIS_DOWNLOAD_MODE` | `False` |
| `ENABLE_SECURITY_DOWNLOAD` | `False` |
| `DIS_DOWNLOAD_MANUAL_ENCRYPT` | `False` |
| `RD_DIS` | `0` |

新样品任一安全项与本表不同，先停止并交由固件/安全工程师判断，不能照抄 F1 的后续流程。

模组基础 MAC 为 `...:dc`，设备作为 AP 时看到的 BSSID 为 `...:dd`，属于不同 Wi-Fi 接口派生地址，不是 MAC 读取错误。PHY 的 `cal_mac` 必须与 esptool 读取的基础 MAC `...:dc` 比较。

---

## 6. G-BACKUP：完整 Flash 双备份

`$FlashSize` 和 `$FlashSizeLabel` 必须由第 5 节的 `flash-id` 输出自动生成，禁止人工填写。本次 F1 解析结果应为 2 MB。

```powershell
$backupEvidence = @(
  ".\$Sample-full-A.bin",
  ".\$Sample-full-B.bin",
  ".\read-A.txt",
  ".\read-B.txt",
  ".\full-backup-sha256.txt",
  ".\full-backup-fc.txt"
)
Assert-NewEvidencePaths -Paths $backupEvidence

py -m esptool --chip esp32c2 --port $Port --baud 115200 `
  --before no-reset --after no-reset read-flash 0 ALL `
  ".\$Sample-full-A.bin" 2>&1 |
  Tee-Object ".\read-A.txt"
if ($LASTEXITCODE -ne 0) { throw "第一次完整备份失败，停止" }

py -m esptool --chip esp32c2 --port $Port --baud 115200 `
  --before no-reset --after no-reset read-flash 0 ALL `
  ".\$Sample-full-B.bin" 2>&1 |
  Tee-Object ".\read-B.txt"
if ($LASTEXITCODE -ne 0) { throw "第二次完整备份失败，停止" }

$a = Get-Item ".\$Sample-full-A.bin"
$b = Get-Item ".\$Sample-full-B.bin"
if (($a.Length -ne $FlashSize) -or ($b.Length -ne $FlashSize)) {
  throw "备份大小错误，停止"
}

$hashes = Get-FileHash ".\$Sample-full-A.bin",".\$Sample-full-B.bin" -Algorithm SHA256
$hashLines = $hashes | ForEach-Object { "$($_.Hash)  $($_.Path)" }
$hashLines | Tee-Object ".\full-backup-sha256.txt"
if ($hashes[0].Hash -ne $hashes[1].Hash) { throw "两份 SHA256 不一致，停止" }

cmd /c fc /b "$Sample-full-A.bin" "$Sample-full-B.bin" 2>&1 |
  Tee-Object ".\full-backup-fc.txt"
if ($LASTEXITCODE -ne 0) { throw "逐字节比较不一致，停止" }
```

`ALL` 让 esptool 按检测到的 Flash 容量读取整片；文件长度仍必须与独立解析出的 `$FlashSize` 交叉一致。通过条件：两个文件大小均等于 `$FlashSize`（F1 为 2,097,152 字节）、SHA256 完全相同，且 `fc /b` 显示找不到差异。把其中一份连同哈希复制到第二个受控存储位置，再继续。

`Tee-Object` 必须与要记录的命令处于同一条管道。单独再执行一行 `Tee-Object ...` 只会生成空文件，不能作为操作日志。

---

## 7. G-PARSE：离线解析分区、NVS 和应用

### 7.1 从完整备份切出区域

F1 已从客户配置和实测镜像确认分区表位于 `0x8000`、有效长度为 `0xC00`。新固件必须先从客户的 `CONFIG_PARTITION_TABLE_OFFSET`、构建产物或可信启动日志确认 `$PartitionTableOffset`，不能默认照抄 `0x8000`。

只读切片和数值转换函数已由第 4 节加载。执行：

```powershell
$PartitionTableOffset = 0x8000
$PartitionTableSize = 0xC00
$FullA = (Resolve-Path ".\$Sample-full-A.bin").Path
$ptBinPath = "$CaseRoot\01_ptable\pt.bin"
if (-not (Test-Path -LiteralPath $ptBinPath)) {
  Export-FlashRegion $FullA $PartitionTableOffset $PartitionTableSize $ptBinPath
}

$pt = [IO.File]::ReadAllBytes($ptBinPath)
if (($pt.Length -ne $PartitionTableSize) -or ($pt[0] -ne 0xAA) -or ($pt[1] -ne 0x50)) {
  throw "分区表长度或 AA-50 魔数错误，停止"
}
Assert-FlashRegionMatches -Source $FullA -Offset $PartitionTableOffset `
  -Length $PartitionTableSize -RegionFile $ptBinPath | Out-Null
```

解析实际分区表：

```powershell
$ptCsvPath = "$CaseRoot\01_ptable\pt.csv"
if (-not (Test-Path -LiteralPath $ptCsvPath)) {
  & $WslExe python3 "$GenPartWsl" --quiet --flash-size $FlashSizeLabel `
    "$CaseRootWsl/01_ptable/pt.bin" `
    "$CaseRootWsl/01_ptable/pt.csv"
  if ($LASTEXITCODE -ne 0) { throw "分区表解析失败，停止" }
}
Get-Content $ptCsvPath
Assert-PartitionCsvMatches `
  -PartitionBinWsl "$CaseRootWsl/01_ptable/pt.bin" `
  -PartitionCsvWin $ptCsvPath `
  -FlashSizeText $FlashSizeLabel `
  -GenPartWslPath $GenPartWsl
```

本次 F1 实测分区如下：

| 分区 | Offset | Size |
|---|---:|---:|
| `nvs` | `0x9000` | `0x6000` |
| `phy_init` | `0xF000` | `0x1000` |
| `factory` | `0x10000` | `0x100000` |

```powershell
$partitionLines = Get-Content "$CaseRoot\01_ptable\pt.csv" |
  Where-Object { $_.Trim() -and ($_ -notmatch '^\s*#') }
$parts = @($partitionLines | ConvertFrom-Csv `
  -Header Name,Type,SubType,Offset,Size,Flags)

$nvsParts = @($parts | Where-Object { $_.Name -eq 'nvs' -and $_.Type -eq 'data' })
$phyInitParts = @($parts | Where-Object {
  $_.Name -eq 'phy_init' -and $_.Type -eq 'data'
})
$appParts = @($parts | Where-Object { $_.Type -eq 'app' })
if ($nvsParts.Count -ne 1) { throw "未找到唯一的 nvs 分区，停止" }
if ($phyInitParts.Count -ne 1) { throw "未找到唯一的 phy_init 分区，停止" }
if ($appParts.Count -ne 1) {
  throw "存在零个或多个 App 分区，必须先确认当前实际启动 App，停止"
}

$NvsOffset = Convert-PartitionNumber $nvsParts[0].Offset
$NvsSize = Convert-PartitionNumber $nvsParts[0].Size
$PhyInitOffset = Convert-PartitionNumber $phyInitParts[0].Offset
$PhyInitSize = Convert-PartitionNumber $phyInitParts[0].Size
$AppName = $appParts[0].Name
$AppOffset = Convert-PartitionNumber $appParts[0].Offset
$AppSize = Convert-PartitionNumber $appParts[0].Size

if ($Sample -eq 'F1') {
  if (($NvsOffset -ne 0x9000) -or ($NvsSize -ne 0x6000) -or
      ($PhyInitOffset -ne 0xF000) -or ($PhyInitSize -ne 0x1000) -or
      ($AppName -ne 'factory') -or ($AppOffset -ne 0x10000) -or
      ($AppSize -ne 0x100000)) {
    throw "F1 分区与已验证基线不一致，停止"
  }
}

$parts | Format-Table Name,Type,SubType,Offset,Size

$nvsImagePath = "$CaseRoot\00_backup\$Sample-nvs.bin"
$phyInitImagePath = "$CaseRoot\02_idfver\$Sample-phy_init.bin"
$appImagePath = "$CaseRoot\02_idfver\$Sample-$AppName-app.bin"
if (-not (Test-Path -LiteralPath $nvsImagePath)) {
  Export-FlashRegion $FullA $NvsOffset $NvsSize $nvsImagePath
}
if (-not (Test-Path -LiteralPath $appImagePath)) {
  Export-FlashRegion $FullA $AppOffset $AppSize $appImagePath
}
if (-not (Test-Path -LiteralPath $phyInitImagePath)) {
  Export-FlashRegion $FullA $PhyInitOffset $PhyInitSize $phyInitImagePath
}

if ((Get-Item $nvsImagePath).Length -ne $NvsSize) { throw "已有 NVS 切片长度错误" }
if ((Get-Item $appImagePath).Length -ne $AppSize) { throw "已有 App 切片长度错误" }
if ((Get-Item $phyInitImagePath).Length -ne $PhyInitSize) {
  throw "已有 phy_init 切片长度错误"
}
Assert-FlashRegionMatches -Source $FullA -Offset $NvsOffset `
  -Length $NvsSize -RegionFile $nvsImagePath | Out-Null
Assert-FlashRegionMatches -Source $FullA -Offset $PhyInitOffset `
  -Length $PhyInitSize -RegionFile $phyInitImagePath | Out-Null
Assert-FlashRegionMatches -Source $FullA -Offset $AppOffset `
  -Length $AppSize -RegionFile $appImagePath | Out-Null
Get-Item $nvsImagePath | Select-Object Name,Length,FullName
$nvsHashPath = "$CaseRoot\00_backup\$Sample-nvs-sha256.txt"
if (-not (Test-Path -LiteralPath $nvsHashPath)) {
  Get-FileHash $nvsImagePath -Algorithm SHA256 |
    Format-List Algorithm,Hash,Path | Tee-Object $nvsHashPath
} else {
  $recordedHashText = Get-Content -LiteralPath $nvsHashPath -Raw
  $recordedHashes = @([regex]::Matches(
    $recordedHashText,
    '(?i)\b[0-9a-f]{64}\b'
  ) | ForEach-Object { $_.Value.ToUpperInvariant() } | Sort-Object -Unique)
  $currentNvsHash = (Get-FileHash -LiteralPath $nvsImagePath -Algorithm SHA256).Hash
  if (($recordedHashes.Count -ne 1) -or ($recordedHashes[0] -ne $currentNvsHash)) {
    throw "已有 NVS 切片与已记录 SHA256 不一致，停止"
  }
  Get-Content -LiteralPath $nvsHashPath
}
```

上述切片代码在续作时只读取并校验已有文件，不会覆盖；目标不存在时才从只读的完整备份 A 生成。若怀疑已有文件被人工改动，应停止续作并核查审计记录，不能删除后重建来掩盖差异。

### 7.2 NVS 完整性与命名空间检查

```powershell
$nvsCheckPath = "$CaseRoot\00_backup\$Sample-nvs-check.txt"
Assert-NewEvidencePaths -Paths @($nvsCheckPath)
& $WslExe python3 "$NvsToolWsl" --integrity-check --dump namespaces --color never `
  "$CaseRootWsl/00_backup/$Sample-nvs.bin" 2>&1 |
  Tee-Object $nvsCheckPath
$nvsToolExit = $LASTEXITCODE
Assert-NvsIntegrityLog -Path $nvsCheckPath -ExitCode $nvsToolExit `
  -ExpectedSize $NvsSize
```

F1 应看到 `misc`、`nvs.net80211`、`phy`、`wifi_cfg`，各有效页均显示 `CRC32: OK`。
`Found unused namespace ... [misc]` 只表示命名空间当前没有有效键，不等于 NVS 损坏。

不能只看 `$LASTEXITCODE`；该工具对部分完整性问题可能只打印错误文本而不返回非零。上述白名单按当前锁定的 IDF v5.5.5 输出编写，只允许命名空间列表、`CRC32: OK`、`Page Empty` 和已知非故障提示 `Found unused namespace`；同时要求正常页加空页总数等于 `$NvsSize / 4096`（F1 必须为 6 页）。其余内容全部停止并人工复核。更换 IDF 版本后必须重新验证白名单，不能直接照用。

### 7.3 应用版本确认

```powershell
$imageInfoPath = "$CaseRoot\02_idfver\$Sample-image-info.txt"
$appHashPath = "$CaseRoot\02_idfver\$Sample-$AppName-app-sha256.txt"
$phyInitHashPath = "$CaseRoot\02_idfver\$Sample-phy_init-sha256.txt"

if (-not (Test-Path -LiteralPath $imageInfoPath)) {
  Assert-NewEvidencePaths -Paths @($imageInfoPath)
  py -m esptool image-info `
    "$CaseRoot\02_idfver\$Sample-$AppName-app.bin" 2>&1 |
    Tee-Object $imageInfoPath
  if ($LASTEXITCODE -ne 0) { throw "应用镜像解析失败，停止" }
} else {
  Get-Content -LiteralPath $imageInfoPath
}

function Confirm-OrCreateSha256Record {
  param(
    [Parameter(Mandatory=$true)][string]$ImagePath,
    [Parameter(Mandatory=$true)][string]$RecordPath
  )
  $currentHash = (Get-FileHash -LiteralPath $ImagePath -Algorithm SHA256).Hash
  if (Test-Path -LiteralPath $RecordPath) {
    $recordedText = Get-Content -LiteralPath $RecordPath -Raw
    $recordedHashes = @([regex]::Matches(
      $recordedText,
      '(?i)\b[0-9a-f]{64}\b'
    ) | ForEach-Object { $_.Value.ToUpperInvariant() } | Sort-Object -Unique)
    if (($recordedHashes.Count -ne 1) -or
        ($recordedHashes[0] -ne $currentHash)) {
      throw "已有 SHA256 记录与镜像不一致：$ImagePath"
    }
    Get-Content -LiteralPath $RecordPath
  } else {
    Assert-NewEvidencePaths -Paths @($RecordPath)
    Get-FileHash -LiteralPath $ImagePath -Algorithm SHA256 |
      Format-List Algorithm,Hash,Path | Tee-Object $RecordPath
  }
}

Confirm-OrCreateSha256Record `
  "$CaseRoot\02_idfver\$Sample-$AppName-app.bin" $appHashPath
Confirm-OrCreateSha256Record `
  "$CaseRoot\02_idfver\$Sample-phy_init.bin" $phyInitHashPath
```

本次 F1 应显示：`hello_world`、App version `1`、ESP-IDF `v5.5.2-dirty`，且镜像 checksum/hash 均为 valid。

本机 IDF v5.5.5 的脚本只用于离线解析 NVS/分区表，不代表它与客户 `v5.5.2-dirty` 的 PHY 库等价。

### 7.4 保存首份 PHY 摘要

```powershell
$baselineSummaryPath = "$CaseRoot\00_backup\$Sample-phy-baseline.txt"
Assert-NewEvidencePaths -Paths @($baselineSummaryPath)
& $WslExe python3 "$PhySummaryWsl" --strict --parser-dir "$NvsParserDirWsl" `
  --expected-mac "$ExpectedMac" `
  "$CaseRootWsl/00_backup/$Sample-nvs.bin" 2>&1 |
  Tee-Object $baselineSummaryPath
if ($LASTEXITCODE -ne 0) { throw "PHY 摘要解析失败，停止" }
```

通过条件：

- `cal_version` 能读出；
- `cal_mac_length=6`；
- `cal_data_length=1904`；
- `cal_data_mac_matches_cal_mac=True`；
- `cal_mac_matches_expected_mac=True`。

`cal_data` 是闭源数据，只比较长度和 SHA256，不解释具体字节含义，也不能因为它与良品不同就判定它异常。

### 7.5 续作或换板时恢复上下文

关闭 PowerShell 后续作时，必须先用上一已完成阶段的第二副本和工单系统中登记的 manifest SHA256 校验本地证据。下例中的 Tag、镜像根目录和批准哈希均为占位值，必须替换；校验会同时检查本地 manifest、第二副本 manifest 以及清单中每个文件。仅仅再次比较本地 Full-A/Full-B 不足以证明它们没有被一致替换。

```powershell
$PreviousManifestTag = 'G-PARSE'  # 改为上一已完成阶段：G-PARSE、S0、P1 或 S1
$MirrorBase = 'E:\ESPC2_FA_MIRROR'
$ApprovedPreviousManifestSha256 = '填写工单系统中批准的64位SHA256'
$manifestRelativePath = `
  "00_backup\$Sample-$PreviousManifestTag-manifest.sha256"
$mirrorCase = Join-Path $MirrorBase "$Sample-$PreviousManifestTag"

Assert-CaseCheckpoint `
  -CaseRoot $CaseRoot `
  -MirrorCase $mirrorCase `
  -ManifestRelativePath $manifestRelativePath `
  -ApprovedManifestSha256 $ApprovedPreviousManifestSha256 | Format-List
```

遗留 F1 工单当前没有上述阶段锚点，不能把事后生成的清单描述成“从首次读取起已具备不可篡改链”。应先由两人复核现有双备份、历史哈希、操作履历和工具链建锚批准，再按 7.6 建立首个 `G-PARSE` 清单与第二副本；报告中注明“此前证据为遗留取证，完整性从该锚点起受控”。

完成续作校验后，或在同一已校验的 PowerShell 会话中于 G1/B/F1 之间换板时，不要手工逐个修改全局变量。先按第 4 节加载助手，再执行一条上下文命令。该命令只读已有 `flash_id.txt`、双份完整备份、`pt.bin`、`pt.csv` 和派生切片，会重新校验容量、MAC、A/B 哈希、分区表解码及各切片与 Full-A 的对应关系；所有闸门通过后才一次性设置后续变量，失败时保留原上下文。

```powershell
Set-PhySampleContext -SampleName "F1" -SerialPort "COM10" `
  -ExpectedBaseMac "8c:8c:29:55:5a:dc" | Format-List
```

输出必须显示正确的样品号、COM 口、基础 MAC、Flash 容量、NVS/App 分区和完整备份 SHA256。连接实物并断电直进 ROM 后，还可在任何正式快照前单独执行 `Confirm-PhySampleIdentity`；它只读芯片 MAC，不创建证据文件。每次换板只改上述三个输入值，不直接修改 `$CaseRootWsl`、`$NvsOffset` 等派生变量。

早期 F1 工单若提示缺少 `F1-phy_init.bin` 或 NVS/App 派生切片，先执行第 5 节的日志机读块和第 7.1 节；第 7.1 节只生成缺失的派生文件，并对已有文件做 Full-A 区域互证，不会覆盖首份证据。已经完成的 G0、双备份、NVS 检查和 PHY 摘要命令不要重跑。

### 7.6 阶段清单与第二副本

G-PARSE、S0、P1、S1 每个阶段完成后各生成一次新清单；把 `$ManifestTag` 改为对应阶段，不能复用旧 Tag。`$MirrorBase` 必须改成项目批准的第二块磁盘或受控网络存储，不能仍指向 C 盘。完整镜像包含敏感数据，第二副本沿用第 2.3 节访问控制。

```powershell
$ManifestTag = 'G-PARSE'
$MirrorBase = 'E:\ESPC2_FA_MIRROR'  # 执行前改为已批准且已存在的受控存储
$manifestPath = `
  "$CaseRoot\00_backup\$Sample-$ManifestTag-manifest.sha256"
Assert-NewEvidencePaths -Paths @($manifestPath)

$rootPath = (Resolve-Path -LiteralPath $CaseRoot).Path.TrimEnd('\')
$manifestLines = @(Get-ChildItem -LiteralPath $rootPath -File -Recurse |
  Sort-Object FullName | ForEach-Object {
    $relative = $_.FullName.Substring($rootPath.Length).TrimStart('\')
    $hash = (Get-FileHash -LiteralPath $_.FullName -Algorithm SHA256).Hash
    "$hash  $relative"
  })
if ($manifestLines.Count -eq 0) { throw "工单没有可列入清单的文件" }
$utf8NoBom = New-Object -TypeName Text.UTF8Encoding -ArgumentList $false
[IO.File]::WriteAllLines(
  $manifestPath,
  $manifestLines,
  $utf8NoBom
)

if (-not (Test-Path -LiteralPath $MirrorBase -PathType Container)) {
  throw "第二存储根目录不存在，停止：$MirrorBase"
}
$mirrorCase = Join-Path $MirrorBase "$Sample-$ManifestTag"
if (Test-Path -LiteralPath $mirrorCase) {
  throw "第二副本目录已存在，禁止覆盖：$mirrorCase"
}
Copy-Item -LiteralPath $CaseRoot -Destination $mirrorCase -Recurse

foreach ($line in Get-Content -LiteralPath $manifestPath -Encoding UTF8) {
  if ($line -notmatch '^([0-9A-F]{64})  (.+)$') {
    throw "清单格式错误：$line"
  }
  $copyPath = Join-Path $mirrorCase $Matches[2]
  if (-not (Test-Path -LiteralPath $copyPath -PathType Leaf)) {
    throw "第二副本缺失：$copyPath"
  }
  $copyHash = (Get-FileHash -LiteralPath $copyPath -Algorithm SHA256).Hash
  if ($copyHash -ne $Matches[1]) { throw "第二副本哈希不一致：$copyPath" }
}
$mirrorManifest = Join-Path $mirrorCase `
  "00_backup\$Sample-$ManifestTag-manifest.sha256"
$manifestSha256 = (Get-FileHash $manifestPath -Algorithm SHA256).Hash
if ($manifestSha256 -ne
    (Get-FileHash $mirrorManifest -Algorithm SHA256).Hash) {
  throw "清单自身的第二副本哈希不一致"
}
"阶段清单及第二副本验证通过：$ManifestTag"
"MANIFEST_SHA256=$manifestSha256"
```

把最后一行 `MANIFEST_SHA256` 立即登记到独立于本机和镜像盘的受控工单/PLM/签核记录中，并由复核人确认。下次续作时，第 7.5 节必须使用这个外部批准值；只把哈希另存到同一工单目录不能形成独立锚点。

---

## 8. S0：更新前的三板 RF 基线

### 8.1 三板必须分别建档

| 编号 | 状态 |
|---|---|
| G1 | 同批良品，只读基准 |
| G2 | 第二片同批良品，用于验证换板重复性；没有 G2 时只能做探索性判断 |
| B | 未处理故障样品，作为故障状态保持对照 |
| F1 | 准备执行冷启动验证的故障样品 |

G1、G2、B、F1 每颗模组都必须使用独立样品编号和目录，在任何正常启动前分别完成第 2.3、5、6、7 节。不能把 F1 的备份代替 B 的备份，也不能因良品只读就省略其身份和 PHY 摘要。

`Save-PhySnapshot` 已由第 4 节的助手加载，用于在 RF 测试前后读取 NVS、复核样品 MAC、检查长度/完整性并生成严格 PHY 摘要。调用前样品必须已按 3.3 节“断电直进 ROM”。可先确认三个函数均已加载：

```powershell
Get-Command Set-PhySampleContext,Confirm-PhySampleIdentity,Save-PhySnapshot,`
  Get-PhyState,Get-PhyDataHash,Assert-PhyStatesEqual
```

开始 S0 前，先比较各板从完整备份切出的实际 App 分区。执行前必须把下列 G1、B 的占位 MAC 改成各自的基础 MAC；没有 G2 时保持注释，有 G2 时取消注释并填写。助手会从各工单的实际 `pt.csv` 自动取得 App 分区名，不默认照抄 `factory`。

```powershell
$sampleSpecs = @(
  @{ SampleName='G1'; SerialPort='COM10'; ExpectedBaseMac='填写G1基础MAC' }
  # @{ SampleName='G2'; SerialPort='COM10'; ExpectedBaseMac='填写G2基础MAC' }
  @{ SampleName='B'; SerialPort='COM10'; ExpectedBaseMac='填写B基础MAC' }
  @{ SampleName='F1'; SerialPort='COM10'; ExpectedBaseMac='8c:8c:29:55:5a:dc' }
)

$requiredSamples = @('G1','B','F1')
$listedSamples = @($sampleSpecs | ForEach-Object { $_.SampleName })
$missingSamples = @($requiredSamples | Where-Object { $_ -notin $listedSamples })
if ($missingSamples.Count -ne 0) {
  throw "三板清单缺少：$($missingSamples -join ', ')"
}

$firmwareRecords = @(
  foreach ($spec in $sampleSpecs) {
    Set-PhySampleContext @spec | Out-Null
    $appPath = Join-Path $CaseRoot "02_idfver\$Sample-$AppName-app.bin"
    $phyInitPath = Join-Path $CaseRoot "02_idfver\$Sample-phy_init.bin"
    foreach ($path in @($appPath,$phyInitPath)) {
      if (-not (Test-Path -LiteralPath $path)) { throw "镜像缺失：$path" }
    }
    [pscustomobject]@{
      Sample = $Sample
      AppSHA256 = (Get-FileHash -LiteralPath $appPath -Algorithm SHA256).Hash
      PhyInitSHA256 = (Get-FileHash -LiteralPath $phyInitPath -Algorithm SHA256).Hash
    }
  }
)
$uniqueAppHashes = @($firmwareRecords.AppSHA256 | Sort-Object -Unique)
$uniquePhyInitHashes = @($firmwareRecords.PhyInitSHA256 | Sort-Object -Unique)
if (($uniqueAppHashes.Count -ne 1) -or ($uniquePhyInitHashes.Count -ne 1)) {
  throw "各板实际 App 或 phy_init SHA256 不一致，停止 S0"
}
$firmwareCrosscheckLog = "C:\ESPC2_FA\F1\08_measure\S0-firmware-crosscheck.txt"
Assert-NewEvidencePaths -Paths @($firmwareCrosscheckLog)
$firmwareRecords | Format-Table Sample,AppSHA256,PhyInitSHA256 -AutoSize |
  Out-String -Width 300 | Tee-Object $firmwareCrosscheckLog
```

少于一片良品、一片未处理故障板和一片待验证故障板时，不执行正式三板结论。还必须从源码、构建配置或可审计运行日志填写并归档下表；任一项不同，先统一配置再测试。

| 运行配置 | G1/G2 | B | F1 | 证据来源 |
|---|---|---|---|---|
| 国家码/信道范围 | | | | |
| 最大发射功率 | | | | |
| Wi-Fi 省电模式 | | | | |
| 固定/自适应速率配置 | | | | |
| RSSI 读取接口及采样周期 | | | | |
| 芯片 revision | | | | eFuse/esptool 日志 |
| 实际启动 App 槽 | | | | 分区表/启动日志 |
| `phy_version`/PHY 库版本 | | | | 启动日志/构建记录 |

### 8.2 S0 时间闭环

S0 必须按“全部 pre -> 交替 RF -> 全部 post”的顺序执行：

1. 清单中的全部样品依次断电直进 ROM，分别调用 `Save-PhySnapshot 08_measure S0-pre`，完成全部样品身份核对后才能开始 RF；至少包含 G1、B、F1，有 G2 时一并执行；
2. 按 8.3 的顺序交替换板完成全部 RF 轮次。每片板结束本轮后直接断电并保持断电，禁止为了进入下载模式先正常上电；
3. RF 全部结束后，清单中的全部样品依次按“断电 -> 按住 SW2 -> 上电直进 ROM -> 松开 SW2”进入下载模式，分别调用 `Save-PhySnapshot 08_measure S0-post`；
4. 用下列循环机读比较清单内每颗样品首份备份时、S0-pre、S0-post 的 `cal_version`、`cal_mac`、长度和 `cal_data_sha256`；循环必须完整通过，不能只检查最后接入的 F1。

每次物理换板时重新执行第 7.5 节的 `Set-PhySampleContext`，禁止手工逐项切换派生变量。`Save-PhySnapshot` 还会重新读取基础 MAC；如接入样品与当前工单不一致，将在创建正式快照前停止。

```powershell
foreach ($spec in $sampleSpecs) {
  Set-PhySampleContext @spec | Out-Null
  $s0StatePaths = @(
    "$CaseRoot\00_backup\$Sample-phy-baseline.txt", `
    "$CaseRoot\08_measure\$Sample-S0-pre-phy-summary.txt", `
    "$CaseRoot\08_measure\$Sample-S0-post-phy-summary.txt"
  )
  Assert-PhyStatesEqual -SummaryPaths $s0StatePaths | Out-Null
  Select-String -Path $s0StatePaths `
    -Pattern "cal_version:|cal_mac:|cal_data_length:|cal_data_sha256:"
}
```

只有 S0-pre 与 S0-post 的 PHY 哈希相同，该板的 S0 RF 数据才与该 PHY 状态形成闭环。如果 F1 在 S0 首次正常启动时哈希已经变化，则不能再宣称测到了“原哈希对应的受控坏状态”；如果 B 哈希变化，该轮 B 不能再称“未处理故障对照”；如果 G1/G2 哈希变化，参考基线不稳定，停止本轮测试。

### 8.3 RF 测试要求

1. 所有板使用同型号底板、同一固件、同一供电方式、同一个 RSSI 读取接口/页面，并确认连接的是同一 AP BSSID；
2. 优先使用固定信道、固定发射功率的路由器/AP；手机热点只能作为受限替代，必须固定位置并记录 BSSID 和信道；
3. 不要把 AP 放在模组附近；强信号点建议约 `-60~-45 dBm`，弱信号点建议约 `-82~-70 dBm`；`-89 dBm` 已接近断线区，不适合做精确 RSSI 差值；
4. 板子不要同时堆在一起测。使用同一非金属夹具的同一个位置；有 G2 时先用 `G1 -> G2 -> G1` 做换板空实验，再按 `G1 -> B -> G1 -> F1` 交替换板；没有 G2 时明确降级为探索性测试；
5. 每次放稳后等待 60 秒，排除移动引起的瞬时约 10 dB 跳变，再以 1 Hz 记录 30 个 RSSI，取中位数；
6. 每个信号点至少重复 5 轮，并同步做 100 包 ping，记录丢包率和断开位置；
7. 附近热点较多会引入同信道干扰和 RSSI 波动。测试前扫描信道，固定选较干净的 1、6 或 11 信道，并保留扫描截图。

良品空实验应记录每轮 `G1-G2` 配对差。换板 10 次的极差应不大于 2 dB、单轮标准差不大于 1.5 dB；不通过时先改夹具和环境。当前只有一片良品时必须在报告中注明，3 dB 残差只能作为暂定工程阈值，不能作为统计结论。

| 日期/轮次 | 信号点 | G1 中位数 | B 中位数 | F1 中位数 | G1-B 差距 | G1-F1 差距 | ping 丢包率 | 备注 |
|---|---|---:|---:|---:|---:|---:|---:|---|
| | 强 | | | | | | | |
| | 弱 | | | | | | | |

不要用某一时刻相差 5 dB 或移动中的一次跳变下结论。统一按 `Gap = 良品 RSSI 中位数 - 被测品 RSSI 中位数` 计算。例如良品为 `-75 dBm`、故障品为 `-95 dBm`，则差距为 `+20 dB`。RSSI 绝对值单位为 dBm，差值单位为 dB。

---

## 9. P1：逐次冷启动 PHY 数据变化验证（最多六次）

### 9.1 冷启动条件

- 屏蔽罩保持正常装配，外壳打开；
- PCB 天线伸出板边，周围至少 5 cm 无金属、手和线缆；
- 使用非金属支架，环境 20~30 ℃，样品稳定 10 分钟；
- 走产品正常电源路径，禁止使用 USB-TTL 的 VCC 给模组供电；
- 必须用示波器同步保存 3V3 和 EN/FEN 波形：Wi-Fi 初始化/校准期间 3V3 为 3.3 V ±5%、纹波小于 80 mV，无 brownout 或异常过冲；EN/FEN 上升沿单一、无抖动，波形经硬件工程师确认符合产品时序；波形未取得时只能标为探索性复测，不能称受控校准；
- AP 位置、信道和发射功率保持不变。

### 9.2 一次冷启动、一次回读

开始前必须确认 F1 的 S0-pre 与 S0-post 哈希相同。然后按以下顺序执行，每次只做一个循环：

1. SW2 保持松开，整板断电至少 5 秒并确认 3V3 已降为 0 V；
2. 正常上电，不按 SW2；
3. 等待连接固定 AP，保持收发流量至少 60 秒，同时保存启动日志和 3V3/EN 波形；
4. 记录本次稳定 RSSI 和 ping；
5. 整板断电；先按住 SW2，再上电直接进入 ROM，等待约 1 秒后松开 SW2；禁止先正常启动后再按 SW2/SW3；
6. 将下列 `$CurrentTag` 依次设为 `P1-run01` 至 `P1-run06` 后完整执行同一个代码块；代码用同一个 Tag 完成快照和比较，禁止把两步拆开手工输入。

```powershell
$CurrentTag = 'P1-run01'
Save-PhySnapshot 03_P1 $CurrentTag

$referenceState = Get-PhyState `
  "$CaseRoot\08_measure\$Sample-S0-post-phy-summary.txt"
$currentSummaryPath = `
  "$CaseRoot\03_P1\$Sample-$CurrentTag-phy-summary.txt"
$currentState = Get-PhyState $currentSummaryPath
if (($currentState.CalVersion -ne $referenceState.CalVersion) -or
    ($currentState.CalMac -ne $referenceState.CalMac) -or
    ($currentState.CalDataLength -ne $referenceState.CalDataLength)) {
  throw "PHY 版本、MAC 或长度发生非预期变化，停止"
}
if ($currentState.CalDataSHA256 -eq $referenceState.CalDataSHA256) {
  "本轮 cal_data 未变化"
} else {
  "本轮首次发现 cal_data 变化：$($currentState.CalDataSHA256)"
}
```

首次发现 PHY 哈希变化时立即停止循环，不要继续盲目冷启动，直接进入 9.3。连续 6 次都未变化则停止 P1，不以增加启动次数尝试“碰出一次自愈”。每次下载模式启动需单独记入启动履历。

UART0 如果输出业务二进制而无法得到可读日志，应记录“UART0 为业务二进制，未取得可判读 PHY 日志”，不要把乱码转换成错误的 FULL/PARTIAL 结论。

### 9.3 更新后的稳定性确认

发现哈希变化后，记录发生变化的轮次和新哈希；然后退出下载模式，在相同条件再完成 1 次冷启动和 60 秒收发。测试结束后整板断电，先按住 SW2，再上电直接进入 ROM，等待约 1 秒后松开 SW2，然后执行：

```powershell
Save-PhySnapshot 03_P1 P1-check1

$referenceSummaryPath = `
  "$CaseRoot\08_measure\$Sample-S0-post-phy-summary.txt"
$referenceState = Get-PhyState $referenceSummaryPath
$escapedSample = [regex]::Escape($Sample)
$runSummaries = @(Get-ChildItem -LiteralPath "$CaseRoot\03_P1" -File |
  Where-Object {
    $_.Name -match "^${escapedSample}-P1-run0[1-6]-phy-summary\.txt$"
  } | Sort-Object Name)
if ($runSummaries.Count -eq 0) { throw "没有 P1 逐次快照，停止" }

$expectedRunNames = @(1..$runSummaries.Count | ForEach-Object {
  "$Sample-P1-run$($_.ToString('00'))-phy-summary.txt"
})
if (@(Compare-Object $expectedRunNames @($runSummaries.Name)).Count -ne 0) {
  throw "P1 逐次快照编号不连续或命名错误，停止"
}

$runStates = @($runSummaries | ForEach-Object { Get-PhyState $_.FullName })
$firstChangedIndex = -1
for ($i = 0; $i -lt $runStates.Count; $i++) {
  $state = $runStates[$i]
  if (($state.CalVersion -ne $referenceState.CalVersion) -or
      ($state.CalMac -ne $referenceState.CalMac) -or
      ($state.CalDataLength -ne $referenceState.CalDataLength)) {
    throw "P1 第 $($i + 1) 轮的版本、MAC 或长度发生非预期变化"
  }
  if (($firstChangedIndex -lt 0) -and
      ($state.CalDataSHA256 -ne $referenceState.CalDataSHA256)) {
    $firstChangedIndex = $i
  }
}
if ($firstChangedIndex -lt 0) { throw "P1 中未发现 cal_data 变化，停止" }

$changedState = $runStates[$firstChangedIndex]
for ($i = $firstChangedIndex; $i -lt $runStates.Count; $i++) {
  if ($runStates[$i].StateKey -ne $changedState.StateKey) {
    throw "首次变化后的 P1 状态不稳定，停止"
  }
}
$ChangedSummaryPath = $runSummaries[$firstChangedIndex].FullName
$checkSummaryPath = `
  "$CaseRoot\03_P1\$Sample-P1-check1-phy-summary.txt"
Assert-PhyStatesEqual -SummaryPaths @(
  $ChangedSummaryPath,
  $checkSummaryPath
) | Out-Null

Select-String -Path `
  "$CaseRoot\08_measure\$Sample-S0-post-phy-summary.txt", `
  "$CaseRoot\03_P1\$Sample-P1-run*-phy-summary.txt", `
  "$CaseRoot\03_P1\$Sample-P1-check1-phy-summary.txt" `
  -Pattern "cal_version:|cal_mac:|cal_data_length:|cal_data_sha256:"
```

代码会按连续编号自动定位首个变化轮次，并要求其后的已留快照均保持同一新状态；该状态与 check1 的 `cal_data_sha256` 必须相同，且各 NVS 均通过长度和完整性检查。只用 `cal_data_sha256` 判断 PHY 数据是否变化；整个 NVS 文件可能因 `nvs.net80211` 或应用正常写入而变化，不能拿整个 NVS 的 SHA256 代替 PHY 键级比较。

### 9.4 P1 判读

| 结果 | 判定与下一步 |
|---|---|
| 某轮哈希变化，check1 与新哈希相同 | 该轮启动期间 PHY 数据发生变化，当前已稳定；进入 S1 RF 复测 |
| 连续六轮哈希均不变 | 未观察到数据变化；若 RF 仍差，停止把冷启动当修复方法 |
| 新哈希与 check1 不同 | 数据反复变化，属于校准/NVS/固件流程不稳定；停止并查根因 |
| 数据变化但 RF 无改善 | 当前症状不能由 PHY 数据变化单独解释，转硬件 FA 或检查测试系统 |

没有可读启动日志时只能写“启动期间 PHY 数据发生变化”，不能判断这次是 NVS 加载失败触发 FULL、PHY 内部校验失败触发的更新，还是其他固件逻辑写入。F1 历史实验是在六次冷启动后才首次回读，所以只能确认“六次期间发生过变化”，不能定位具体轮次。

---

## 10. S1：更新后三板复测与验收

完全复用 S0 的夹具、AP、信道、位置、顺序、采样数量和供电条件。不要为了得到更好的数字改变 AP 距离、板子朝向或外壳状态。

S1 仍按“全部 pre -> 交替 RF -> 全部 post”执行。测试前，G1、B、F1 均用断电直进 ROM 时序执行 `Save-PhySnapshot 08_measure S1-pre`；完成全部 RF 轮次并把各板断电后，再逐板按“断电 -> 按住 SW2 -> 上电直进 ROM -> 松开 SW2”执行 `Save-PhySnapshot 08_measure S1-post`。禁止先正常启动后再按 SW2/SW3 取得 post 快照。

G1、B 各自的前后哈希必须不变；B 一旦变化，本轮不能再作为“未处理故障板”对照。F1 的 S1-pre、S1-post 必须等于 P1-check1 的新哈希，否则更新后状态不稳定。每次换板均重新执行第 7.5 节的 `Set-PhySampleContext`，只填写样品号、COM 口和基础 MAC；身份校验通过后再读取 NVS。

```powershell
Assert-PhyStatesEqual -SummaryPaths @(
  "C:\ESPC2_FA\G1\00_backup\G1-phy-baseline.txt",
  "C:\ESPC2_FA\G1\08_measure\G1-S0-post-phy-summary.txt",
  "C:\ESPC2_FA\G1\08_measure\G1-S1-pre-phy-summary.txt",
  "C:\ESPC2_FA\G1\08_measure\G1-S1-post-phy-summary.txt"
) | Out-Null
Assert-PhyStatesEqual -SummaryPaths @(
  "C:\ESPC2_FA\B\00_backup\B-phy-baseline.txt",
  "C:\ESPC2_FA\B\08_measure\B-S0-post-phy-summary.txt",
  "C:\ESPC2_FA\B\08_measure\B-S1-pre-phy-summary.txt",
  "C:\ESPC2_FA\B\08_measure\B-S1-post-phy-summary.txt"
) | Out-Null
Assert-PhyStatesEqual -SummaryPaths @(
  "C:\ESPC2_FA\F1\03_P1\F1-P1-check1-phy-summary.txt",
  "C:\ESPC2_FA\F1\08_measure\F1-S1-pre-phy-summary.txt",
  "C:\ESPC2_FA\F1\08_measure\F1-S1-post-phy-summary.txt"
) | Out-Null
```

| 日期/轮次 | 信号点 | G 中位数 | B 中位数 | F1 更新后中位数 | G-B 差距 | G-F1 残差 | ping 丢包率 | 备注 |
|---|---|---:|---:|---:|---:|---:|---:|---|
| | 强 | | | | | | | |
| | 弱 | | | | | | | |

S1 配对 RF 结果通过后，再对 F1 做 10 次逐次稳定性验证，不能只比较第 10 次终态：

1. 用 `Set-PhySampleContext` 切回 F1，确认输出中的 MAC 和分区正确；
2. 整板断电至少 5 秒，正常上电运行并保持收发 60 秒，记录 RSSI 和 ping；
3. 整板断电，按住 SW2 后上电直进 ROM，再松开 SW2；
4. 依次把 `$StabilityTag` 设为 `S1-stab01` 至 `S1-stab10`，每轮执行下列代码，每次只使用一个未使用的 Tag；
5. 每一轮摘要的 `cal_data_sha256` 都必须等于 P1-check1，且每轮 RF 没有持续劣化；任一轮变化立即停止稳定性测试并查固件/NVS 流程。

```powershell
$StabilityTag = 'S1-stab01'
Save-PhySnapshot 08_measure $StabilityTag
$p1Check = "$CaseRoot\03_P1\$Sample-P1-check1-phy-summary.txt"
$stabilitySummary = `
  "$CaseRoot\08_measure\$Sample-$StabilityTag-phy-summary.txt"
Assert-PhyStatesEqual -SummaryPaths @($p1Check,$stabilitySummary) | Out-Null
```

第 10 轮后再检查文件数和全体状态：

```powershell
$p1Check = "$CaseRoot\03_P1\$Sample-P1-check1-phy-summary.txt"
if (-not (Test-Path -LiteralPath $p1Check -PathType Leaf)) {
  throw "缺少 P1-check1 摘要，停止验收"
}
$escapedSample = [regex]::Escape($Sample)
$stabilitySummaries = @(Get-ChildItem -LiteralPath "$CaseRoot\08_measure" -File |
  Where-Object {
    $_.Name -match "^${escapedSample}-S1-stab(0[1-9]|10)-phy-summary\.txt$"
  } | Sort-Object Name)
if ($stabilitySummaries.Count -ne 10) {
  throw "稳定性摘要不是 10 份，停止验收"
}
$allStabilityPaths = @($p1Check) + @($stabilitySummaries.FullName)
Assert-PhyStatesEqual -SummaryPaths $allStabilityPaths | Out-Null
```

正式判据：

- 未处理故障板在弱信号下相对良品仍保持明显差距；
- 至少 5 轮配对数据，逐轮计算 `R_i = Gap_before_i - Gap_after_i`，报告轮数、平均恢复量、标准差和 95% 置信区间；
- 恢复量的 95% 置信区间下界大于 6 dB；逐轮计算更新后与良品的绝对残差，残差均值的 95% 置信区间上界必须小于 3 dB，不能只看残差点估计；
- F1 的丢包率、吞吐量或断开门限至少一项同步恢复；
- 10 次逐次冷启动快照的 PHY 哈希均保持不变，RF 结果没有持续性劣化；
- 裸板态和装壳态分别记录，禁止混算；若装壳比裸板差超过 6 dB，转天线匹配/结构问题分析。

95% 置信区间按 `平均值 ± t(0.975,n-1) × 标准差 / sqrt(n)` 计算；`n=5` 时 t 值取 2.776。若没有 G2 或良品空实验不通过，上述门槛只能列为探索性工程判断，不能写成统计证实。

如果只有 RSSI 数值恢复、业务性能没有对应变化，结论应写为“RSSI 指示/接收增益表现恢复”，不能写“实际 20 dB 射频衰减已修复”。

---

## 11. 真正的受控强制重校准（工程审批阶段）

仅在工程审批后，因主动重建 PHY 数据、可逆因果验证或返修需要时进入本阶段。P1 中数据变化后表现已恢复的样品，不把强制重校准作为普通现场必做项。普通现场操作员不得自行执行。

准入条件：

1. 已取得客户 `v5.5.2-dirty` 对应的完整源码、私有补丁、`sdkconfig`、分区表和 PHY 库；
2. 已完成 G-BACKUP，并先在至少两片牺牲良品上跑通写入、校准、客户 App 恢复和整片回滚；任一牺牲良品重校后下降超过 3 dB，立即停止、回滚并重新检查环境，禁止转到故障样品；
3. 工装 App 已完成代码评审和实板验证；现有大指导书中的 B1 代码 UART 输入部分为省略模板，不能直接作为生产工装；
4. 工装只允许在人工确认后调用 `esp_phy_erase_cal_data_in_nvs()`，不得调用 `nvs_flash_erase()`；
5. 烧录工装阶段只写实际 App 分区，不改 bootloader、分区表、NVS、eFuse 或 MAC；工装运行阶段只允许在人工确认后修改 NVS 的 `phy` 命名空间；
6. 校准在 9.1 的受控半装配环境中执行，3V3/EN 波形必须满足 9.1 的硬门槛并归档。

工程流程：

```text
审批和物理取证
  -> 双份完整 Flash 备份及 NVS 解析
  -> 备份客户实际 App 分区
  -> 写入同版本 PHY 工装 App，并立即回读核验
  -> 第 1 次：人工确认后只清除 NVS 的 phy 命名空间
  -> 工装初始化 Wi-Fi，触发 FULL calibration
  -> 回读 NVS，确认 phy 已重建、长度 1904、MAC 正确、其他命名空间仍在
  -> 恢复客户 App并做同条件 RF；随后重写工装，重复上述步骤至共 3 次独立 FULL
  -> 比较 3 次校准后的 PHY 摘要和 RF；结果极差超过 5 dB 时停止，不得转量产
  -> 采用获批状态恢复客户 App，并立即回读核验
  -> 客户 App 冷启动，确认不会再次更新 PHY 数据
  -> 执行 S1 三板 RF 复测和稳定性测试
```

10 次普通冷启动只证明某一份 `cal_data` 的持久性，不能替代上述至少 3 次“仅清除本机 `phy` -> 独立 FULL -> 同条件 RF”的重校重复性验证。任何一次都必须保留写前/写后回读、PHY 摘要、供电/EN 波形和 RF 原始数据。

### 11.1 受限 FA：旧/新数据 A/B/A/B

以下不是现场返修步骤，只能由获批的 FA 工程师执行。要把“PHY 数据是直接原因”升级为因果结论，还需在同一模组上使用它自己的首份备份 NVS 做至少两个完整来回的盲测：

```text
首份坏状态 S0 -> 新校准状态 S1 -> 回灌本机首份状态 S2
               -> 再校准状态 S3 -> 再回灌首份状态 S4
```

每次回灌前必须重新核对 eFuse、安全模式、模组基础 MAC、实际 NVS offset/size 和镜像长度。首份备份 NVS 只能回灌到原 MAC 的同一模组；写后必须立即回读并确认 SHA256 完全一致，未通过前严禁正常上电。

整 NVS 回灌会同时改变 `phy`、`nvs.net80211`、`wifi_cfg` 和其他应用命名空间，不是天然的 PHY 单变量实验。S0、S1、S2、S3、S4 每个状态都必须在实际正常启动并完成 RF 后，立即断电直进 ROM 留 post 快照；随后在受控环境中对每份 NVS 做语义导出，并对所有非 `phy` 键执行机器 diff。只有经评审的计数器/时间戳等易变键可进入书面白名单，其他差异一律停止因果判定；还要逐态核对国家码、最大发射功率、省电模式和速率配置。敏感键只在受控内部环境比较，不进入客户报告。无法证明这些混淆项不变时，A/B/A/B 最多说明“NVS 状态与现象相关”，不能说明“PHY 数据直接导致现象”。

S2/S4 正常启动后要立即再次回读，确认旧 `cal_data` 哈希仍保持，并确认日志中没有 `falling back to full calibration` 或 `Saving new calibration data due to`。若旧哈希已被自动替换，或无法取得可判读日志，该状态不能作为完整的因果证据。

只有 `S0≈S2≈S4` 坏、`S1≈S3` 好，旧/新哈希均通过上述状态闸门、非 PHY 配置已证明不变，且业务指标同步变化，才可写“直接因果”。

---

## 12. 后续根因排查与防复发措施

### 12.1 查异常 PHY 数据如何形成

- 用示波器抓首次校准时的模组 3V3 与 EN/FEN，检查电源建立、复位释放、纹波和掉电是否异常；
- 向客户取得故障发生前后的 OTA 时间线、固件 bin SHA256、ESP-IDF/PHY 库版本和完整 `sdkconfig`；
- 核对 `CONFIG_ESP_PHY_CALIBRATION_AND_DATA_STORAGE`、`CONFIG_ESP_PHY_CALIBRATION_MODE`、`CONFIG_ESP_PHY_IMPROVE_RX_11B`、最大发射功率和国家码；
- 检查应用是否在 `nvs_flash_init()` 失败时自动擦除整个 NVS，或在恢复出厂/OTA 中错误处理 `phy` 命名空间；
- 追溯首次上电或 OTA 后首次上电时，产品是否已经装壳、靠近金属/人体、处于高温或供电不稳定状态；
- 比对同批良品和故障品的 `cal_version`、PHY 哈希、生产日期和 OTA 批次，禁止仅凭不同模组的 cal_data 内容不同判坏。

### 12.2 量产和返修措施

- 在 SMT 后、装壳前设置受控校准/验证工位：屏蔽罩装好、外壳打开、非金属治具、天线净空、常温稳定供电；
- 逐台保存 MAC、固件哈希、PHY 版本、`cal_version`、`cal_data` 长度和哈希，以及固定 AP 下的 RSSI 中位数和业务门限；
- 增加弱信号出货筛选，不能只做 AP 近距离强信号通断测试；
- 保留维修人员逐台人工触发的 PHY 维护入口，但禁止 OTA 或设备自主批量擦除/重校准；
- OTA 前后只读上报 PHY 摘要并统计变化，发现异常后人工判定；
- 对更新后的样品做 10 次冷启动、72 小时连续运行及必要的温循复测；
- 若 PHY 更新无改善，按天线净空、匹配元件/焊点、屏蔽罩压迫、RF 脚焊接、LNA/PA/ESD 损伤顺序进入硬件 FA。

---

## 13. F1 当前证据

### 13.1 已由镜像复核的数字取证

| 项目 | F1 实测值 |
|---|---|
| esptool | 5.3.1 |
| 串口 | COM10 |
| 芯片 | ESP8684H / ESP32-C2 rev2.0 |
| 晶振 | 26 MHz |
| Flash | 2 MB |
| 基础 MAC / PHY cal_mac | `8c:8c:29:55:5a:dc` |
| AP BSSID | `8c:8c:29:55:5a:dd` |
| eFuse 安全项 | 加密、Secure Boot、安全下载均未启用，`RD_DIS=0` |
| 完整备份 A/B SHA256 | `6605FA1952C4924DB193524E4D7B2A2E531D72B4D7DC62D4A5019104F4DEC4BA` |
| 首份备份时 NVS SHA256 | `7FA75181B7C6C6632FA8CFD542DBE80087A8A50AC3A9F93514829A1CE274932B` |
| App | `hello_world`, version 1, ESP-IDF `v5.5.2-dirty` |
| App 分区 SHA256 | `7745A0B9D0B5326CF0589E5E728CD94247B79344494F868D8652100B60825E0C` |
| App 编译时间 | `Jun 24 2026 09:40:08` |
| 首份备份时 cal_version | 372 / `0x00000174` |
| 首份备份时 cal_data 长度 | 1904 bytes |
| 首份备份时 cal_data SHA256 | `31F5F8C249B6014C38BF355D65304713D0F1F56502F1CF7DFD6D47FF698E7B09` |
| 6 次冷启动后 cal_data SHA256 | `8083F18EC4A563C35117FF44CFEBA51B2CA1F04BB38DA80EEDC5790C808AA24A` |
| 再冷启动 1 次 cal_data SHA256 | `8083F18EC4A563C35117FF44CFEBA51B2CA1F04BB38DA80EEDC5790C808AA24A` |

首份备份时、操作人员记录的六次冷启动后和再次冷启动后的三份 NVS 镜像均已通过 `nvs_tool.py --integrity-check`，所有有效页为 `CRC32: OK`。三次采集点的镜像证据确认：`cal_version`、MAC 和长度未变；首份与六次操作后的快照之间 `cal_data` 不同，随后一次冷启动快照保持新哈希。六次冷启动次数来自操作履历，不是镜像本身能够证明的事实。

### 13.2 尚待原始记录归档的现场观察

现场口述的三板观察为：更新后的 F1 接近良品，另一块故障板在弱信号下仍低 20 dB 以上。但当前 `08_measure` 尚无原始 RSSI CSV、5 轮中位数、夹具照片和 ping/吞吐记录，也没有 S0 前后及另一块故障板前后的 PHY 哈希闭环，因此该部分只能标为“现场初步观察”，不能列为已完成的正式统计验证。补齐第 8~10 节记录后再升级证据等级。

数字取证与现场观察形成了“PHY 数据变化与表现改善同时出现”的相关性线索，但样本量有限，且缺少逐次启动取样、同一模组 A/B/A/B 回灌和可读 PHY 启动日志。

注意：`03_P1\read-after.txt` 当时是脱离读取命令单独执行 `Tee-Object` 生成的 2 字节空日志，不能作为读取过程证据；对应 NVS 镜像和 PHY 摘要有效，后续命令必须按本指南把 `Tee-Object` 写在同一条管道内。

---

## 14. 对客户的阶段性表述

> 交叉验证显示故障随模组移动。镜像取证确认，故障样品首份备份与操作人员记录的六次冷启动后快照之间，PHY `cal_data` 已发生变化；随后一次冷启动快照保持相同。现场初步三板对照观察显示，数据变化后样品的弱信号 RSSI/接收表现接近良品，另一块故障板仍存在明显差异。现有结果形成了“PHY 数据变化与表现改善同时出现”的相关性线索。由于尚未完成逐次启动取样、RF 原始记录归档及同一模组旧/新数据的可逆复现，目前不将首份备份时的 `cal_data` 定义为已确认异常，也不作为最终根因。是否存在同幅度的实际链路衰减，还需结合丢包率、吞吐量或断开门限确认；该数据状态的形成原因将继续从供电/EN 时序、校准环境、OTA/PHY 版本和固件 NVS 处理逻辑进行 FA。
