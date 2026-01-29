# ============================================================
# 测试失败诊断 Hook 示例
# ============================================================
# 用于在测试项目的 conftest.py 中实现失败自动截图和视频保存
# 适用于现有项目或 API 项目升级为 UI 测试
# ============================================================

import pytest
from pathlib import Path


@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """测试失败时自动截图和保存视频

    功能:
    1. 测试失败时自动截图到 reports/screenshots/
    2. 自动获取视频路径并输出（如果配置了 record_video）
    3. 自动附加到 Allure 报告（如果安装了 allure-pytest）

    使用:
    - 将此 hook 添加到项目的 conftest.py 中
    - 无需额外配置,框架会自动处理
    """
    outcome = yield
    report = outcome.get_result()

    # 只处理测试执行阶段（call）的失败
    if report.when == "call" and report.failed:
        # 检查测试是否使用了 page fixture
        if "page" in item.funcargs:
            page = item.funcargs["page"]

            # ========== 1. 失败截图 ==========
            screenshots_dir = Path("reports/screenshots")
            screenshots_dir.mkdir(parents=True, exist_ok=True)
            screenshot_path = screenshots_dir / f"{item.name}_failure.png"

            try:
                page.screenshot(path=str(screenshot_path))
                print(f"\n📸 失败截图: {screenshot_path}")

                # 附加到 Allure 报告
                try:
                    import allure
                    allure.attach.file(
                        str(screenshot_path),
                        name="失败截图",
                        attachment_type=allure.attachment_type.PNG
                    )
                except ImportError:
                    pass  # 未安装 allure-pytest，跳过

            except Exception as e:
                print(f"\n⚠️  截图失败: {e}")

            # ========== 2. 视频路径（如果录制了视频）==========
            try:
                video = page.video
                if video:
                    video_path = video.path()
                    print(f"\n🎬 测试视频: {video_path}")

                    # 附加到 Allure 报告
                    try:
                        import allure
                        allure.attach.file(
                            str(video_path),
                            name="测试视频",
                            attachment_type=allure.attachment_type.WEBM
                        )
                    except ImportError:
                        pass
            except Exception:
                pass  # 没有视频或获取失败，静默跳过


# ============================================================
# 配置示例（config/base.yaml）
# ============================================================
"""
web:
  browser_type: chromium
  headless: true
  timeout: 30000
  record_video: retain-on-failure  # 仅保留失败的视频
  video_dir: reports/videos

observability:
  debug_output: true  # 启用调试输出（需要 pytest -s）
"""


# ============================================================
# 使用说明
# ============================================================
"""
1. 将 pytest_runtest_makereport hook 添加到项目的 conftest.py

2. 配置视频录制（可选）:
   # config/base.yaml
   web:
     record_video: retain-on-failure

3. 运行测试:
   pytest tests/ -v -s  # -s 显示截图/视频路径

4. 查看失败诊断:
   - 截图: reports/screenshots/test_xxx_failure.png
   - 视频: reports/videos/test_xxx.webm (仅失败测试)
   - Allure: allure serve reports/allure-results
"""
