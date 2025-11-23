"""
簡化版 Stage 1 測試腳本
直接測試基本功能，不依賴 pytest
"""

import sys
from pathlib import Path

# 添加專案根目錄到 path
sys.path.insert(0, str(Path(__file__).parent))

print("\n" + "="*60)
print("InsightCosmos Stage 1 測試")
print("="*60 + "\n")

# 測試 1: 測試 Logger
print("【測試 1】Logger System")
print("-" * 60)
try:
    from src.utils.logger import Logger

    # 創建 logger
    logger = Logger.get_logger("test_stage1", log_level="DEBUG")
    print("✓ Logger 創建成功")

    # 寫入不同級別的日誌
    logger.debug("這是 DEBUG 訊息")
    logger.info("這是 INFO 訊息")
    logger.warning("這是 WARNING 訊息")
    logger.error("這是 ERROR 訊息")
    print("✓ 日誌訊息寫入成功")

    # 檢查日誌檔案
    from datetime import datetime
    today = datetime.now().strftime("%Y%m%d")
    log_file = Path("logs") / f"test_stage1_{today}.log"

    if log_file.exists():
        print(f"✓ 日誌檔案已創建: {log_file}")
        content = log_file.read_text(encoding='utf-8')
        if "INFO 訊息" in content:
            print("✓ 日誌檔案內容正確")
        else:
            print("✗ 日誌檔案內容異常")
    else:
        print(f"✗ 日誌檔案未找到: {log_file}")

    print("\n✅ Logger 測試通過\n")

except Exception as e:
    print(f"\n❌ Logger 測試失敗: {e}\n")
    import traceback
    traceback.print_exc()
    sys.exit(1)


# 測試 2: 測試 Config（使用測試檔案）
print("【測試 2】Config Manager")
print("-" * 60)
try:
    from src.utils.config import Config

    # 創建測試 .env 檔案
    test_env = Path(".env.test_stage1")
    test_env.write_text("""
GOOGLE_API_KEY=test_google_key_12345
SEARCH_API_KEY=test_search_key
SEARCH_ENGINE_ID=test_engine_id
EMAIL_ACCOUNT=test@example.com
EMAIL_PASSWORD=test_password
USER_NAME=TestUser
USER_INTERESTS=AI,Robotics,Multi-Agent Systems
LOG_LEVEL=INFO
""".strip())
    print("✓ 測試 .env 檔案已創建")

    # 載入配置
    config = Config.load(str(test_env))
    print("✓ Config 載入成功")

    # 驗證配置值
    assert config.google_api_key == "test_google_key_12345", "API key 不匹配"
    assert config.user_name == "TestUser", "使用者名稱不匹配"
    assert config.log_level == "INFO", "日誌級別不匹配"
    print("✓ 配置值正確")

    # 測試 get_interests_list
    interests = config.get_interests_list()
    assert len(interests) == 3, "興趣列表數量不正確"
    assert "AI" in interests, "興趣列表缺少 AI"
    print(f"✓ 興趣列表解析正確: {interests}")

    # 測試 __repr__ 隱藏敏感資訊
    repr_str = repr(config)
    assert "test_google_key" not in repr_str, "__repr__ 沒有隱藏敏感資訊"
    assert "sensitive fields hidden" in repr_str, "__repr__ 缺少隱藏標記"
    print("✓ __repr__ 正確隱藏敏感資訊")

    # 清理測試檔案
    test_env.unlink()
    print("✓ 測試檔案已清理")

    print("\n✅ Config 測試通過\n")

except Exception as e:
    print(f"\n❌ Config 測試失敗: {e}\n")
    import traceback
    traceback.print_exc()
    if Path(".env.test_stage1").exists():
        Path(".env.test_stage1").unlink()
    sys.exit(1)


# 測試 3: 測試 Config 錯誤處理
print("【測試 3】Config 錯誤處理")
print("-" * 60)
try:
    from src.utils.config import Config

    # 測試缺失必需欄位
    test_env = Path(".env.test_invalid")
    test_env.write_text("""
SEARCH_API_KEY=test_key
""".strip())

    try:
        config = Config.load(str(test_env))
        print("✗ 應該拋出 ValueError")
        test_env.unlink()
        sys.exit(1)
    except ValueError as e:
        if "GOOGLE_API_KEY" in str(e):
            print(f"✓ 正確捕獲缺失欄位錯誤: {e}")
        else:
            print(f"✗ 錯誤訊息不正確: {e}")
            test_env.unlink()
            sys.exit(1)

    test_env.unlink()

    # 測試檔案不存在
    try:
        config = Config.load("/nonexistent/.env")
        print("✗ 應該拋出 FileNotFoundError")
        sys.exit(1)
    except FileNotFoundError as e:
        print(f"✓ 正確捕獲檔案不存在錯誤")

    print("\n✅ Config 錯誤處理測試通過\n")

except Exception as e:
    print(f"\n❌ Config 錯誤處理測試失敗: {e}\n")
    import traceback
    traceback.print_exc()
    if Path(".env.test_invalid").exists():
        Path(".env.test_invalid").unlink()
    sys.exit(1)


# 測試 4: 整合測試
print("【測試 4】Config + Logger 整合")
print("-" * 60)
try:
    from src.utils.config import Config
    from src.utils.logger import Logger

    # 創建測試配置
    test_env = Path(".env.test_integration")
    test_env.write_text("""
GOOGLE_API_KEY=test_key
SEARCH_API_KEY=test_key
SEARCH_ENGINE_ID=test_id
EMAIL_ACCOUNT=test@example.com
EMAIL_PASSWORD=test_password
USER_NAME=IntegrationTest
LOG_LEVEL=DEBUG
""".strip())

    # 載入配置
    config = Config.load(str(test_env))
    print("✓ 配置載入成功")

    # 使用配置創建 logger
    logger = Logger.get_logger("integration_test", log_level=config.log_level)
    print("✓ 使用配置創建 Logger")

    # 寫入日誌
    logger.info(f"使用者: {config.user_name}")
    logger.info(f"興趣: {config.user_interests}")
    print("✓ 日誌寫入成功")

    # 清理
    test_env.unlink()

    print("\n✅ 整合測試通過\n")

except Exception as e:
    print(f"\n❌ 整合測試失敗: {e}\n")
    import traceback
    traceback.print_exc()
    if Path(".env.test_integration").exists():
        Path(".env.test_integration").unlink()
    sys.exit(1)


# 總結
print("="*60)
print("測試總結")
print("="*60)
print("✅ Logger System - 通過")
print("✅ Config Manager - 通過")
print("✅ 錯誤處理 - 通過")
print("✅ 整合測試 - 通過")
print("="*60)
print("\n🎉 所有測試通過！Stage 1 實作成功！\n")
