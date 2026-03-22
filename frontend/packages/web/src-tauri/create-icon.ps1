Add-Type -AssemblyName System.Drawing
$bmp = New-Object System.Drawing.Bitmap(256,256)
$g = [System.Drawing.Graphics]::FromImage($bmp)
$g.Clear([System.Drawing.Color]::FromArgb(0,135,212))
$g.FillEllipse([System.Drawing.Brushes]::White, 48, 48, 160, 160)
$brush = New-Object System.Drawing.SolidBrush([System.Drawing.Color]::FromArgb(0,135,212))
$g.DrawString("M", (New-Object System.Drawing.Font("Arial", 80, [System.Drawing.FontStyle]::Bold)), $brush, 88, 68)
$bmp.Save("D:\AI_MIYA_Facyory\MIYA\Miya\frontend\packages\web\src-tauri\icons\icon.png", [System.Drawing.Imaging.ImageFormat]::Png)
$g.Dispose()
$bmp.Dispose()
Write-Host "Icon created successfully"
