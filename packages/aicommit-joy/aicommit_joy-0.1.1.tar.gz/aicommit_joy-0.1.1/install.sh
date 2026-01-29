#!/bin/bash

# aicommit-cli 安裝腳本
# 自動安裝 aicommit-cli 並設定為全域命令

set -e  # 遇到錯誤立即停止

echo "🚀 aicommit-cli 安裝程式"
echo "========================"
echo ""

# 檢查是否已安裝 pipx
if ! command -v pipx &> /dev/null; then
    echo "❌ 找不到 pipx"
    echo "📦 正在安裝 pipx..."
    
    # 檢查作業系統
    if [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS
        if command -v brew &> /dev/null; then
            brew install pipx
            pipx ensurepath
        else
            echo "❌ 請先安裝 Homebrew: https://brew.sh"
            exit 1
        fi
    elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
        # Linux
        python3 -m pip install --user pipx
        python3 -m pipx ensurepath
    else
        echo "❌ 不支援的作業系統"
        exit 1
    fi
    
    echo "✅ pipx 安裝完成"
    echo ""
fi

# 取得腳本所在目錄（aicommit-cli 專案目錄）
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

echo "📍 aicommit-cli 位置: $SCRIPT_DIR"
echo ""

# 安裝 aicommit-cli
echo "📦 正在安裝 aicommit-cli..."
pipx install -e "$SCRIPT_DIR" --force

echo ""
echo "✅ aicommit-cli 安裝完成！"
echo ""

# 檢查 .env 檔案
if [ ! -f "$SCRIPT_DIR/.env" ]; then
    echo "⚠️  找不到 .env 檔案"
    echo ""
    read -p "請輸入您的 Gemini API 金鑰: " API_KEY
    
    if [ -n "$API_KEY" ]; then
        echo "GEMINI_API_KEY=$API_KEY" > "$SCRIPT_DIR/.env"
        echo "✅ API 金鑰已儲存到 $SCRIPT_DIR/.env"
    else
        echo "⚠️  未設定 API 金鑰"
        echo "請手動建立 $SCRIPT_DIR/.env 檔案並加入："
        echo "GEMINI_API_KEY=your_api_key_here"
    fi
else
    echo "✅ 找到 .env 檔案"
fi

echo ""
echo "🎉 安裝完成！"
echo ""
echo "使用方式："
echo "  1. 在任何 Git 專案中執行 'git add .'"
echo "  2. 執行 'aicommit-cli'"
echo ""
echo "測試安裝："
echo "  aicommit-cli --help"
echo ""
