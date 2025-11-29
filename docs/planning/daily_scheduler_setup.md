# InsightCosmos 每日自動排程設置指南

## 概述

本文件說明如何設置 InsightCosmos 每日報表的自動排程執行。使用 macOS launchd 服務在每天早上 6:00 自動執行 Pipeline，並將執行結果記錄在 `docs/optimization` 資料夾。

## 檔案結構

```
InsightCosmos/
├── scripts/
│   ├── daily_pipeline.sh          # 執行腳本
│   └── com.insightcosmos.daily.plist  # launchd 配置
├── logs/
│   ├── launchd_stdout.log         # launchd 標準輸出
│   └── launchd_stderr.log         # launchd 錯誤輸出
└── docs/optimization/
    ├── daily_run_YYYYMMDD_HHMMSS.log  # 詳細執行日誌
    └── production_run_YYYYMMDD_HHMMSS.md  # Markdown 報告
```

## 設置步驟

### 1. 安裝 launchd 服務

複製 plist 檔案到 LaunchAgents 目錄：

```bash
cp /Users/ray/sides/InsightCosmos/scripts/com.insightcosmos.daily.plist \
   ~/Library/LaunchAgents/
```

### 2. 載入服務

```bash
launchctl load ~/Library/LaunchAgents/com.insightcosmos.daily.plist
```

### 3. 驗證服務狀態

```bash
launchctl list | grep insightcosmos
```

如果服務已載入，會顯示類似：
```
-	0	com.insightcosmos.daily
```

## 管理命令

### 啟動服務（立即執行一次）

```bash
launchctl start com.insightcosmos.daily
```

### 停止服務

```bash
launchctl stop com.insightcosmos.daily
```

### 卸載服務

```bash
launchctl unload ~/Library/LaunchAgents/com.insightcosmos.daily.plist
```

### 重新載入（修改配置後）

```bash
launchctl unload ~/Library/LaunchAgents/com.insightcosmos.daily.plist
launchctl load ~/Library/LaunchAgents/com.insightcosmos.daily.plist
```

## 執行時間配置

預設執行時間為每天 **06:00**。如需修改，編輯 plist 檔案中的 `StartCalendarInterval`：

```xml
<key>StartCalendarInterval</key>
<dict>
    <key>Hour</key>
    <integer>6</integer>    <!-- 改為你想要的小時 (0-23) -->
    <key>Minute</key>
    <integer>0</integer>    <!-- 改為你想要的分鐘 (0-59) -->
</dict>
```

修改後需重新載入服務。

## 執行結果查看

### 查看最新執行報告

```bash
ls -lt /Users/ray/sides/InsightCosmos/docs/optimization/production_run_*.md | head -1
```

### 查看執行日誌

```bash
ls -lt /Users/ray/sides/InsightCosmos/docs/optimization/daily_run_*.log | head -1
```

### 查看 launchd 日誌

```bash
# 標準輸出
tail -100 /Users/ray/sides/InsightCosmos/logs/launchd_stdout.log

# 錯誤輸出
tail -100 /Users/ray/sides/InsightCosmos/logs/launchd_stderr.log
```

## 手動執行測試

在設置 launchd 前，建議先手動測試腳本：

```bash
/Users/ray/sides/InsightCosmos/scripts/daily_pipeline.sh
```

## 故障排除

### 服務未執行

1. 確認電腦在排程時間處於開機狀態
2. 檢查 launchd 日誌是否有錯誤
3. 確認腳本有執行權限：
   ```bash
   ls -l /Users/ray/sides/InsightCosmos/scripts/daily_pipeline.sh
   ```

### 環境變數問題

如果 Python 或相關工具找不到，編輯 plist 的 `EnvironmentVariables`：

```xml
<key>EnvironmentVariables</key>
<dict>
    <key>PATH</key>
    <string>/usr/local/bin:/usr/bin:/bin:/opt/homebrew/bin</string>
    <key>GOOGLE_API_KEY</key>
    <string>your_api_key_here</string>  <!-- 如果需要 -->
</dict>
```

### 查看系統日誌

```bash
log show --predicate 'subsystem == "com.apple.xpc.launchd"' --last 1h | grep insightcosmos
```

## 注意事項

1. **電腦需開機**: launchd 只在電腦開機時執行。如果錯過排程時間，不會補執行。

2. **網路連接**: Pipeline 需要網路連接來獲取 RSS 和執行 Google Search。

3. **API 配額**: 確保 Google API 配額足夠每日執行。

4. **磁碟空間**: 日誌會持續累積，建議定期清理舊日誌：
   ```bash
   # 刪除 30 天前的日誌
   find /Users/ray/sides/InsightCosmos/docs/optimization -name "daily_run_*.log" -mtime +30 -delete
   ```

5. **環境變數**: 腳本會從 `.env` 檔案讀取配置，確保該檔案存在且包含必要的 API keys。

---
*建立時間: 2025-11-26*
*維護者: Ray 張瑞涵*
