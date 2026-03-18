# @file backend/core/plugin_loader.py
# @brief 插件加载器：扫描、加载、管理插件
# @create 2026-03-18

import yaml
import importlib.util
import asyncio
from pathlib import Path
from typing import Dict, List, Any, Optional
from fastapi import FastAPI
from config import PLUGINS_DIR, API_VERSION
from core.database import get_database


class PluginLoader:
    def __init__(self):
        self.loaded_plugins: Dict[str, Dict[str, Any]] = {}
        self._plugin_modules: Dict[str, Any] = {}
        self.app: Optional[FastAPI] = None
        self.plugins_dir: Optional[Path] = None

    def initialize(self, app: FastAPI, plugins_dir: str = None):
        self.app = app
        self.plugins_dir = Path(plugins_dir or PLUGINS_DIR)

    def load_config(self) -> Dict:
        config_path = self.plugins_dir / "plugins.yaml"
        if config_path.exists():
            with open(config_path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f) or {}
        return {"plugins": {}}

    async def load_all_plugins(self):
        config = self.load_config()
        plugin_types = ["collectors", "curators", "reviewers"]

        for plugin_type in plugin_types:
            type_dir = self.plugins_dir / plugin_type
            if not type_dir.exists():
                continue

            for plugin_folder in type_dir.iterdir():
                if not plugin_folder.is_dir():
                    continue
                if plugin_folder.name.startswith('.') or plugin_folder.name.startswith('_'):
                    continue

                plugin_name = plugin_folder.name
                plugin_config = config.get("plugins", {}).get(f"{plugin_type}/{plugin_name}", {})

                if plugin_config.get("enabled", True):
                    await self._load_plugin(plugin_folder, plugin_type)

    async def _load_plugin(self, plugin_dir: Path, plugin_type: str):
        plugin_yaml = plugin_dir / "plugin.yaml"

        if not plugin_yaml.exists():
            print(f"[PluginLoader] 警告: 插件 {plugin_dir.name} 缺少 plugin.yaml")
            return

        with open(plugin_yaml, 'r', encoding='utf-8') as f:
            plugin_config = yaml.safe_load(f)

        plugin_name = plugin_config.get("name", plugin_dir.name)
        print(f"[PluginLoader] 加载插件: {plugin_name} ({plugin_type})")

        backend_entry = plugin_config.get("backend_entry")
        if backend_entry:
            await self._load_backend(plugin_dir / backend_entry, plugin_name, plugin_type)

        self._save_plugin_to_db(plugin_name, plugin_type, plugin_config)
        self.loaded_plugins[f"{plugin_type}/{plugin_name}"] = {
            "config": plugin_config,
            "path": str(plugin_dir),
            "plugin_type": plugin_type,
        }

        print(f"[PluginLoader] 插件 {plugin_name} 加载完成")

    def _save_plugin_to_db(self, name: str, plugin_type: str, config: Dict):
        db = get_database()
        import json
        try:
            db.execute(
                "INSERT OR REPLACE INTO plugins (name, plugin_type, is_enabled, config) VALUES (?, ?, ?, ?)",
                (name, plugin_type, 1, json.dumps(config))
            )
        except Exception as e:
            print(f"[PluginLoader] 保存插件到数据库失败: {e}")

    async def _load_backend(self, backend_path: Path, plugin_name: str, plugin_type: str):
        if not backend_path.exists():
            print(f"[PluginLoader] 后端文件不存在: {backend_path}")
            return

        spec = importlib.util.spec_from_file_location(
            f"plugin_{plugin_name}",
            backend_path
        )
        module = importlib.util.module_from_spec(spec)
        self._plugin_modules[f"{plugin_type}/{plugin_name}"] = module
        spec.loader.exec_module(module)

        if hasattr(module, 'router'):
            self.app.include_router(
                module.router,
                prefix=f"/api/{API_VERSION}/plugins/{plugin_type}/{plugin_name}",
                tags=[f"plugin/{plugin_type}/{plugin_name}"]
            )
            print(f"[PluginLoader] 注册路由: /api/{API_VERSION}/plugins/{plugin_type}/{plugin_name}")

        if hasattr(module, 'on_load'):
            if asyncio.iscoroutinefunction(module.on_load):
                await module.on_load()
            else:
                module.on_load()

    def get_plugin_manifests(self) -> List[Dict]:
        manifests = []
        for plugin_key, plugin_data in self.loaded_plugins.items():
            config = plugin_data["config"]
            manifests.append({
                "name": config.get("name", plugin_key.split("/")[-1]),
                "plugin_type": plugin_data["plugin_type"],
                "version": config.get("version", "1.0.0"),
                "description": config.get("description", ""),
                "author": config.get("author", ""),
                "frontend_entry": config.get("frontend_entry"),
                "path": plugin_data["path"],
            })
        return manifests

    def get_plugin_config(self, plugin_name: str) -> Optional[Dict]:
        for plugin_key, plugin_data in self.loaded_plugins.items():
            if plugin_key.endswith(f"/{plugin_name}"):
                return plugin_data["config"]
        return None

    def get_plugin_frontend_code(self, plugin_name: str) -> Optional[str]:
        for plugin_key, plugin_data in self.loaded_plugins.items():
            if plugin_key.endswith(f"/{plugin_name}"):
                config = plugin_data["config"]
                frontend_entry = config.get("frontend_entry")
                if not frontend_entry:
                    return None

                frontend_path = Path(plugin_data["path"]) / frontend_entry
                if not frontend_path.exists():
                    return None

                with open(frontend_path, 'r', encoding='utf-8') as f:
                    return f.read()
        return None

    def get_enabled_plugins(self, plugin_type: str = None) -> List[Dict]:
        db = get_database()
        results = []
        if plugin_type:
            rows = db.fetchall("SELECT * FROM plugins WHERE plugin_type = ? AND is_enabled = 1", (plugin_type,))
        else:
            rows = db.fetchall("SELECT * FROM plugins WHERE is_enabled = 1")

        for row in rows:
            results.append(dict(row))
        return results

    async def enable_plugin(self, plugin_name: str) -> bool:
        db = get_database()
        db.execute("UPDATE plugins SET is_enabled = 1 WHERE name = ?", (plugin_name,))
        return True

    async def disable_plugin(self, plugin_name: str) -> bool:
        db = get_database()
        db.execute("UPDATE plugins SET is_enabled = 0 WHERE name = ?", (plugin_name,))
        return True


plugin_loader = PluginLoader()
