"""Core functionality for aicommit-cli."""

import os
import subprocess
from pathlib import Path
from dotenv import load_dotenv

# 直接引用新版 SDK，不要放在 try 裡面，如果沒裝就讓它報錯
from google import genai

# 載入 .env
# 策略：優先讀取使用者當前執行目錄下的 .env，其次讀取安裝目錄下的 .env
current_dir_env = Path.cwd() / '.env'
package_dir_env = Path(__file__).parent.parent / '.env'

if current_dir_env.exists():
    load_dotenv(current_dir_env)
elif package_dir_env.exists():
    load_dotenv(package_dir_env)

API_KEY = os.getenv("GEMINI_API_KEY")

def get_api_key():
    """取得 Gemini API 金鑰。"""
    if not API_KEY:
        print("❌ Error: 找不到 GEMINI_API_KEY")
        print("請在當前目錄建立 .env 檔案，內容：GEMINI_API_KEY=你的金鑰")
        return None
    return API_KEY

def get_git_diff():  # 這裡建議改名，因為它抓的是 Diff 不是 Message
    """取得Git暫存區的變更(Diff)。"""
    try:
        # 執行 git diff --staged
        result = subprocess.run(
            ["git", "diff", "--staged"], 
            capture_output=True, 
            text=True, 
            check=True
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError:
        # 這通常代表不是 git 專案
        return None
    except FileNotFoundError:
        print("❌ 錯誤：找不到 git 指令，請確認已安裝 git。")
        return None

def generate_commit_message(diff_content):
    """使用 Gemini 生成 Commit 訊息"""
    if not diff_content:
        return None
        
    key = get_api_key()
    if not key:
        return None

    # 限制長度
    if len(diff_content) > 3000:
        diff_content = diff_content[:3000] + "\n...(略)..."

    prompt = f"""
    你是一個資深的軟體工程師。請根據以下的 git diff 內容，生成一個符合 'Conventional Commits' 規範的 commit message。

    規範要求：
    1. 格式為：<type>: <subject>
    2. type 只能是：feat, fix, docs, style, refactor, test, chore, perf, ci, build, revert
    3. subject 用繁體中文，簡潔有力，不超過 50 個字。
    4. 不要輸出 Markdown 格式 (如 ```)，只輸出純文字訊息。

    Git Diff 內容：
    {diff_content}
    """

    try:
        client = genai.Client(api_key=key)
        # 建議使用穩定版模型，或者統一用 gemini-2.0-flash
        response = client.models.generate_content(
            model='gemini-2.5-flash-lite', 
            contents=prompt
        )
        return response.text.strip()
    except Exception as e:
        print(f"❌ AI 生成失敗: {e}")
        return None

def validate_commit_message(message):
    """驗證 commit 訊息格式"""
    allowed_types = ['feat', 'fix', 'docs', 'style', 'refactor', 'test', 'chore', 'perf', 'ci', 'build', 'revert']
    
    if not message or not message.strip():
        return False, "commit 訊息不可為空"
    
    if ':' not in message:
        return False, f"格式錯誤：缺少冒號(:)\n正確格式: <type>: <subject>"
    
    parts = message.split(':', 1)
    commit_type = parts[0].strip()
    
    if commit_type not in allowed_types:
        return False, f"不合法的 type: '{commit_type}'\n允許列表: {', '.join(allowed_types)}"
        
    return True, ""