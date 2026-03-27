1. 密钥注册表 不能代码内注册，通过yaml文件注册
2. Infisical交互通过 Infisical Agent 实现。
3. 插件通过# plugins/plugins.yaml注册
plugins:
  rating:
    enabled: true
    path: plugins/rating
  knowflow_openclaw:
    enabled: true
    # path 没有设置默认为plugins/name
4. 整个流程具有鲜明的流程化，init 阶段会执行 args参数解析，插件注册，环境变量注册，（密匙注册，此时检查Infisical服务是否启动。密匙检查，有三种值，Infisical值，默认值，随机值，空值。required必须有值。优先使用Infisical值，其次是随机值，再次是默认值，再次是空值）。setting完成后开始uvicorn.run。
5. main.py 支持argpse输入，参数解析在setting部分。


6. 所有路由都在api文件夹中。包括helath
7. register_plugins只能干注册插件的事情，干什么创建文件夹？
8. secrets_manager直接在import模块的时候已经创建了 其他代码例如main只需执行secrets_manager.initialize
9. 除了main,setting之外其他代码不能出现默认值，例如这个就有问题 SecretsManager self.secrets_yaml_path = Path(secrets_yaml_path) if secrets_yaml_path else backend_root.parent / "secrets" / "backend.yaml"
10. 插件注册是在插件注册一步的，不能在def _collect_secret_defs(self)中收集有哪些插件。有哪些插件应该setting中已经获取了。收集插件应该是插件管理服务的事情。
11. _collect_secret_defs直接从已有的插件列表中导出plugin config即可。插件管理load完之后可能是个dict,key=name,val=plugin.yaml的dict。
12. 除了main,setting之外其他代码不能出现默认值,例如 DEFAULT_SOCKET_PATH
13. 要清楚的意识到类/模块中_XXX变量是告诉其他模块不要调用的（我自己用的），它本身没有安全性。不要为了安全用这个。应该是根据其他模块用不用来判断。
14. _resolve_secret_value逻辑不对。无论如何infisical_value是第一优先级，若没有infisical_value，则判断是否required，若required，则随机，若是optional则是默认值或空值。required的默认值没有用到。
15. self._secrets_cache[name] 不是永久的，其会刷新的，记录其创建时间，当其创建时间超了就刷新，外部可以通过一个函数强制刷新。getsce 默认先反回self._secrets_cache

16.5. 流程第一步是注册各个manager 每个manager初始化__init__就是注册，init
16. 创建setting_manager, 其可以注册argpase, 保留其他模块注册argpase的方法。setup_settings在setting_manager中
17. load_plugin_registry在plugin_manager中。
18. register_secrets在secrets_manager中。
19. database变成database_manager，其初始化时注册数据库连接。
