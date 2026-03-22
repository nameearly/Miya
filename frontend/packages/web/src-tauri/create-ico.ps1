Add-Type -AssemblyName System.Drawing
$iconPath = "D:\AI_MIYA_Facyory\MIYA\Miya\frontend\packages\web\src-tauri\icons"

$sizes = @(16, 32, 48, 256)
$bitmaps = @()

foreach ($size in $sizes) {
    $bmp = New-Object System.Drawing.Bitmap($size, $size)
    $g = [System.Drawing.Graphics]::FromImage($bmp)
    $g.SmoothingMode = [System.Drawing.Drawing2D.SmoothingMode]::AntiAlias
    
    $g.Clear([System.Drawing.Color]::FromArgb(0,135,212))
    $g.FillEllipse([System.Drawing.Brushes]::White, [int]($size*0.18), [int]($size*0.18), [int]($size*0.64), [int]($size*0.64))
    
    $fontSize = [int]($size * 0.35)
    if ($fontSize -lt 8) { $fontSize = 8 }
    $brush = New-Object System.Drawing.SolidBrush([System.Drawing.Color]::FromArgb(0,135,212))
    $font = New-Object System.Drawing.Font("Arial", $fontSize, [System.Drawing.FontStyle]::Bold)
    $sf = New-Object System.Drawing.StringFormat
    $sf.Alignment = [System.Drawing.StringAlignment]::Center
    $sf.LineAlignment = [System.Drawing.StringAlignment]::Center
    $rect = New-Object System.Drawing.RectangleF(0, 0, $size, $size)
    $g.DrawString("M", $font, $brush, $rect, $sf)
    
    $g.Dispose()
    $bitmaps += $bmp
}

$ms = New-Object System.IO.MemoryStream
$bw = New-Object System.IO.BinaryWriter($ms)

$bw.Write([int16]0)
$bw.Write([int16]1)
$bw.Write([int16]$bitmaps.Count)

$dataOffset = 6 + ($bitmaps.Count * 16)
$imageData = @()

foreach ($bmp in $bitmaps) {
    $pngStream = New-Object System.IO.MemoryStream
    $bmp.Save($pngStream, [System.Drawing.Imaging.ImageFormat]::Png)
    $pngBytes = $pngStream.ToArray()
    $imageData += ,$pngBytes
    
    $width = if ($bmp.Width -ge 256) { 0 } else { $bmp.Width }
    $height = if ($bmp.Height -ge 256) { 0 } else { $bmp.Height }
    
    $bw.Write([byte]$width)
    $bw.Write([byte]$height)
    $bw.Write([byte]0)
    $bw.Write([byte]0)
    $bw.Write([int16]1)
    $bw.Write([int16]32)
    $bw.Write([int32]$pngBytes.Length)
    $bw.Write([int32]$dataOffset)
    
    $dataOffset += $pngBytes.Length
    $pngStream.Dispose()
}

foreach ($data in $imageData) {
    $bw.Write($data)
}

$icoPath = Join-Path $iconPath "icon.ico"
[System.IO.File]::WriteAllBytes($icoPath, $ms.ToArray())

foreach ($bmp in $bitmaps) {
    $bmp.Dispose()
}
$bw.Dispose()
$ms.Dispose()

Write-Host "ICO file created at: $icoPath"
