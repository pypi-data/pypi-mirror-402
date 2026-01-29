#!/bin/bash

# aicommit-joy 自動安裝腳本
# 支援從 PyPI 安裝，適合非 Python 專案使用

set -e  # 遇到錯誤立即停止

echo "🚀 aicommit-joy 安裝程式"
echo "========================"
echo ""

# 顏色定義
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 檢查 Python 版本
check_python() {
    if command -v python3 &> /dev/null; then
        PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
        PYTHON_MAJOR=$(echo $PYTHON_VERSION | cut -d. -f1)
        PYTHON_MINOR=$(echo $PYTHON_VERSION | cut -d. -f2)
        
        if [ "$PYTHON_MAJOR" -ge 3 ] && [ "$PYTHON_MINOR" -ge 10 ]; then
            echo -e "${GREEN}✅ 找到 Python $PYTHON_VERSION${NC}"
            return 0
        else
            echo -e "${YELLOW}⚠️  Python 版本過舊: $PYTHON_VERSION (需要 3.10+)${NC}"
            return 1
        fi
    else
        echo -e "${RED}❌ 找不到 Python 3${NC}"
        return 1
    fi
}

# 提示安裝 Python
install_python_guide() {
    echo ""
    echo -e "${YELLOW}📦 請先安裝 Python 3.10 或更高版本${NC}"
    echo ""
    
    if [[ "$OSTYPE" == "darwin"* ]]; then
        echo "macOS 安裝方式："
        echo "  1. 使用 Homebrew (推薦):"
        echo "     brew install python@3.12"
        echo ""
        echo "  2. 或從官網下載："
        echo "     https://www.python.org/downloads/"
    elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
        echo "Linux 安裝方式："
        echo "  Ubuntu/Debian:"
        echo "    sudo apt update && sudo apt install python3.12"
        echo ""
        echo "  Fedora:"
        echo "    sudo dnf install python3.12"
        echo ""
        echo "  或從官網下載："
        echo "    https://www.python.org/downloads/"
    fi
    
    echo ""
    exit 1
}

# 檢查並安裝 pipx
install_pipx() {
    if command -v pipx &> /dev/null; then
        echo -e "${GREEN}✅ 找到 pipx${NC}"
        return 0
    fi
    
    echo -e "${YELLOW}📦 正在安裝 pipx...${NC}"
    
    if [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS
        if command -v brew &> /dev/null; then
            brew install pipx
            pipx ensurepath
        else
            python3 -m pip install --user pipx
            python3 -m pipx ensurepath
        fi
    elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
        # Linux
        python3 -m pip install --user pipx
        python3 -m pipx ensurepath
    else
        echo -e "${RED}❌ 不支援的作業系統${NC}"
        exit 1
    fi
    
    echo -e "${GREEN}✅ pipx 安裝完成${NC}"
    echo ""
}

# 檢查是否已安裝 aicommit-joy
check_existing_installation() {
    if pipx list | grep -q "aicommit-joy"; then
        echo -e "${YELLOW}⚠️  偵測到已安裝 aicommit-joy${NC}"
        echo ""
        read -p "是否要升級到最新版本? (y/n): " -n 1 -r
        echo ""
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            echo "📦 正在升級 aicommit-joy..."
            pipx upgrade aicommit-joy
            echo -e "${GREEN}✅ 升級完成！${NC}"
            return 0
        else
            echo "跳過安裝。"
            return 1
        fi
    fi
    return 0
}

# 安裝 aicommit-joy
install_aicommit() {
    # 檢查是否在專案目錄中（有 pyproject.toml）
    SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
    
    if [ -f "$SCRIPT_DIR/pyproject.toml" ] && grep -q "aicommit-joy" "$SCRIPT_DIR/pyproject.toml"; then
        echo "📍 偵測到本地開發版本"
        read -p "要安裝本地版本 (L) 還是 PyPI 版本 (P)? (L/P): " -n 1 -r
        echo ""
        
        if [[ $REPLY =~ ^[Ll]$ ]]; then
            echo "📦 正在從本地安裝 aicommit-joy..."
            pipx install -e "$SCRIPT_DIR" --force
        else
            echo "📦 正在從 PyPI 安裝 aicommit-joy..."
            pipx install aicommit-joy
        fi
    else
        echo "📦 正在從 PyPI 安裝 aicommit-joy..."
        pipx install aicommit-joy
    fi
    
    echo ""
    echo -e "${GREEN}✅ aicommit-joy 安裝完成！${NC}"
}

# 設定 API 金鑰
setup_api_key() {
    echo ""
    echo "🔑 設定 Gemini API 金鑰"
    echo "------------------------"
    echo ""
    echo "aicommit 需要 Google Gemini API 金鑰才能運作。"
    echo "你可以在這裡免費取得: https://aistudio.google.com/apikey"
    echo ""
    
    read -p "是否要現在設定 API 金鑰? (y/n): " -n 1 -r
    echo ""
    
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        read -p "請輸入您的 Gemini API 金鑰: " API_KEY
        
        if [ -n "$API_KEY" ]; then
            # 在當前目錄建立 .env
            echo "GEMINI_API_KEY=$API_KEY" > .env
            echo -e "${GREEN}✅ API 金鑰已儲存到當前目錄的 .env 檔案${NC}"
            echo ""
            echo "💡 提示: 每個專案都需要有 .env 檔案"
            echo "   你可以複製這個檔案到其他專案，或在每個專案中執行相同設定"
        else
            echo -e "${YELLOW}⚠️  未設定 API 金鑰${NC}"
            show_manual_setup_guide
        fi
    else
        show_manual_setup_guide
    fi
}

# 顯示手動設定指南
show_manual_setup_guide() {
    echo ""
    echo "📝 手動設定 API 金鑰："
    echo "   在你的專案目錄建立 .env 檔案："
    echo "   echo \"GEMINI_API_KEY=your_api_key_here\" > .env"
    echo ""
}

# 驗證安裝
verify_installation() {
    echo ""
    echo "🔍 驗證安裝..."
    
    if command -v aicommit &> /dev/null; then
        VERSION=$(aicommit --version 2>&1 || echo "unknown")
        echo -e "${GREEN}✅ aicommit 命令可用${NC}"
        echo "   版本: $VERSION"
        echo ""
        return 0
    else
        echo -e "${RED}❌ aicommit 命令無法執行${NC}"
        echo ""
        echo "請嘗試："
        echo "  1. 重新開啟終端機"
        echo "  2. 執行: pipx ensurepath"
        echo "  3. 或手動添加到 PATH: export PATH=\"\$HOME/.local/bin:\$PATH\""
        echo ""
        return 1
    fi
}

# 顯示使用說明
show_usage() {
    echo ""
    echo "🎉 安裝完成！"
    echo ""
    echo -e "${GREEN}使用方式：${NC}"
    echo "  1. 在任何 Git 專案中執行 'git add .'"
    echo "  2. 執行 'aicommit'"
    echo ""
    echo -e "${GREEN}測試安裝：${NC}"
    echo "  aicommit --help"
    echo ""
    echo "📚 更多資訊: https://github.com/Joy0130/SmartCommit"
    echo ""
}

# 主程式流程
main() {
    # 1. 檢查 Python
    if ! check_python; then
        install_python_guide
    fi
    
    echo ""
    
    # 2. 安裝 pipx
    install_pipx
    
    # 3. 檢查現有安裝
    if ! check_existing_installation; then
        exit 0
    fi
    
    # 4. 安裝 aicommit-joy
    install_aicommit
    
    # 5. 設定 API 金鑰
    setup_api_key
    
    # 6. 驗證安裝
    if verify_installation; then
        # 7. 顯示使用說明
        show_usage
    fi
}

# 執行主程式
main
