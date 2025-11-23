#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""最簡單的測試"""

print("開始測試...")

# 測試 1: 導入模組
try:
    from src.utils.logger import Logger
    print("[1/4] ✓ Logger 模組導入成功")
except Exception as e:
    print(f"[1/4] ✗ Logger 導入失敗: {e}")
    exit(1)

try:
    from src.utils.config import Config
    print("[2/4] ✓ Config 模組導入成功")
except Exception as e:
    print(f"[2/4] ✗ Config 導入失敗: {e}")
    exit(1)

# 測試 2: 創建 Logger
try:
    logger = Logger.get_logger("simple_test")
    logger.info("測試訊息")
    print("[3/4] ✓ Logger 創建並寫入成功")
except Exception as e:
    print(f"[3/4] ✗ Logger 測試失敗: {e}")
    exit(1)

# 測試 3: 測試 Config（需要 .env 檔案）
try:
    # 創建臨時測試檔案
    with open(".env.simple_test", "w", encoding="utf-8") as f:
        f.write("GOOGLE_API_KEY=test123\n")
        f.write("SEARCH_API_KEY=test456\n")
        f.write("SEARCH_ENGINE_ID=testid\n")
        f.write("EMAIL_ACCOUNT=test@test.com\n")
        f.write("EMAIL_PASSWORD=testpass\n")

    config = Config.load(".env.simple_test")

    # 清理
    import os
    os.remove(".env.simple_test")

    print("[4/4] ✓ Config 載入成功")
    print(f"      使用者: {config.user_name}")

except Exception as e:
    print(f"[4/4] ✗ Config 測試失敗: {e}")
    import os
    if os.path.exists(".env.simple_test"):
        os.remove(".env.simple_test")
    exit(1)

print("\n" + "="*50)
print("✅ 所有基本測試通過！")
print("="*50)
