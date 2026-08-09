# @file backend/core/plugin_manager.py
# @brief 插件管理器 - 负责插件注册和加载
# @create 2026-03-26

import os
import sys
import yaml
import logging
import importlib
import importlib.util
from pathlib import Path
from typing import Dict, List, Any, Optional
import argparse

from core import hook_manager
from core import setting_manager


class PluginManager:
    """插件管理器

    职责：
    1. 扫描并注册插件
    2. 加载插件后端代码
    3. 管理插件生命周期
    """

    @hook_manager.wrap_hooks("plugin_manager_construct_before", "plugin_manager_construct_after")
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.plugins_dir: Optional[Path] = self._resolve_plugins_dir()
        self.plugins: Dict[str, Any] = self._load_registry()
        self.logger.info(f"[PluginManager] 发现 {len(self.plugins)} 个插件:")
        for key, info in self.plugins.items():
            self.logger.info(f"  - {key} ({info['type']})")
        self.loaded_plugins: Dict[str, Any] = {}
        self.plugin_modules: Dict[str, Any] = {}

    def _resolve_plugins_dir(self) -> Optional[Path]:
        """解析插件目录（相对路径基于项目根）"""
        plugins_dir_val = setting_manager.get("PLUGINS_DIR", "") or ""
        if not plugins_dir_val:
            return None
        path = Path(plugins_dir_val)
        if not path.is_absolute():
            path = Path(setting_manager.ROOT_DIR) / path
        return path.resolve()

    @hook_manager.wrap_hooks(after="plugin_manager_register_arguments")
    def register_arguments(self, parser: argparse.ArgumentParser):
        """注册 argparse 参数

        Args:
            parser: argparse.ArgumentParser 实例
        """
        pass

    @hook_manager.wrap_hooks("plugin_manager_init_before", "plugin_manager_init_after")
    def init(self, args: argparse.Namespace):
        """初始化插件管理器

        Args:
            args: 解析后的参数
        """

    def register_hooks(self):
        """注册插件钩子 - 优先按包名导入，失败时回退按文件路径加载"""
        if not self.plugins_dir:
            self.logger.warning("插件目录未设置，跳过插件注册")
            return

        self.loaded_plugins = {}
        root = str(setting_manager.ROOT_DIR)
        if root not in sys.path:
            sys.path.insert(0, root)
        plugins_parent = str(self.plugins_dir.parent)
        if plugins_parent not in sys.path:
            sys.path.insert(0, plugins_parent)

        for key, info in self.plugins.items():
            if not info.get("enabled", True):
                continue
            module_name = f"plugins.{key.replace(os.sep, '.').replace('/', '.')}"
            try:
                try:
                    module = importlib.import_module(module_name)
                except ModuleNotFoundError:
                    module = self._load_from_file(info, module_name)
                self.loaded_plugins[key] = self.plugins[key]
                self.plugin_modules[key] = module
                self.logger.info(f"成功加载插件: {info['name']} ({key})")
            except Exception as e:
                self.logger.error(f"导入插件 {key} 失败: {e}", exc_info=True)
                module_name = f"plugins.{key.replace(os.sep, '.').replace('/', '.')}"
                if module_name in sys.modules:
                    del sys.modules[module_name]
                if key in self.loaded_plugins:
                    del self.loaded_plugins[key]

    def _load_from_file(self, info: Dict, module_name: str):
        """按文件路径加载插件模块（适用于非项目内插件目录）"""
        plugin_path = Path(info["path"])
        module_file = None
        if plugin_path.is_file() and plugin_path.suffix == ".py":
            module_file = plugin_path
        elif plugin_path.is_dir():
            init_file = plugin_path / "__init__.py"
            if init_file.exists():
                module_file = init_file

        if module_file is None:
            raise ImportError(f"插件入口不存在: {plugin_path}")

        spec = importlib.util.spec_from_file_location(module_name, module_file)
        if spec is None or spec.loader is None:
            raise ImportError(f"无法为插件创建模块规范: {module_file}")

        module = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = module
        spec.loader.exec_module(module)
        return module

    def _load_registry(self) -> Dict[str, Any]:
        """加载插件注册表

        Returns:
            {plugin_key: {enabled, path, name, type, manifest}}
        """
        if not self.plugins_dir or not self.plugins_dir.exists():
            self.logger.warning("插件目录不存在或未设置，跳过加载插件注册表")
            return {}

        registry_path = self.plugins_dir / "plugins.yaml"

        if not registry_path.exists():
            self.logger.debug(f"插件注册表文件不存在: {registry_path}")
            return {}

        try:
            with open(registry_path, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f) or {}
        except Exception as e:
            self.logger.error(f"读取插件注册表失败: {e}", exc_info=True)
            return {}

        plugins = {}
        for key, cfg in data.get("plugins", {}).items():
            if cfg is None:
                continue
            if not cfg.get("enabled", True):
                # 保留禁用插件到注册表（供 enable API 查找），但不加载
                plugins[key] = {
                    "enabled": False,
                    "path": "",
                    "name": key.split("/")[-1],
                    "type": "unknown",
                    "manifest": {},
                }
                self.logger.debug(f"插件 {key} 已禁用，跳过")
                continue

            try:
                if "path" in cfg:
                    path = Path(cfg["path"])
                    if not path.is_absolute():
                        path = (self.plugins_dir / path).resolve()
                    else:
                        path = path.resolve()
                else:
                    path = (self.plugins_dir / key).resolve()

                if not path.exists():
                    self.logger.warning(f"插件路径不存在: {path}，跳过插件 {key}")
                    continue

                if path.is_dir():
                    plugin_yaml = path / "plugin.yaml"
                    if not plugin_yaml.exists():
                        self.logger.warning(f"插件清单文件不存在: {plugin_yaml}，跳过插件 {key}")
                        continue

                    try:
                        with open(plugin_yaml, 'r', encoding='utf-8') as f:
                            manifest = yaml.safe_load(f) or {}
                    except Exception as e:
                        self.logger.error(f"读取插件清单失败 ({key}): {e}", exc_info=True)
                        continue
                elif path.suffix == ".py":
                    manifest = {
                        "name": path.stem,
                        "type": "unknown",
                        "backend_entry": path.name
                    }
                else:
                    self.logger.warning(f"插件路径既不是目录也不是 .py 文件: {path}，跳过插件 {key}")
                    continue

                plugin_type = manifest.get("type", "unknown")

                plugins[key] = {
                    "enabled": True,
                    "path": str(path),
                    "name": manifest.get("name", key.split("/")[-1] if "/" in key else key),
                    "type": plugin_type,
                    "manifest": manifest,
                }
                self.logger.debug(f"成功加载插件注册表项: {key} ({path})")

            except Exception as e:
                self.logger.error(f"处理插件 {key} 时发生错误: {e}", exc_info=True)
                continue

        return plugins

    def get_plugin_secrets(self) -> List[Dict[str, Any]]:
        """从已注册插件中提取密钥定义

        Returns:
            密钥定义列表
        """
        secrets = []
        for key, info in self.plugins.items():
            manifest = info.get("manifest", {})
            for secret in manifest.get("secrets", []):
                secrets.append({
                    "name": secret["name"],
                    "description": secret.get("description", ""),
                    "level": secret.get("level", "optional"),
                    "default": secret.get("default", None),
                    "source": info["name"],
                })
        return secrets

    def set_enabled(self, plugin_key: str, enabled: bool) -> bool:
        """启用/禁用插件，持久化到 plugins.yaml 并重载注册表

        Returns:
            是否设置成功
        """
        if plugin_key not in self.plugins:
            return False
        if not self.plugins_dir:
            return False

        registry_path = self.plugins_dir / "plugins.yaml"
        if not registry_path.exists():
            return False

        try:
            with open(registry_path, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f) or {}
            plugin_cfg = data.setdefault("plugins", {}).setdefault(plugin_key, {})
            plugin_cfg["enabled"] = enabled
            # 注意：safe_dump 会重写文件，不保留注释（已知限制）
            with open(registry_path, 'w', encoding='utf-8') as f:
                yaml.safe_dump(data, f, allow_unicode=True, sort_keys=False)
        except Exception as e:
            self.logger.error(f"更新插件状态失败 ({plugin_key}): {e}", exc_info=True)
            return False

        self.plugins = self._load_registry()
        self.register_hooks()
        self.logger.info(f"插件 {plugin_key} 已{'启用' if enabled else '禁用'}")
        return True

    def get_all(self) -> List[Dict]:
        """获取所有已加载插件的信息"""
        result = []
        for key, info in self.loaded_plugins.items():
            plugin_info = info.copy()
            plugin_info["key"] = key
            # 从 key 中提取 plugin_type (例如：collectors/openclaw -> collectors)
            if '/' in key:
                plugin_info['plugin_type'] = key.split('/')[0]
            else:
                plugin_info['plugin_type'] = 'unknown'
            result.append(plugin_info)
        return result



plugin_manager = PluginManager()
