# 發布 aicommit-cli 到 PyPI

本文檔說明如何發布 aicommit-cli (套件名稱: `aicommit-cli`) 到 PyPI。

## 前置準備

1. **PyPI 帳號**: https://pypi.org/account/register/
2. **API Token**: https://pypi.org/manage/account/token/
   - 建立一個新的 API token
   - 範圍可設為「整個帳號」或「特定專案」
   - 保存好 token（格式：`pypi-...`）

## 發布流程

### 1. 更新版本號

編輯 `pyproject.toml`，更新版本號：

```toml
version = "0.1.1"  # 例如從 0.1.0 升級到 0.1.1
```

### 2. 構建套件

使用 `uv` 構建發行套件：

```bash
uv build
```

這會在 `dist/` 目錄生成兩個文件：

- `aicommit-cli-x.x.x.tar.gz` (源碼發行版)
- `aicommit-cli-x.x.x-py3-none-any.whl` (wheel 套件)

### 3. 檢查套件 (可選但推薦)

```bash
uv tool run twine check dist/*
```

### 4. 上傳到 PyPI

使用 API token 上傳：

```bash
uv tool run twine upload dist/* -u __token__ -p pypi-YOUR_API_TOKEN_HERE
```

或者使用互動式輸入（系統會提示輸入用戶名和密碼）：

```bash
uv tool run twine upload dist/*
# Username: __token__
# Password: pypi-YOUR_API_TOKEN_HERE
```

### 5. 驗證發布

訪問 PyPI 頁面確認：

- https://pypi.org/project/aicommit-cli/

測試安裝：

```bash
pip install aicommit-cli
aicommit-cli --version
```

## 測試發布 (推薦首次使用)

在首次發布前，建議先上傳到 TestPyPI 測試：

### 1. 註冊 TestPyPI 帳號

https://test.pypi.org/account/register/

### 2. 建立 TestPyPI API Token

https://test.pypi.org/manage/account/token/

### 3. 上傳到 TestPyPI

```bash
uv tool run twine upload --repository testpypi dist/* -u __token__ -p YOUR_TESTPYPI_TOKEN
```

### 4. 從 TestPyPI 安裝測試

```bash
pip install --index-url https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple aicommit-cli
```

注意：需要 `--extra-index-url` 因為依賴套件（如 `google-genai`）在正式 PyPI。

## 清理構建產物

發布後可以清理：

```bash
rm -rf dist/ build/ *.egg-info
```

## 版本號規範

遵循 [Semantic Versioning](https://semver.org/):

- **MAJOR.MINOR.PATCH** (例如 1.2.3)
  - **MAJOR**: 不兼容的 API 變更
  - **MINOR**: 向後兼容的功能新增
  - **PATCH**: 向後兼容的錯誤修復

範例：

- `0.1.0` → `0.1.1`: 錯誤修復
- `0.1.1` → `0.2.0`: 新增功能
- `0.2.0` → `1.0.0`: 重大變更或穩定版本

## 常見問題

### 上傳失敗：檔案已存在

PyPI 不允許覆蓋已上傳的版本。需要：

1. 更新版本號
2. 重新構建
3. 再次上傳

### Token 認證失敗

確認：

- Username 必須是 `__token__`（兩個底線）
- Password 是完整的 token（包含 `pypi-` 前綴）

### 依賴套件安裝失敗

確保 `pyproject.toml` 中的依賴版本正確且可用。
