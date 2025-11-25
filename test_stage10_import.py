"""
Stage 10 Import Test

測試 Stage 10 新增模組的 import 功能
"""

print("=" * 60)
print("Stage 10 Import Test")
print("=" * 60)

# Test 1: VectorClusteringTool
print("\n[Test 1] VectorClusteringTool import...")
try:
    from src.tools.vector_clustering import VectorClusteringTool, cluster_articles
    print("✓ VectorClusteringTool import successful")

    # 測試基本初始化
    tool = VectorClusteringTool(n_clusters=3)
    print(f"✓ VectorClusteringTool initialization: method={tool.method}, n_clusters={tool.n_clusters}")
except Exception as e:
    print(f"✗ VectorClusteringTool import failed: {e}")

# Test 2: TrendAnalysisTool
print("\n[Test 2] TrendAnalysisTool import...")
try:
    from src.tools.trend_analysis import TrendAnalysisTool, analyze_weekly_trends
    print("✓ TrendAnalysisTool import successful")

    # 測試基本初始化
    tool = TrendAnalysisTool()
    print("✓ TrendAnalysisTool initialization successful")
except Exception as e:
    print(f"✗ TrendAnalysisTool import failed: {e}")

# Test 3: CuratorWeeklyRunner
print("\n[Test 3] CuratorWeeklyRunner import...")
try:
    from src.agents.curator_weekly import (
        CuratorWeeklyRunner,
        create_weekly_curator_agent,
        generate_weekly_report
    )
    print("✓ CuratorWeeklyRunner import successful")
    print("✓ create_weekly_curator_agent import successful")
    print("✓ generate_weekly_report import successful")
except Exception as e:
    print(f"✗ CuratorWeeklyRunner import failed: {e}")

# Test 4: Tools module export
print("\n[Test 4] Tools module export...")
try:
    from src.tools import VectorClusteringTool, TrendAnalysisTool
    print("✓ VectorClusteringTool exported from src.tools")
    print("✓ TrendAnalysisTool exported from src.tools")
except Exception as e:
    print(f"✗ Tools module export failed: {e}")

# Test 5: Agents module export
print("\n[Test 5] Agents module export...")
try:
    from src.agents import (
        CuratorWeeklyRunner,
        create_weekly_curator_agent,
        generate_weekly_report
    )
    print("✓ CuratorWeeklyRunner exported from src.agents")
    print("✓ create_weekly_curator_agent exported from src.agents")
    print("✓ generate_weekly_report exported from src.agents")
except Exception as e:
    print(f"✗ Agents module export failed: {e}")

# Test 6: scikit-learn availability
print("\n[Test 6] scikit-learn availability...")
try:
    import sklearn
    print(f"✓ scikit-learn version: {sklearn.__version__}")

    from sklearn.cluster import KMeans
    print("✓ sklearn.cluster.KMeans import successful")

    from sklearn.feature_extraction.text import TfidfVectorizer
    print("✓ sklearn.feature_extraction.text.TfidfVectorizer import successful")
except Exception as e:
    print(f"✗ scikit-learn import failed: {e}")

print("\n" + "=" * 60)
print("Import Test Complete")
print("=" * 60)
