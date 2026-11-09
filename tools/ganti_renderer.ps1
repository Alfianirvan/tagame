# Berpindah mode renderer di project.godot.
# Pemakaian:
#   .\tools\ganti_renderer.ps1 lokal   -> Vulkan (Mobile) untuk tes di laptop yang OpenGL-nya bermasalah
#   .\tools\ganti_renderer.ps1 web     -> Compatibility (OpenGL) untuk export Web
#   .\tools\ganti_renderer.ps1         -> tampilkan mode saat ini
# Tutup editor Godot dulu, atau pilih Project > Reload Current Project setelahnya.
param([ValidateSet('lokal', 'web', '')][string]$Mode = '')

$file = Join-Path $PSScriptRoot '..\project.godot'
$text = [System.IO.File]::ReadAllText($file)

# Hapus semua baris renderer lama, lalu tulis ulang sesuai mode
$pola = '(?m)^renderer/rendering_method[^\r\n]*\r?\n'

if ($Mode -eq '') {
    $m = [regex]::Match($text, '(?m)^renderer/rendering_method="([^"]+)"')
    if ($m.Success) { "Mode saat ini: $($m.Groups[1].Value)" } else { 'Baris renderer tidak ditemukan.' }
    return
}

if ($Mode -eq 'lokal') {
    $baru = "renderer/rendering_method=`"mobile`"`nrenderer/rendering_method.mobile=`"gl_compatibility`"`nrenderer/rendering_method.web=`"gl_compatibility`"`n"
} else {
    $baru = "renderer/rendering_method=`"gl_compatibility`"`nrenderer/rendering_method.mobile=`"gl_compatibility`"`n"
}

if (-not [regex]::IsMatch($text, $pola)) { throw 'Baris renderer tidak ditemukan di project.godot.' }

# Ganti blok baris renderer pertama, hapus sisanya (bila ada)
$text = [regex]::Replace($text, $pola, '')
$text = $text -replace '(?m)^(\[rendering\]\r?\n\r?\n?)', "`$1$baru"
[System.IO.File]::WriteAllText($file, $text, (New-Object System.Text.UTF8Encoding($false)))
"Mode diubah ke: $Mode"
