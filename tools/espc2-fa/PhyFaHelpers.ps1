function Assert-NewEvidencePaths {
  param([Parameter(Mandatory=$true)][string[]]$Paths)

  $existing = @($Paths | Where-Object { Test-Path -LiteralPath $_ })
  if ($existing.Count -ne 0) {
    throw "Evidence file already exists; overwrite blocked: $($existing -join ', ')"
  }
}

function Assert-CaseCheckpoint {
  param(
    [Parameter(Mandatory=$true)][string]$CaseRoot,
    [Parameter(Mandatory=$true)][string]$MirrorCase,
    [Parameter(Mandatory=$true)][string]$ManifestRelativePath,
    [Parameter(Mandatory=$true)][string]$ApprovedManifestSha256
  )

  $approvedHash = $ApprovedManifestSha256.Trim().ToUpperInvariant()
  if ($approvedHash -notmatch '^[0-9A-F]{64}$') {
    throw "Approved manifest SHA256 must contain exactly 64 hex digits"
  }
  if ([IO.Path]::IsPathRooted($ManifestRelativePath) -or
      ($ManifestRelativePath -match '(^|[\\/])\.\.([\\/]|$)')) {
    throw "Manifest path must stay inside the case directory"
  }

  $localManifest = Join-Path $CaseRoot $ManifestRelativePath
  $mirrorManifest = Join-Path $MirrorCase $ManifestRelativePath
  foreach ($manifest in @($localManifest,$mirrorManifest)) {
    if (-not (Test-Path -LiteralPath $manifest -PathType Leaf)) {
      throw "Checkpoint manifest is missing: $manifest"
    }
    $actualHash = (Get-FileHash -LiteralPath $manifest -Algorithm SHA256).Hash
    if ($actualHash -ne $approvedHash) {
      throw "Checkpoint manifest differs from the externally approved hash: $manifest"
    }
  }

  $seen = @{}
  $entryCount = 0
  foreach ($line in Get-Content -LiteralPath $mirrorManifest -Encoding UTF8) {
    if ($line -notmatch '^([0-9A-Fa-f]{64})  (.+)$') {
      throw "Invalid checkpoint manifest line: $line"
    }
    $recordedHash = $Matches[1].ToUpperInvariant()
    $relative = $Matches[2]
    if ([IO.Path]::IsPathRooted($relative) -or
        ($relative -match '(^|[\\/])\.\.([\\/]|$)')) {
      throw "Checkpoint entry escapes the case directory: $relative"
    }
    $entryKey = $relative.ToUpperInvariant()
    if ($seen.ContainsKey($entryKey)) {
      throw "Duplicate checkpoint entry: $relative"
    }
    $seen[$entryKey] = $true
    $entryCount++

    foreach ($root in @($CaseRoot,$MirrorCase)) {
      $filePath = Join-Path $root $relative
      if (-not (Test-Path -LiteralPath $filePath -PathType Leaf)) {
        throw "Checkpoint file is missing: $filePath"
      }
      $fileHash = (Get-FileHash -LiteralPath $filePath -Algorithm SHA256).Hash
      if ($fileHash -ne $recordedHash) {
        throw "Checkpoint file hash differs: $filePath"
      }
    }
  }
  if ($entryCount -eq 0) { throw "Checkpoint manifest contains no files" }

  [pscustomobject]@{
    ManifestSHA256 = $approvedHash
    FilesVerified = $entryCount
    LocalCase = $CaseRoot
    MirrorCase = $MirrorCase
  }
}

function Convert-PartitionNumber {
  param([Parameter(Mandatory=$true)][string]$Text)

  $value = $Text.Trim()
  if ($value -match '^0x([0-9A-Fa-f]+)$') {
    return [Convert]::ToInt64($Matches[1], 16)
  }
  if ($value -match '^(\d+)K$') { return [int64]$Matches[1] * 1KB }
  if ($value -match '^(\d+)M$') { return [int64]$Matches[1] * 1MB }
  if ($value -match '^\d+$') { return [Convert]::ToInt64($value, 10) }
  throw "Cannot parse partition value: $Text"
}

function Export-FlashRegion {
  param(
    [Parameter(Mandatory=$true)][string]$Source,
    [Parameter(Mandatory=$true)][long]$Offset,
    [Parameter(Mandatory=$true)][int]$Length,
    [Parameter(Mandatory=$true)][string]$Output
  )

  if (Test-Path -LiteralPath $Output) {
    throw "Flash-region output already exists; overwrite blocked: $Output"
  }
  $src = [IO.File]::ReadAllBytes((Resolve-Path -LiteralPath $Source).Path)
  if (($Offset + $Length) -gt $src.LongLength) {
    throw "Flash region exceeds source image bounds"
  }
  $dst = New-Object byte[] $Length
  [Array]::Copy($src, $Offset, $dst, 0, $Length)
  [IO.File]::WriteAllBytes($Output, $dst)
}

function Get-ByteArraySha256 {
  param([Parameter(Mandatory=$true)][byte[]]$Bytes)

  $sha = [Security.Cryptography.SHA256]::Create()
  try {
    return ([BitConverter]::ToString($sha.ComputeHash($Bytes)) -replace '-','')
  } finally {
    $sha.Dispose()
  }
}

function Assert-FlashRegionMatches {
  param(
    [Parameter(Mandatory=$true)][string]$Source,
    [Parameter(Mandatory=$true)][long]$Offset,
    [Parameter(Mandatory=$true)][int]$Length,
    [Parameter(Mandatory=$true)][string]$RegionFile
  )

  $src = [IO.File]::ReadAllBytes((Resolve-Path -LiteralPath $Source).Path)
  $region = [IO.File]::ReadAllBytes((Resolve-Path -LiteralPath $RegionFile).Path)
  if (($Offset + $Length) -gt $src.LongLength) {
    throw "Flash region exceeds source image bounds"
  }
  if ($region.Length -ne $Length) {
    throw "Region-file length differs from partition length: $RegionFile"
  }
  $expected = New-Object byte[] $Length
  [Array]::Copy($src, $Offset, $expected, 0, $Length)
  $expectedHash = Get-ByteArraySha256 -Bytes $expected
  $regionHash = Get-ByteArraySha256 -Bytes $region
  if ($expectedHash -ne $regionHash) {
    throw "Region file does not match full backup: $RegionFile"
  }
  return $regionHash
}

function Assert-PartitionCsvMatches {
  param(
    [Parameter(Mandatory=$true)][string]$PartitionBinWsl,
    [Parameter(Mandatory=$true)][string]$PartitionCsvWin,
    [Parameter(Mandatory=$true)][string]$FlashSizeText,
    [Parameter(Mandatory=$true)][string]$GenPartWslPath,
    [string]$WslExePath = "$env:SystemRoot\System32\wsl.exe"
  )

  $generated = @(& $WslExePath python3 "$GenPartWslPath" --quiet `
    --flash-size $FlashSizeText $PartitionBinWsl 2>&1)
  $exitVariable = Get-Variable -Name LASTEXITCODE -ErrorAction SilentlyContinue
  $generatorExit = if ($null -eq $exitVariable) { -1 } else { $exitVariable.Value }
  if ($generatorExit -ne 0) {
    $generated | Out-Host
    throw "Partition-table regeneration failed"
  }
  $generatedNormalized = @($generated | ForEach-Object {
    $_.ToString().TrimEnd()
  } | Where-Object { $_.Trim() }) -join "`n"
  $storedNormalized = @(Get-Content -LiteralPath $PartitionCsvWin |
    ForEach-Object { $_.TrimEnd() } |
    Where-Object { $_.Trim() }) -join "`n"
  if ($generatedNormalized -cne $storedNormalized) {
    throw "Stored pt.csv differs from a fresh decode of pt.bin"
  }
}

function Assert-NvsIntegrityLog {
  param(
    [Parameter(Mandatory=$true)][string]$Path,
    [Parameter(Mandatory=$true)][int]$ExitCode,
    [Parameter(Mandatory=$true)][int]$ExpectedSize
  )

  if ($ExitCode -ne 0) { throw "NVS tool returned ${ExitCode}: $Path" }
  if (($ExpectedSize -le 0) -or (($ExpectedSize % 4096) -ne 0)) {
    throw "NVS size is not a positive multiple of 4096: $ExpectedSize"
  }
  $crcCount = 0
  $emptyCount = 0
  foreach ($line in Get-Content -LiteralPath $Path) {
    $item = $line.Trim()
    if ($item -eq '') { continue }
    if ($item -match '^Index:\s+Namespace$') { continue }
    if ($item -match '^\d{3}:\s+.+$') { continue }
    if ($item -match '^Page no\.\s+\d+\s+CRC32:\s+OK$') {
      $crcCount++
      continue
    }
    if ($item -eq 'Page Empty') {
      $emptyCount++
      continue
    }
    if ($item -match '^Found unused namespace\. Namespace index:\s+\d+\s+\[[^\]]+\]$') {
      continue
    }
    throw "Unexpected NVS integrity output: $item"
  }
  if ($crcCount -eq 0) { throw "NVS log has no valid-page CRC result" }
  $expectedPages = [int]($ExpectedSize / 4096)
  if (($crcCount + $emptyCount) -ne $expectedPages) {
    throw "NVS page count mismatch: log has $($crcCount + $emptyCount), expected $expectedPages"
  }
}

function Get-UniqueMacFromText {
  param([Parameter(Mandatory=$true)][string]$Text)

  $matches = [regex]::Matches(
    $Text,
    '(?im)^\s*MAC:\s*([0-9a-f]{2}(?::[0-9a-f]{2}){5})\s*$'
  )
  $macs = @($matches | ForEach-Object {
    $_.Groups[1].Value.ToLowerInvariant()
  } | Sort-Object -Unique)
  if ($macs.Count -ne 1) { throw "Could not parse one unique base MAC" }
  return $macs[0]
}

function Get-PhyDataHash {
  param([Parameter(Mandatory=$true)][string]$SummaryPath)

  $text = Get-Content -LiteralPath $SummaryPath -Raw
  $matches = [regex]::Matches(
    $text,
    '(?im)^cal_data_sha256:\s*([0-9a-f]{64})\s*$'
  )
  $hashes = @($matches | ForEach-Object {
    $_.Groups[1].Value.ToUpperInvariant()
  } | Sort-Object -Unique)
  if ($hashes.Count -ne 1) {
    throw "Could not parse one unique cal_data_sha256: $SummaryPath"
  }
  return $hashes[0]
}

function Get-PhyState {
  param([Parameter(Mandatory=$true)][string]$SummaryPath)

  $text = Get-Content -LiteralPath $SummaryPath -Raw
  $values = @{}
  foreach ($field in @('cal_version','cal_mac','cal_data_length','cal_data_sha256')) {
    $matches = [regex]::Matches(
      $text,
      "(?im)^${field}:\s*(\S+)\s*$"
    )
    $uniqueValues = @($matches | ForEach-Object {
      $_.Groups[1].Value.ToUpperInvariant()
    } | Sort-Object -Unique)
    if ($uniqueValues.Count -ne 1) {
      throw "Could not parse one unique ${field}: $SummaryPath"
    }
    $values[$field] = $uniqueValues[0]
  }
  [pscustomobject]@{
    Path = $SummaryPath
    CalVersion = $values['cal_version']
    CalMac = $values['cal_mac']
    CalDataLength = $values['cal_data_length']
    CalDataSHA256 = $values['cal_data_sha256']
    StateKey = @(
      $values['cal_version'],
      $values['cal_mac'],
      $values['cal_data_length'],
      $values['cal_data_sha256']
    ) -join '|'
  }
}

function Assert-PhyStatesEqual {
  param([Parameter(Mandatory=$true)][string[]]$SummaryPaths)

  if ($SummaryPaths.Count -lt 2) {
    throw "At least two PHY summaries are required"
  }
  $results = @($SummaryPaths | ForEach-Object {
    Get-PhyState -SummaryPath $_
  })
  $uniqueStates = @($results.StateKey | Sort-Object -Unique)
  $results | Format-Table `
    Path,CalVersion,CalMac,CalDataLength,CalDataSHA256 -AutoSize | Out-Host
  if ($uniqueStates.Count -ne 1) {
    throw "PHY states differ"
  }
  return $results[0]
}

function Set-PhySampleContext {
  param(
    [Parameter(Mandatory=$true)][string]$SampleName,
    [Parameter(Mandatory=$true)][string]$SerialPort,
    [Parameter(Mandatory=$true)][string]$ExpectedBaseMac,
    [string]$CaseBase = 'C:\ESPC2_FA',
    [long]$PartitionTableOffset = 0x8000,
    [int]$PartitionTableSize = 0xC00
  )

  if ($SampleName -notmatch '^[A-Za-z0-9_-]+$') {
    throw "SampleName may contain only letters, digits, underscore, and hyphen"
  }
  if ($ExpectedBaseMac -notmatch '^[0-9a-fA-F]{2}(?::[0-9a-fA-F]{2}){5}$') {
    throw "ExpectedBaseMac has an invalid format"
  }
  if ($CaseBase -notmatch '^([A-Za-z]):\\(.*)$') {
    throw "CaseBase must be an absolute Windows path"
  }

  $drive = $Matches[1].ToLowerInvariant()
  $baseTail = $Matches[2].TrimEnd('\') -replace '\\','/'
  $caseRoot = Join-Path $CaseBase $SampleName
  $caseRootWsl = "/mnt/$drive/$baseTail/$SampleName"
  $flashIdPath = Join-Path $caseRoot '00_backup\flash_id.txt'
  $readMacPath = Join-Path $caseRoot '00_backup\read_mac.txt'
  $ptBinPath = Join-Path $caseRoot '01_ptable\pt.bin'
  $ptCsvPath = Join-Path $caseRoot '01_ptable\pt.csv'
  $fullAPath = Join-Path $caseRoot "00_backup\$SampleName-full-A.bin"
  $fullBPath = Join-Path $caseRoot "00_backup\$SampleName-full-B.bin"

  foreach ($required in @(
    $flashIdPath,$ptBinPath,$ptCsvPath,$fullAPath,$fullBPath
  )) {
    if (-not (Test-Path -LiteralPath $required)) {
      throw "Required case file is missing: $required"
    }
  }

  $flashIdText = Get-Content -LiteralPath $flashIdPath -Raw
  $flashMatch = [regex]::Match(
    $flashIdText,
    '(?im)^\s*Detected flash size:\s*(\d+)\s*(MB|KB)\s*$'
  )
  if (-not $flashMatch.Success) { throw "Could not parse size from flash-id log" }
  $capacityNumber = [int64]$flashMatch.Groups[1].Value
  $capacityUnit = $flashMatch.Groups[2].Value.ToUpperInvariant()
  if ($capacityUnit -eq 'MB') {
    $flashSize = $capacityNumber * 1MB
  } else {
    $flashSize = $capacityNumber * 1KB
  }
  if (($flashSize % 1MB) -ne 0) { throw "Flash size is not a whole number of MB" }
  $flashSizeLabel = "$([int64]($flashSize / 1MB))MB"
  $supported = @('1MB','2MB','4MB','8MB','16MB','32MB','64MB','128MB')
  if ($flashSizeLabel -notin $supported) {
    throw "Partition tool does not support flash size $flashSizeLabel"
  }

  $macEvidencePaths = @($readMacPath,$flashIdPath) |
    Where-Object { Test-Path -LiteralPath $_ }
  $macEvidenceText = ($macEvidencePaths | ForEach-Object {
    Get-Content -LiteralPath $_ -Raw
  }) -join "`n"
  $actualMac = Get-UniqueMacFromText -Text $macEvidenceText
  if ($actualMac -ne $ExpectedBaseMac.ToLowerInvariant()) {
    throw "Evidence MAC $actualMac differs from expected MAC $ExpectedBaseMac"
  }

  $fullA = Get-Item -LiteralPath $fullAPath
  $fullB = Get-Item -LiteralPath $fullBPath
  if (($fullA.Length -ne $flashSize) -or ($fullB.Length -ne $flashSize)) {
    throw "Full-backup length differs from detected flash size"
  }
  $fullAHash = (Get-FileHash -LiteralPath $fullAPath -Algorithm SHA256).Hash
  $fullBHash = (Get-FileHash -LiteralPath $fullBPath -Algorithm SHA256).Hash
  if ($fullAHash -ne $fullBHash) { throw "Full-backup A/B hashes differ" }
  Assert-FlashRegionMatches -Source $fullAPath `
    -Offset $PartitionTableOffset -Length $PartitionTableSize `
    -RegionFile $ptBinPath | Out-Null
  if (-not (Get-Variable -Name GenPartWsl -Scope Global `
      -ErrorAction SilentlyContinue)) {
    throw "Missing context variable: GenPartWsl"
  }
  Assert-PartitionCsvMatches `
    -PartitionBinWsl "$caseRootWsl/01_ptable/pt.bin" `
    -PartitionCsvWin $ptCsvPath `
    -FlashSizeText $flashSizeLabel `
    -GenPartWslPath $global:GenPartWsl

  $partitionLines = Get-Content -LiteralPath $ptCsvPath |
    Where-Object { $_.Trim() -and ($_ -notmatch '^\s*#') }
  $parts = @($partitionLines | ConvertFrom-Csv `
    -Header Name,Type,SubType,Offset,Size,Flags)
  $nvsParts = @($parts | Where-Object {
    $_.Name -eq 'nvs' -and $_.Type -eq 'data'
  })
  $phyInitParts = @($parts | Where-Object {
    $_.Name -eq 'phy_init' -and $_.Type -eq 'data'
  })
  $appParts = @($parts | Where-Object { $_.Type -eq 'app' })
  if ($nvsParts.Count -ne 1) { throw "Did not find exactly one nvs partition" }
  if ($phyInitParts.Count -ne 1) {
    throw "Did not find exactly one phy_init partition"
  }
  if ($appParts.Count -ne 1) {
    throw "App partition is not unique; identify the active App first"
  }

  $nvsOffset = Convert-PartitionNumber $nvsParts[0].Offset
  $nvsSize = Convert-PartitionNumber $nvsParts[0].Size
  $phyInitOffset = Convert-PartitionNumber $phyInitParts[0].Offset
  $phyInitSize = Convert-PartitionNumber $phyInitParts[0].Size
  $appName = $appParts[0].Name
  $appOffset = Convert-PartitionNumber $appParts[0].Offset
  $appSize = Convert-PartitionNumber $appParts[0].Size

  $nvsImagePath = Join-Path $caseRoot "00_backup\$SampleName-nvs.bin"
  $phyInitImagePath = Join-Path $caseRoot "02_idfver\$SampleName-phy_init.bin"
  $appImagePath = Join-Path $caseRoot "02_idfver\$SampleName-$appName-app.bin"
  foreach ($required in @($nvsImagePath,$phyInitImagePath,$appImagePath)) {
    if (-not (Test-Path -LiteralPath $required)) {
      throw "Required derived image is missing: $required"
    }
  }
  Assert-FlashRegionMatches -Source $fullAPath `
    -Offset $nvsOffset -Length $nvsSize `
    -RegionFile $nvsImagePath | Out-Null
  Assert-FlashRegionMatches -Source $fullAPath `
    -Offset $phyInitOffset -Length $phyInitSize `
    -RegionFile $phyInitImagePath | Out-Null
  Assert-FlashRegionMatches -Source $fullAPath `
    -Offset $appOffset -Length $appSize `
    -RegionFile $appImagePath | Out-Null

  # Commit the context only after every identity and evidence gate has passed.
  $global:Sample = $SampleName
  $global:Port = $SerialPort
  $global:ExpectedMac = $ExpectedBaseMac.ToLowerInvariant()
  $global:ActualMac = $actualMac
  $global:CaseRoot = $caseRoot
  $global:CaseRootWsl = $caseRootWsl
  $global:FlashSize = $flashSize
  $global:FlashSizeLabel = $flashSizeLabel
  $global:NvsOffset = $nvsOffset
  $global:NvsSize = $nvsSize
  $global:PhyInitOffset = $phyInitOffset
  $global:PhyInitSize = $phyInitSize
  $global:AppName = $appName
  $global:AppOffset = $appOffset
  $global:AppSize = $appSize

  [pscustomobject]@{
    Sample = $global:Sample
    Port = $global:Port
    MAC = $global:ActualMac
    Flash = $global:FlashSizeLabel
    NvsOffset = ('0x{0:X}' -f $nvsOffset)
    NvsSize = ('0x{0:X}' -f $nvsSize)
    PhyInitOffset = ('0x{0:X}' -f $phyInitOffset)
    PhyInitSize = ('0x{0:X}' -f $phyInitSize)
    App = $appName
    AppOffset = ('0x{0:X}' -f $appOffset)
    AppSize = ('0x{0:X}' -f $appSize)
    FullFlashSHA256 = $fullAHash
  }
}

function Confirm-PhySampleIdentity {
  $macOutput = @(py -m esptool --chip esp32c2 --port $Port --baud 115200 `
    --before no-reset --after no-reset read-mac 2>&1)
  $exitVariable = Get-Variable -Name LASTEXITCODE -ErrorAction SilentlyContinue
  $macExit = if ($null -eq $exitVariable) { -1 } else { $exitVariable.Value }
  $macOutput | Out-Host
  if ($macExit -ne 0) { throw "MAC read failed" }
  $actualMac = Get-UniqueMacFromText -Text ($macOutput -join "`n")
  if ($actualMac -ne $ExpectedMac.ToLowerInvariant()) {
    throw "Wrong sample: measured $actualMac, expected $ExpectedMac"
  }
  return $actualMac
}

function Save-PhySnapshot {
  param(
    [Parameter(Mandatory=$true)]
    [ValidateSet('03_P1','08_measure')]
    [string]$Folder,
    [Parameter(Mandatory=$true)][string]$Tag
  )

  if ($Tag -notmatch '^[A-Za-z0-9_-]+$') {
    throw "Tag may contain only letters, digits, underscore, and hyphen"
  }
  foreach ($name in @(
    'Sample','Port','ExpectedMac','CaseRoot','CaseRootWsl',
    'NvsOffset','NvsSize','WslExe','NvsParserDirWsl','NvsToolWsl','PhySummaryWsl'
  )) {
    if (-not (Get-Variable -Name $name -Scope Global -ErrorAction SilentlyContinue)) {
      throw "Missing context variable: $name"
    }
  }

  $binWin = "$CaseRoot\$Folder\$Sample-$Tag-nvs.bin"
  $binWsl = "$CaseRootWsl/$Folder/$Sample-$Tag-nvs.bin"
  $readLog = "$CaseRoot\$Folder\$Sample-$Tag-read.txt"
  $macLog = "$CaseRoot\$Folder\$Sample-$Tag-mac.txt"
  $checkLog = "$CaseRoot\$Folder\$Sample-$Tag-nvs-check.txt"
  $summaryLog = "$CaseRoot\$Folder\$Sample-$Tag-phy-summary.txt"
  Assert-NewEvidencePaths -Paths @(
    $binWin,$readLog,$macLog,$checkLog,$summaryLog
  )

  $macOutput = @(py -m esptool --chip esp32c2 --port $Port --baud 115200 `
    --before no-reset --after no-reset read-mac 2>&1)
  $exitVariable = Get-Variable -Name LASTEXITCODE -ErrorAction SilentlyContinue
  $macExit = if ($null -eq $exitVariable) { -1 } else { $exitVariable.Value }
  $macOutput
  if ($macExit -ne 0) {
    throw "$Tag MAC read failed; no formal snapshot file was created"
  }
  $snapshotMac = Get-UniqueMacFromText -Text ($macOutput -join "`n")
  if ($snapshotMac -ne $ExpectedMac.ToLowerInvariant()) {
    throw "$Tag wrong sample: measured $snapshotMac, expected $ExpectedMac; no formal snapshot file was created"
  }
  $macOutput | Tee-Object $macLog

  py -m esptool --chip esp32c2 --port $Port --baud 115200 `
    --before no-reset --after no-reset read-flash $NvsOffset $NvsSize `
    $binWin 2>&1 | Tee-Object $readLog
  $exitVariable = Get-Variable -Name LASTEXITCODE -ErrorAction SilentlyContinue
  $readExit = if ($null -eq $exitVariable) { -1 } else { $exitVariable.Value }
  if ($readExit -ne 0) { throw "$Tag NVS read failed" }
  if ((Get-Item -LiteralPath $binWin).Length -ne $NvsSize) {
    throw "$Tag NVS length mismatch"
  }

  & $WslExe python3 "$NvsToolWsl" --integrity-check --dump namespaces --color never `
    $binWsl 2>&1 | Tee-Object $checkLog
  $exitVariable = Get-Variable -Name LASTEXITCODE -ErrorAction SilentlyContinue
  $nvsExit = if ($null -eq $exitVariable) { -1 } else { $exitVariable.Value }
  Assert-NvsIntegrityLog -Path $checkLog -ExitCode $nvsExit `
    -ExpectedSize $NvsSize

  & $WslExe python3 "$PhySummaryWsl" --strict --parser-dir "$NvsParserDirWsl" `
    --expected-mac "$ExpectedMac" `
    $binWsl 2>&1 | Tee-Object $summaryLog
  $exitVariable = Get-Variable -Name LASTEXITCODE -ErrorAction SilentlyContinue
  $summaryExit = if ($null -eq $exitVariable) { -1 } else { $exitVariable.Value }
  if ($summaryExit -ne 0) { throw "$Tag PHY summary failed" }
  Get-Content -LiteralPath $summaryLog
}
