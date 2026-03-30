## Context

当前我们在 `openclaw` 分支里强行用 PowerShell 脚本（GBK 编码）改写了原有的 UTF-8 Python 代码，导致 `plugins/collectors/openclaw/backend.py` 出现了乱码。此外，用户建议 `openclaw-extension` 最好作为一个 Submodule 直接放在 `plugins/` 目录中，引用外部仓库 `git@github.com:mcocdaa/plugin-openclaw-to-harvestflow.git`。我之前只把它加在了项目根目录下，并且还没移除。

## Goals / Non-Goals

**Goals:**
1. 使用 `git checkout origin/main -- plugins/collectors/openclaw/backend.py plugins/curators/openclaw/backend.py` 强行把刚才破坏的 Python 文件回退到纯净版，不让它被我乱搞的代码干扰。
2. 彻底删除 `openclaw-extension` 文件夹及其所有对主树的改动。
3. 通过 `git submodule add git@github.com:mcocdaa/plugin-openclaw-to-harvestflow.git plugins/plugin-openclaw-to-harvestflow` 来将那个外包的 OpenClaw Extension 绑定为主项目的一个 Submodule。

**Non-Goals:**
1. 我不再尝试用脚本去替换修改 Python 逻辑（除非另有授权），这部分代码让后端的开发者自己去完善。

## Decisions

- **回滚**: 不手动修改，直接从 Git 回退。
- **Submodule 绑定**: 利用 Git 的 Submodule 特性代替内嵌目录。

## Risks / Trade-offs

- **Submodule 权限风险**: 如果执行 submodule add 的时候 SSH 不通，会失败。不过我们在前一个回合里刚刚拉取过代码，GitHub 的通讯应该是没问题的。