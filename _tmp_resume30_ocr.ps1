$ErrorActionPreference = 'Stop'
Add-Type -AssemblyName System.Runtime.WindowsRuntime

$script:asTaskGeneric = ([System.WindowsRuntimeSystemExtensions].GetMethods() |
    Where-Object { $_.Name -eq 'AsTask' -and $_.GetParameters().Count -eq 1 -and
                   $_.GetParameters()[0].ParameterType.Name -eq 'IAsyncOperation`1' })[0]

function Await {
    param($Op, [type]$T)
    $m = $script:asTaskGeneric.MakeGenericMethod($T)
    $task = $m.Invoke($null, @($Op))
    $task.Wait(-1) | Out-Null
    return $task.Result
}

$null = [Windows.Storage.StorageFile, Windows.Storage, ContentType=WindowsRuntime]
$null = [Windows.Graphics.Imaging.BitmapDecoder, Windows.Graphics.Imaging, ContentType=WindowsRuntime]
$null = [Windows.Media.Ocr.OcrEngine, Windows.Media.Ocr, ContentType=WindowsRuntime]
$null = [Windows.Media.Ocr.OcrResult, Windows.Media.Ocr, ContentType=WindowsRuntime]
$null = [Windows.Graphics.Imaging.SoftwareBitmap, Windows.Graphics.Imaging, ContentType=WindowsRuntime]
$null = [Windows.Globalization.Language, Windows.Globalization, ContentType=WindowsRuntime]
$null = [Windows.Storage.Streams.IRandomAccessStream, Windows.Storage.Streams, ContentType=WindowsRuntime]

$engine = [Windows.Media.Ocr.OcrEngine]::TryCreateFromLanguage((New-Object Windows.Globalization.Language "zh-Hans-CN"))
if ($null -eq $engine) { $engine = [Windows.Media.Ocr.OcrEngine]::TryCreateFromUserProfileLanguages() }

$dir = $args[0]
$full = $args[1]
if ($full) {
    $sf = Await -Op ([Windows.Storage.StorageFile]::GetFileFromPathAsync($full)) -T ([Windows.Storage.StorageFile])
    $st = Await -Op ($sf.OpenAsync([Windows.Storage.FileAccessMode]::Read)) -T ([Windows.Storage.Streams.IRandomAccessStream])
    $dec = Await -Op ([Windows.Graphics.Imaging.BitmapDecoder]::CreateAsync($st)) -T ([Windows.Graphics.Imaging.BitmapDecoder])
    $bmp = Await -Op ($dec.GetSoftwareBitmapAsync()) -T ([Windows.Graphics.Imaging.SoftwareBitmap])
    $res = Await -Op ($engine.RecognizeAsync($bmp)) -T ([Windows.Media.Ocr.OcrResult])
    $i = 0
    foreach ($ln in $res.Lines) {
        $y = 0
        try { $y = [int]$ln.BoundingRect.Y } catch { $y = -1 }
        Write-Host ("[FULL y=" + $y + "] " + $ln.Text)
        $i++
    }
    Write-Host ("[FULL lines] " + $i)
    exit 0
}

$files = Get-ChildItem -LiteralPath $dir -Filter 'b_*.png' | Sort-Object Name
foreach ($f in $files) {
    $sf = Await -Op ([Windows.Storage.StorageFile]::GetFileFromPathAsync($f.FullName)) -T ([Windows.Storage.StorageFile])
    $st = Await -Op ($sf.OpenAsync([Windows.Storage.FileAccessMode]::Read)) -T ([Windows.Storage.Streams.IRandomAccessStream])
    $dec = Await -Op ([Windows.Graphics.Imaging.BitmapDecoder]::CreateAsync($st)) -T ([Windows.Graphics.Imaging.BitmapDecoder])
    $bmp = Await -Op ($dec.GetSoftwareBitmapAsync()) -T ([Windows.Graphics.Imaging.SoftwareBitmap])
    $res = Await -Op ($engine.RecognizeAsync($bmp)) -T ([Windows.Media.Ocr.OcrResult])
    $parts = @()
    foreach ($ln in $res.Lines) { $parts += [string]$ln.Text }
    Write-Host ("[" + $f.BaseName + "] " + ($parts -join ' | '))
    $st.Dispose()
}
