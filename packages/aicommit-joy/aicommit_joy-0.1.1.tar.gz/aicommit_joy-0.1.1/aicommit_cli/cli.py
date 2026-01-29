"""Command-line interface for aicommit-cli."""

import sys
import subprocess
from .core import (
    get_api_key,
    get_git_diff,          # 只保留這個
    generate_commit_message,
    validate_commit_message
)


def main():
    """執行主程式。"""
    # 處理命令行參數
    if len(sys.argv) > 1:
        if sys.argv[1] in ['--help', '-h']:
            print("""aicommit-cli - AI-powered Git commit message generator
                    使用方式:
                    aicommit-cli          在目前的 Git 專案中生成 commit 訊息
                    aicommit-cli --help   顯示此幫助訊息

                    功能:
                    - 自動分析 Git diff 並生成符合 Conventional Commits 規範的訊息
                    - 支援手動編輯 AI 生成的訊息
                    - 自動驗證訊息格式
                """)
            return
        
        elif sys.argv[1] == '--version':
            from . import __version__
            print(f"aicommit-cli v{__version__}")
            return
    
    # 檢查 API 金鑰
    if not get_api_key():
        return

    # 檢查是否有暫存的變更
    diff = get_git_diff()
    if not diff:
        print("⚠️ 沒有偵測到暫存的變更(Staged Changes)，如有變更請先執行 git add")
        return
    
    print("🤖 AI 正在分析程式碼變更，請稍候...")

    # 生成Commit訊息
    commit_msg = generate_commit_message(diff)

    # 檢查Commit訊息是否生成成功
    if not commit_msg:
        print("Error: 無法生成 Commit 訊息 (可能是 API 錯誤或 Token 限制)")
        return

    # 輸出Commit訊息
    print("\n------------------------------------")
    print(f"📝 建議訊息: \033[1;32m{commit_msg}\033[0m") # 綠色高亮
    print("------------------------------------")
    
    # 詢問使用者操作選項
    while True:
        user_input = input("\n請選擇操作 (y=使用/e=編輯/n=取消): ").lower()
        
        if user_input == 'y':
            # 使用AI生成的訊息提交
            subprocess.run(['git', 'commit', '-m', commit_msg])
            print("✅ 提交成功！可以使用 git push 上傳")
            break
        elif user_input == 'e':
            # 讓使用者編輯訊息
            print("\n請輸入新的 commit 訊息（按 Enter 確認）:")
            edited_msg = input(f"{commit_msg}\n> ").strip()
            
            # 如果使用者有輸入內容，驗證並使用編輯後的訊息
            if edited_msg:
                # 驗證commit訊息格式
                is_valid, error_msg = validate_commit_message(edited_msg)
                
                if not is_valid:
                    # 格式不正確，顯示錯誤訊息
                    print(f"\n{error_msg}")
                    print("請重新編輯或返回選單...\n")
                    continue
                
                # 格式正確，更新訊息
                commit_msg = edited_msg
                print(f"\n✅ 訊息格式正確！")
                print(f"📝 更新後的訊息: \033[1;32m{commit_msg}\033[0m") # 綠色高亮
                
                # 再次確認是否提交
                confirm = input("\n是否提交此訊息? (y/n): ").lower()
                if confirm == 'y':
                    subprocess.run(['git', 'commit', '-m', commit_msg])
                    print("✅ 提交成功！可以使用 git push 上傳")
                    break
                else:
                    print("返回選單...")
                    continue
            else:
                print("⚠️ 訊息不可為空，返回選單...")
                continue
        elif user_input == 'n':
            # 取消提交
            print("已取消。")
            break
        else:
            print("無效的選項，請輸入 y、e 或 n")


if __name__ == "__main__":
    main()
