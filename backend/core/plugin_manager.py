# @file backend/core/plugin_manager.py
# @brief 插件管理器 - 负责插件注册和加载
# @create 2026-03-26

import os
import re
import sys
import yaml
import logging
import threading
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
        self._registry_lock = threading.Lock()

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
        self.plugin_modules = {}
        root = str(setting_manager.ROOT_DIR)
        if root not in sys.path:
            sys.path.insert(0, root)
        plugins_parent = str(self.plugins_dir.parent)
        if plugins_parent not in sys.path:
            sys.path.insert(0, plugins_parent)

        for key, info in self.plugins.items():
            if not info.get("enabled", True):
                continue
            module_name = self._module_name(key)
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
                module_name = self._module_name(key)
                if module_name in sys.modules:
                    del sys.modules[module_name]
                self.plugin_modules.pop(key, None)

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

    def _module_name(self, key: str) -> str:
        """插件 key → 模块名：plugins.{key 中的路径分隔符替换为 .}"""
        return f"plugins.{key.replace(os.sep, '.').replace('/', '.')}"

    def _read_yaml(self, path: Path) -> Optional[Dict]:
        """读取 yaml 文件，异常记录错误返回 None

        Args:
            path: yaml 文件路径

        Returns:
            解析后的字典（空内容返回 {}），读取失败返回 None
        """
        try:
            with open(path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f) or {}
        except Exception as e:
            self.logger.error(f"读取 yaml 文件失败: {path}: {e}", exc_info=True)
            return None

    def _read_manifest(self, path: Path) -> Dict:
        """读取插件清单：目录取 plugin.yaml；.py 单文件构造默认清单

        Args:
            path: 插件路径（目录或 .py 文件）

        Returns:
            插件清单字典
        """
        if path.is_dir():
            return self._read_yaml(path / "plugin.yaml")
        return {"name": path.stem, "type": "unknown", "backend_entry": path.name}

    def _load_entry(self, key: str, cfg: Dict) -> Optional[Dict]:
        """处理注册表单个条目

        Args:
            key: 插件 key
            cfg: plugins.yaml 中该插件的配置

        Returns:
            {enabled, path, name, type, manifest}，失败返回 None
        """
        if cfg is None:
            return None
        if not cfg.get("enabled", True):
            # 保留禁用插件到注册表（供 enable API 查找），但不加载
            self.logger.debug(f"插件 {key} 已禁用，跳过")
            return {
                "enabled": False,
                "path": "",
                "name": key.split("/")[-1],
                "type": "unknown",
                "manifest": {},
            }

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
            return None

        if path.is_dir():
            plugin_yaml = path / "plugin.yaml"
            if not plugin_yaml.exists():
                self.logger.warning(f"插件清单文件不存在: {plugin_yaml}，跳过插件 {key}")
                return None
            manifest = self._read_yaml(plugin_yaml)
            if manifest is None:
                # 清单读取失败（IO/解析异常），跳过该插件
                return None
        elif path.suffix == ".py":
            manifest = self._read_manifest(path)
        else:
            self.logger.warning(f"插件路径既不是目录也不是 .py 文件: {path}，跳过插件 {key}")
            return None

        return {
            "enabled": True,
            "path": str(path),
            "name": manifest.get("name", key.split("/")[-1] if "/" in key else key),
            "type": manifest.get("type", "unknown"),
            "manifest": manifest,
        }

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

        data = self._read_yaml(registry_path)
        if data is None:
            return {}

        plugins = {}
        for key, cfg in data.get("plugins", {}).items():
            try:
                entry = self._load_entry(key, cfg)
            except Exception as e:
                self.logger.error(f"处理插件 {key} 时发生错误: {e}", exc_info=True)
                continue
            if entry is None:
                continue
            plugins[key] = entry
            self.logger.debug(f"成功加载插件注册表项: {key} ({entry['path']})")

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
                name = secret.get("name")
                if not name:
                    continue
                secrets.append({
                    "name": name,
                    "description": secret.get("description", ""),
                    "level": secret.get("level", "optional"),
                    "default": secret.get("default", None),
                    "source": info["name"],
                })
        return secrets

    def _set_enabled_in_yaml(self, key: str, enabled: bool) -> bool:
        """Update enabled field in plugins.yaml using line-level replacement (preserves comments)."""
        registry_path = self.plugins_dir / "plugins.yaml"
        if not registry_path.exists():
            return False

        with self._registry_lock:
            try:
                with open(registry_path, 'r', encoding='utf-8') as f:
                    content = f.read()
            except Exception as e:
                self.logger.error(f"读取插件注册表失败: {e}")
                return False

            # Match the plugin key block and replace its enabled line
            # `:.*` 允许 key 行同行注释（如 `curators/openclaw:   # 说明`）
            escaped_key = re.escape(key)
            pattern = rf'^(\s*{escaped_key}\s*:.*\n\s+enabled\s*:\s*)\w+'
            new_enabled = "true" if enabled else "false"

            if re.search(pattern, content, re.MULTILINE):
                new_content = re.sub(pattern, rf'\1{new_enabled}', content, flags=re.MULTILINE)
            else:
                self.logger.warning(f"未找到插件 {key} 的 enabled 字段，跳过")
                return False

            try:
                with open(registry_path, 'w', encoding='utf-8') as f:
                    f.write(new_content)
            except Exception as e:
                self.logger.error(f"写入插件注册表失败: {e}")
                return False

            return True

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

        if not self._set_enabled_in_yaml(plugin_key, enabled):
            return False

        if not enabled:
            module_name = self._module_name(plugin_key)
            hook_manager.unregister_by_module(module_name)
            to_remove = [m for m in sys.modules if m == module_name or m.startswith(module_name + ".")]
            for m in to_remove:
                del sys.modules[m]
            self.plugin_modules.pop(plugin_key, None)
            self.loaded_plugins.pop(plugin_key, None)

        self.plugins = self._load_registry()

        if enabled:
            self.register_hooks()

        self.logger.info(f"插件 {plugin_key} 已{'启用' if enabled else '禁用'}")
        return True

    def _display_name(self, key: str, manifest: Dict) -> str:
        """插件显示名：优先 manifest.name，缺省用 key 最后一段"""
        return manifest.get("name", key.split("/")[-1] if "/" in key else key)

    def _plugin_type(self, key: str, manifest: Dict) -> str:
        """插件类型：key 含 '/' 取首段，否则取 manifest.type"""
        if '/' in key:
            return key.split('/')[0]
        return manifest.get("type", "unknown")

    def get_all(self) -> List[Dict]:
        """获取所有已注册插件的信息（包括禁用插件），展开 manifest 字段"""
        result = []
        for key, info in self.plugins.items():
            manifest = info.get("manifest", {})
            result.append({
                "key": key,
                "plugin_type": self._plugin_type(key, manifest),
                "enabled": info.get("enabled", True),
                "name": self._display_name(key, manifest),
                "version": manifest.get("version", ""),
                "description": manifest.get("description", ""),
                "author": manifest.get("author", ""),
                "type": manifest.get("type", "unknown"),
            })
        return result



plugin_manager = PluginManager()
