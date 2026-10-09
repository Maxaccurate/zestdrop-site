# Opens one ZestDrop tool window with --debug-tool and saves a picture of it (PrintWindow), then closes it.
# Used for combined tool windows, which the app's own --debug-tool-render mode does not cover.
#   capture-window.ps1 -App <ZestDrop.exe> -Tool merge:cropRotate -File <photo.png> -Lang en -Out <shot.png>
param(
    [Parameter(Mandatory)] [string] $App,
    [Parameter(Mandatory)] [string] $Tool,
    [Parameter(Mandatory)] [string] $File,
    [Parameter(Mandatory)] [ValidateSet('en', 'zh')] [string] $Lang,
    [Parameter(Mandatory)] [string] $Out,
    [int] $WaitSeconds = 9
)
$ErrorActionPreference = 'Stop'
Add-Type -AssemblyName System.Drawing
Add-Type @'
using System;
using System.Runtime.InteropServices;
public static class ZdWindowCapture
{
    [StructLayout(LayoutKind.Sequential)] public struct RECT { public int Left, Top, Right, Bottom; }
    [DllImport("user32.dll")] public static extern bool GetWindowRect(IntPtr hwnd, out RECT rect);
    [DllImport("user32.dll")] public static extern bool PrintWindow(IntPtr hwnd, IntPtr hdc, uint flags);
    [DllImport("dwmapi.dll")] public static extern int DwmGetWindowAttribute(IntPtr hwnd, int attribute, out RECT rect, int size);
}
'@
$env:ZESTDROP_LANG = $Lang
$process = Start-Process -FilePath $App -ArgumentList @('--debug-tool', $Tool, "`"$File`"") -WorkingDirectory (Split-Path -LiteralPath $App) -PassThru
try {
    $deadline = (Get-Date).AddSeconds(30)
    while ($process.MainWindowHandle -eq [IntPtr]::Zero -and (Get-Date) -lt $deadline) { Start-Sleep -Milliseconds 300; $process.Refresh() }
    if ($process.MainWindowHandle -eq [IntPtr]::Zero) { throw 'The tool window did not open.' }
    Start-Sleep -Seconds $WaitSeconds   # let the preview load
    $hwnd = $process.MainWindowHandle
    $rect = New-Object ZdWindowCapture+RECT
    [ZdWindowCapture]::GetWindowRect($hwnd, [ref]$rect) | Out-Null
    $width = $rect.Right - $rect.Left; $height = $rect.Bottom - $rect.Top
    $bitmap = New-Object System.Drawing.Bitmap $width, $height, ([System.Drawing.Imaging.PixelFormat]::Format32bppArgb)
    $graphics = [System.Drawing.Graphics]::FromImage($bitmap)
    $hdc = $graphics.GetHdc()
    $ok = [ZdWindowCapture]::PrintWindow($hwnd, $hdc, 2)   # PW_RENDERFULLCONTENT
    $graphics.ReleaseHdc($hdc); $graphics.Dispose()
    if (-not $ok) { throw 'PrintWindow failed.' }
    $bitmap.Save($Out, [System.Drawing.Imaging.ImageFormat]::Png); $bitmap.Dispose()
    "{0}x{1} -> {2}" -f $width, $height, $Out
}
finally {
    if (-not $process.HasExited) { $process.CloseMainWindow() | Out-Null; if (-not $process.WaitForExit(3000)) { $process.Kill() } }
}
