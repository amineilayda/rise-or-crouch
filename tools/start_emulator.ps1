# Pixel_4a emülatörünü temiz başlatır.
#
# Emülatör yarıda kapanınca AVD klasöründe kilit dosyaları (*.lock) kalıyor ve
# bir sonraki açılış "The Android emulator exited with code 1" hatası veriyor.
# Bu betik takılı kalmış emülatörü kapatır, kilitleri siler ve sıfırdan açar.
#
# Kullanım:  powershell -ExecutionPolicy Bypass -File tools\start_emulator.ps1

param([string]$Avd = "Pixel_4a")

$sdk = "$env:LOCALAPPDATA\Android\sdk"
$adb = "$sdk\platform-tools\adb.exe"
$avdDir = "$env:USERPROFILE\.android\avd\$Avd.avd"

Write-Host "Takılı kalmış emülatör varsa kapatılıyor..."
Get-Process -Name "qemu-system*", "emulator*" -ErrorAction SilentlyContinue | Stop-Process -Force
Start-Sleep -Seconds 2

Write-Host "Kilit dosyaları siliniyor..."
Get-ChildItem $avdDir -Filter *.lock -Recurse -Force -ErrorAction SilentlyContinue | Remove-Item -Recurse -Force

Write-Host "$Avd temiz başlatılıyor (cold boot)..."
Start-Process "$sdk\emulator\emulator.exe" -ArgumentList "-avd", $Avd, "-no-snapshot-load"

Write-Host "Açılması bekleniyor..."
for ($i = 0; $i -lt 60; $i++) {
    $booted = (& $adb shell getprop sys.boot_completed 2>$null)
    if ("$booted".Trim() -eq "1") {
        Write-Host "Emülatör hazır. Şimdi 'flutter run' çalıştırabilirsin."
        exit 0
    }
    Start-Sleep -Seconds 5
}
Write-Host "Emülatör 5 dakikada açılmadı. Android Studio > Device Manager'dan Cold Boot dene."
exit 1
