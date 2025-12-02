#!/bin/bash
# InsightCosmos Daily Pipeline Runner
# 自動執行每日報表並記錄結果到 docs/optimization

set -e

# 配置
PROJECT_DIR="/Users/ray/sides/InsightCosmos"
VENV_DIR="${PROJECT_DIR}/venv"
LOG_DIR="${PROJECT_DIR}/docs/optimization"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
DATE_DISPLAY=$(date +"%Y-%m-%d %H:%M")
LOG_FILE="${LOG_DIR}/daily_run_${TIMESTAMP}.log"
TIMEOUT_SECONDS=1800  # 30 分鐘超時，避免進程卡住影響下次排程

# 切換到專案目錄
cd "${PROJECT_DIR}"

# 啟動虛擬環境
source "${VENV_DIR}/bin/activate"

# 執行前記錄
echo "=============================================" | tee -a "${LOG_FILE}"
echo "InsightCosmos Daily Pipeline" | tee -a "${LOG_FILE}"
echo "執行時間: ${DATE_DISPLAY}" | tee -a "${LOG_FILE}"
echo "=============================================" | tee -a "${LOG_FILE}"

# 記錄開始時間
START_TIME=$(date +%s)

# 執行 Pipeline 並捕獲輸出（使用 Python 內建 timeout）
python -c "
import subprocess
import sys
try:
    result = subprocess.run(
        [sys.executable, '-m', 'src.orchestrator.daily_runner'],
        timeout=${TIMEOUT_SECONDS},
        check=False
    )
    sys.exit(result.returncode)
except subprocess.TimeoutExpired:
    print('ERROR: Pipeline 執行超時 (${TIMEOUT_SECONDS} 秒)')
    sys.exit(124)
" 2>&1 | tee -a "${LOG_FILE}"
PIPELINE_EXIT_CODE=${PIPESTATUS[0]}

# 檢查是否超時 (exit code 124 = timeout)
if [ ${PIPELINE_EXIT_CODE} -eq 124 ]; then
    echo "Pipeline 已被強制終止" | tee -a "${LOG_FILE}"
fi

# 計算執行時間
END_TIME=$(date +%s)
DURATION=$((END_TIME - START_TIME))
DURATION_MIN=$((DURATION / 60))
DURATION_SEC=$((DURATION % 60))

# 生成執行報告
REPORT_FILE="${LOG_DIR}/production_run_${TIMESTAMP}.md"

# 從 log 中提取關鍵數據
SCOUT_ARTICLES=$(grep -o "Collected [0-9]* articles" "${LOG_FILE}" | grep -o "[0-9]*" | head -1 || echo "N/A")
STORED_ARTICLES=$(grep -o "Stored [0-9]* new articles" "${LOG_FILE}" | grep -o "[0-9]*" | head -1 || echo "N/A")
ANALYZED_ARTICLES=$(grep -o "Analyzed [0-9]* articles" "${LOG_FILE}" | grep -o "[0-9]*" | head -1 || echo "N/A")
EMAIL_SENT=$(grep -q "Email sent successfully\|Email Sent: True" "${LOG_FILE}" && echo "成功" || echo "失敗")
PIPELINE_STATUS=$([ ${PIPELINE_EXIT_CODE} -eq 0 ] && echo "SUCCESS" || echo "FAILED")

# 生成 Markdown 報告
cat > "${REPORT_FILE}" << EOF
# Production Daily Run - ${DATE_DISPLAY} (UTC+8)

## 執行摘要

- **執行狀態**: ${PIPELINE_STATUS}
- **執行時間**: ${DURATION_MIN} 分 ${DURATION_SEC} 秒
- **Exit Code**: ${PIPELINE_EXIT_CODE}

## 執行結果

| 指標 | 數值 |
|------|------|
| Scout 收集文章 | ${SCOUT_ARTICLES} 篇 |
| 新存儲文章 | ${STORED_ARTICLES} 篇 |
| 分析完成文章 | ${ANALYZED_ARTICLES} 篇 |
| Email 發送 | ${EMAIL_SENT} |

## 詳細日誌

完整日誌請參考: \`daily_run_${TIMESTAMP}.log\`

---
*自動生成於: ${DATE_DISPLAY}*
*執行模式: PRODUCTION (自動排程)*
*執行結果: ${PIPELINE_STATUS}*
EOF

echo "" | tee -a "${LOG_FILE}"
echo "=============================================" | tee -a "${LOG_FILE}"
echo "執行完成" | tee -a "${LOG_FILE}"
echo "耗時: ${DURATION_MIN} 分 ${DURATION_SEC} 秒" | tee -a "${LOG_FILE}"
echo "報告已生成: ${REPORT_FILE}" | tee -a "${LOG_FILE}"
echo "=============================================" | tee -a "${LOG_FILE}"

exit ${PIPELINE_EXIT_CODE}
