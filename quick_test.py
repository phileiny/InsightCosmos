"""Quick test to verify basic functionality"""

print("Starting quick test...")

try:
    from src.utils.logger import Logger
    print("✓ Logger imported successfully")

    logger = Logger.get_logger("quicktest")
    print("✓ Logger created successfully")

    logger.info("Test message")
    print("✓ Logger can write messages")

except Exception as e:
    print(f"✗ Error: {e}")
    import traceback
    traceback.print_exc()

print("Quick test complete")
