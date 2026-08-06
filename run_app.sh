#!/bin/bash

# متوقف شدن اسکریپت در صورت بروز خطای بحرانی
set -e

# دریافت پویا و ایمن مسیر فعلی پروژه
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_ROOT"

echo "=================================================="
echo "⚙️  موتور ارکستراسیون و اجرای سیستم ارزیابی پروپوزال"
echo "=================================================="

# ۱. آزادسازی قطعی پورت 8501 با دستور ترکیبی PowerShell و Bash
echo "🧹 [1/4] آزادسازی پورت 8501 و بستن پروسه‌های معلق Streamlit..."

# اجرای مستقیم دستور PowerShell برای شناسایی و بستن اجباری پروسه پورت 8501 در ویندوز
if command -v powershell.exe &> /dev/null; then
    powershell.exe -Command "if (Get-NetTCPConnection -LocalPort 8501 -ErrorAction SilentlyContinue) { Stop-Process -Id (Get-NetTCPConnection -LocalPort 8501).OwningProcess -Force -ErrorAction SilentlyContinue }" 2>/dev/null || true
fi

# دستورات رزرو برای بستن پروسه در محیط‌های لینوکس یا WSL
pkill -9 -f "streamlit" 2>/dev/null || true
if command -v fuser &> /dev/null; then
    fuser -k -9 8501/tcp 2>/dev/null || true
fi
sleep 1

# ۲. بررسی وضعیت سرویس Ollama روی پورت 11434
echo "🔍 [2/4] بررسی وضعیت سرویس هوش مصنوعی Ollama (پورت 11434)..."
if curl -s http://localhost:11434/api/tags >/dev/null 2>&1; then
    echo "✅ سرویس Ollama فعال و آماده پاسخگویی است."
else
    echo "⚠️ سرویس Ollama در دسترس نیست! در حال تلاش برای راه‌اندازی..."
    ollama serve > /dev/null 2>&1 &
    sleep 3
fi

# ۳. شناسایی هوشمند مسیر پایتون در محیط مجازی (Windows / Linux)
echo "🐍 [3/4] بررسی و فعال‌سازی محیط ایزوله پایتون..."
PYTHON_BIN="python"

if [ -f "$PROJECT_ROOT/venv/Scripts/python.exe" ]; then
    PYTHON_BIN="$PROJECT_ROOT/venv/Scripts/python.exe"
    echo "✅ پایتون محیط مجازی ویندوز (venv/Scripts/python.exe) شناسایی شد."
elif [ -f "$PROJECT_ROOT/venv/Scripts/python" ]; then
    PYTHON_BIN="$PROJECT_ROOT/venv/Scripts/python"
    echo "✅ پایتون محیط مجازی ویندوز شناسایی شد."
elif [ -f "$PROJECT_ROOT/venv/bin/python" ]; then
    PYTHON_BIN="$PROJECT_ROOT/venv/bin/python"
    echo "✅ پایتون محیط مجازی لینوکس شناسایی شد."
else
    echo "⚠️ پوشه venv یافت نشد! از پایتون سیستم استفاده می‌شود."
fi

# تابع مدیریت خروج تمیز و آزادسازی پورت هنگام بستن برنامه
cleanup() {
    echo ""
    echo "🛑 در حال متوقف‌سازی کامل برنامه Streamlit..."
    if command -v powershell.exe &> /dev/null; then
        powershell.exe -Command "if (Get-NetTCPConnection -LocalPort 8501 -ErrorAction SilentlyContinue) { Stop-Process -Id (Get-NetTCPConnection -LocalPort 8501).OwningProcess -Force -ErrorAction SilentlyContinue }" 2>/dev/null || true
    fi
    pkill -9 -f "streamlit" 2>/dev/null || true
    exit 0
}

trap cleanup SIGINT SIGTERM

# ۴. راه‌اندازی سرویس Streamlit با پایتون محیط مجازی
echo "🚀 [4/4] در حال راه‌اندازی رابط کاربری Streamlit..."
echo "=================================================="
echo "🎯 برنامه اجرا شد. جهت متوقف‌سازی کلیدهای Ctrl+C را فشار دهید."
echo "=================================================="

"$PYTHON_BIN" -m streamlit run main.py --server.port=8501