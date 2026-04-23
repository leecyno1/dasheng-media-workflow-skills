#!/usr/bin/env python3
"""
端到端测试：路径配置系统
验证 DASHENG_ROOT 环境变量覆盖和路径解析功能
"""

import os
import sys
import tempfile
import unittest
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "scripts"))


class TestPathConfig(unittest.TestCase):
    """测试路径配置系统的环境变量覆盖功能"""

    def setUp(self):
        """保存原始环境变量"""
        self.original_env = os.environ.get('DASHENG_ROOT')

    def tearDown(self):
        """恢复原始环境变量"""
        env_vars = ['DASHENG_PROJECT_ROOT', 'DASHENG_DESKTOP_ROOT']
        for var in env_vars:
            if var in os.environ:
                del os.environ[var]

    def test_env_override_basic(self):
        """测试基本的环境变量覆盖"""
        with tempfile.TemporaryDirectory() as tmpdir:
            os.environ['DASHENG_PROJECT_ROOT'] = tmpdir

            # Import after setting env var
            import path_config
            from importlib import reload
            reload(path_config)

            # Verify project root is set correctly
            project_root = path_config.get_project_root()
            self.assertEqual(str(project_root), tmpdir)

    def test_resolve_path_with_override(self):
        """测试 get_project_root 函数使用环境变量覆盖"""
        with tempfile.TemporaryDirectory() as tmpdir:
            os.environ['DASHENG_PROJECT_ROOT'] = tmpdir

            import path_config
            from importlib import reload
            reload(path_config)

            # Test get_project_root
            project_root = path_config.get_project_root()
            self.assertEqual(str(project_root), tmpdir)

    def test_output_paths_configurable(self):
        """测试输出路径可配置"""
        with tempfile.TemporaryDirectory() as tmpdir:
            os.environ['DASHENG_DESKTOP_ROOT'] = tmpdir

            import path_config
            from importlib import reload
            reload(path_config)

            # Check desktop root path
            desktop_root = path_config.get_desktop_root()
            self.assertEqual(str(desktop_root), tmpdir)


if __name__ == '__main__':
    unittest.main()
