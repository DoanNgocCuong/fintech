# ===========================================
# 📦 XNO FULL INSTALLATION SCRIPT
# ===========================================
# Script này cài đặt TẤT CẢ dependencies cần thiết cho xno
# Chạy script này trong PowerShell: .\install_xno_full.ps1

Write-Host "🚀 Bắt đầu cài đặt XNO Full Dependencies..." -ForegroundColor Green

# ===========================================
# STEP 1: ACTIVATE VIRTUAL ENVIRONMENT
# ===========================================
Write-Host "`n📁 Activating virtual environment..." -ForegroundColor Yellow
& ".\.venv\Scripts\activate"

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Không thể activate .venv! Đảm bảo bạn đang ở trong project folder." -ForegroundColor Red
    exit 1
}

Write-Host "✅ Virtual environment activated!" -ForegroundColor Green

# ===========================================
# STEP 2: UPGRADE PIP
# ===========================================
Write-Host "`n🔧 Upgrading pip..." -ForegroundColor Yellow
python -m pip install --upgrade pip

# ===========================================
# STEP 3: INSTALL CORE DATA PROCESSING
# ===========================================
Write-Host "`n📊 Installing core data processing libraries..." -ForegroundColor Yellow

# Fix numpy version for TA-Lib compatibility
Write-Host "   - Installing compatible numpy version..." -ForegroundColor Cyan
pip install "numpy>=1.21.0,<2.0"

# Core data processing
Write-Host "   - Installing pandas..." -ForegroundColor Cyan
pip install "pandas>=1.5.0"

Write-Host "   - Installing scipy..." -ForegroundColor Cyan
pip install "scipy>=1.7.0"

# ===========================================
# STEP 4: INSTALL TA-LIB DEPENDENCIES
# ===========================================
Write-Host "`n📈 Installing TA-Lib dependencies..." -ForegroundColor Yellow

Write-Host "   - Installing protobuf..." -ForegroundColor Cyan
pip install protobuf

Write-Host "   - Installing Cython..." -ForegroundColor Cyan
pip install Cython

# ===========================================
# STEP 5: INSTALL DATABASE DEPENDENCIES
# ===========================================
Write-Host "`n🗄️ Installing database dependencies..." -ForegroundColor Yellow

Write-Host "   - Installing SQLAlchemy..." -ForegroundColor Cyan
pip install "sqlalchemy>=1.4.0"

Write-Host "   - Installing PostgreSQL driver..." -ForegroundColor Cyan
pip install psycopg2-binary

Write-Host "   - Installing Redis client..." -ForegroundColor Cyan
pip install redis

# ===========================================
# STEP 6: INSTALL PROGRESS & UTILITIES
# ===========================================
Write-Host "`n🛠️ Installing utility libraries..." -ForegroundColor Yellow

Write-Host "   - Installing tqdm..." -ForegroundColor Cyan
pip install tqdm

Write-Host "   - Installing requests..." -ForegroundColor Cyan
pip install requests

Write-Host "   - Installing click..." -ForegroundColor Cyan
pip install click

# ===========================================
# STEP 7: INSTALL VIETNAMESE STOCK DATA
# ===========================================
Write-Host "`n🇻🇳 Installing Vietnamese stock data libraries..." -ForegroundColor Yellow

Write-Host "   - Installing vnstock..." -ForegroundColor Cyan
pip install "vnstock>=0.2.9"

Write-Host "   - Installing vnai..." -ForegroundColor Cyan
pip install vnai

# ===========================================
# STEP 8: INSTALL VISUALIZATION
# ===========================================
Write-Host "`n📊 Installing visualization libraries..." -ForegroundColor Yellow

Write-Host "   - Installing matplotlib..." -ForegroundColor Cyan
pip install matplotlib

Write-Host "   - Installing seaborn..." -ForegroundColor Cyan
pip install seaborn

Write-Host "   - Installing plotly..." -ForegroundColor Cyan
pip install plotly

# ===========================================
# STEP 9: INSTALL FASTAPI & WEB
# ===========================================
Write-Host "`n🌐 Installing web framework..." -ForegroundColor Yellow

Write-Host "   - Installing FastAPI..." -ForegroundColor Cyan
pip install fastapi

Write-Host "   - Installing uvicorn..." -ForegroundColor Cyan
pip install uvicorn

Write-Host "   - Installing pydantic..." -ForegroundColor Cyan
pip install pydantic

# ===========================================
# STEP 10: INSTALL ADDITIONAL UTILITIES
# ===========================================
Write-Host "`n🔧 Installing additional utilities..." -ForegroundColor Yellow

Write-Host "   - Installing beautifulsoup4..." -ForegroundColor Cyan
pip install beautifulsoup4

Write-Host "   - Installing fake-useragent..." -ForegroundColor Cyan
pip install fake-useragent

Write-Host "   - Installing openpyxl..." -ForegroundColor Cyan
pip install openpyxl

Write-Host "   - Installing xlsxwriter..." -ForegroundColor Cyan
pip install xlsxwriter

Write-Host "   - Installing wordcloud..." -ForegroundColor Cyan
pip install wordcloud

# ===========================================
# STEP 11: MANUAL TA-LIB INSTALLATION
# ===========================================
Write-Host "`n⚠️  MANUAL STEP REQUIRED: TA-Lib Installation" -ForegroundColor Red
Write-Host "`nTA-Lib cần được cài thủ công vì nó là C extension:" -ForegroundColor Yellow
Write-Host "1. Download file .whl từ: https://www.lfd.uci.edu/~gohlke/pythonlibs/#ta-lib" -ForegroundColor Cyan
Write-Host "2. Chọn file phù hợp với Python version của bạn" -ForegroundColor Cyan
Write-Host "3. Chạy: pip install path\to\downloaded\file.whl" -ForegroundColor Cyan
Write-Host "`nHoặc thử:" -ForegroundColor Yellow
Write-Host "pip install ta-lib-binary" -ForegroundColor Cyan

# ===========================================
# STEP 12: VERIFICATION
# ===========================================
Write-Host "`n🧪 Testing all imports..." -ForegroundColor Yellow

$testScript = @"
try:
    # Test core libraries
    import numpy as np
    import pandas as pd
    import scipy
    
    # Test protobuf
    import google.protobuf
    
    # Test database
    import sqlalchemy
    import psycopg2
    import redis
    
    # Test utilities
    import tqdm
    import requests
    import click
    
    # Test Vietnamese stock data
    from vnstock import Fundamental, Financial
    import vnai
    
    # Test visualization
    import matplotlib
    import seaborn
    import plotly
    
    # Test web framework
    import fastapi
    import uvicorn
    import pydantic
    
    # Test TA-Lib (might fail if not manually installed)
    try:
        import talib
        print("✅ TA-Lib: OK")
    except ImportError:
        print("⚠️  TA-Lib: Needs manual installation")
    
    print("✅ All core libraries working!")
    
except ImportError as e:
    print(f"❌ Import error: {e}")
    exit(1)
"@

python -c $testScript

if ($LASTEXITCODE -eq 0) {
    Write-Host "`n🎉 XNO FULL INSTALLATION COMPLETED!" -ForegroundColor Green
    Write-Host "`n📋 Next steps:" -ForegroundColor Yellow
    Write-Host "1. Cài TA-Lib thủ công (nếu chưa cài)" -ForegroundColor Cyan
    Write-Host "2. Test script: python fintech_comprehensive_mece.py" -ForegroundColor Cyan
    Write-Host "3. Kiểm tra requirements.txt đã được cập nhật" -ForegroundColor Cyan
} else {
    Write-Host "`n❌ Installation có vấn đề. Kiểm tra lại các bước trên." -ForegroundColor Red
}

Write-Host "`n📝 Script hoàn thành!" -ForegroundColor Green
