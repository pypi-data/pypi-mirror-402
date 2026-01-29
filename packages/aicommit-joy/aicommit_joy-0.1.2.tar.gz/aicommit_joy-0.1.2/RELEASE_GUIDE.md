# GitHub Release 設定指南

## 📦 如何發布 Release（包含 install.sh）

### 方式一：使用 GitHub Web 界面（推薦）

1. **前往 Releases 頁面**
   - 在你的 repo 頁面，點擊右側的 "Releases"
   - 或直接訪問：`https://github.com/Joy0130/SmartCommit/releases`

2. **創建新 Release**
   - 點擊 "Draft a new release"
   - 填寫以下資訊：
     - **Tag version**: `v0.1.2`
     - **Release title**: `v0.1.2 - 跨平台安裝改進`
     - **Description**:

       ```markdown
       ## 新功能

       - ✅ 修復 package 配置問題
       - ✅ 改進安裝腳本，支援非 Python 專案
       - ✅ 提供完全自動化安裝體驗

       ## 安裝方式

       ### 使用 pipx（推薦）

       \`\`\`bash
       pipx install aicommit-joy
       \`\`\`

       ### 使用自動安裝腳本

       下載 install.sh 並執行：
       \`\`\`bash
       bash install.sh
       \`\`\`
       ```

3. **上傳 install.sh**
   - 在 "Attach binaries" 區域
   - 拖曳或選擇 `/Users/joy/Documents/SmartCommit/install.sh`
   - 檔案會自動上傳

4. **發布**
   - 勾選 "Set as the latest release"
   - 點擊 "Publish release"

### 方式二：使用 GitHub CLI（進階）

如果你安裝了 `gh` CLI：

```bash
cd /Users/joy/Documents/SmartCommit

# 創建 tag
git tag v0.1.2
git push origin v0.1.2

# 創建 release 並上傳 install.sh
gh release create v0.1.2 \
  --title "v0.1.2 - 跨平台安裝改進" \
  --notes "改進安裝體驗，支援非 Python 專案使用" \
  install.sh
```

---

## 🔗 用戶如何使用

發布後，用戶可以透過以下方式下載：

### 1. 手動下載

訪問：`https://github.com/Joy0130/SmartCommit/releases/latest`

### 2. 命令下載

```bash
curl -L -O https://github.com/Joy0130/SmartCommit/releases/latest/download/install.sh
bash install.sh
```

---

## 🔄 更新 Release

每次更新 install.sh 後：

1. 修改版本號（例如 v0.1.3）
2. 重新創建 tag 和 release
3. 上傳新的 install.sh

---

## 📝 自動化建議（未來）

可以使用 GitHub Actions 自動化發布流程：

```yaml
# .github/workflows/release.yml
name: Release

on:
  push:
    tags:
      - "v*"

jobs:
  release:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Create Release
        uses: softprops/action-gh-release@v1
        with:
          files: install.sh
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
```

這樣只要推送 tag 就會自動創建 release！

---

## ✅ 驗證 Release

發布後，測試下載連結：

```bash
# 測試下載
curl -L -O https://github.com/Joy0130/SmartCommit/releases/latest/download/install.sh

# 檢查檔案
ls -lh install.sh
cat install.sh | head -5
```

應該能成功下載並看到腳本內容。
