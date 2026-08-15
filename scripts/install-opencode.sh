#!/bin/bash
# ============================================
# HarvestFlow vendored skills 安装脚本
# 将仓库 skills/ 下的 superpowers-* skills 安装到 OpenCode 的
# filesystem skill 目录（~/.config/opencode/skills/）
#
# 用法:
#   ./scripts/install-opencode.sh
#   OPENCODE_SKILLS_DIR=/自定义/目录 ./scripts/install-opencode.sh
# ============================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
SKILLS_SRC="$PROJECT_ROOT/skills"
DEST="${OPENCODE_SKILLS_DIR:-$HOME/.config/opencode/skills}"

if [ ! -d "$SKILLS_SRC" ]; then
  echo "错误: 未找到 skills 目录: $SKILLS_SRC" >&2
  exit 1
fi

mkdir -p "$DEST"

installed=0
for skill_dir in "$SKILLS_SRC"/superpowers-*/; do
  [ -d "$skill_dir" ] || continue
  name="$(basename "$skill_dir")"
  # 防止源目录与目标目录相同（如用户已将 skills/ 软链到安装目录）
  if [ "$SKILLS_SRC/$name" -ef "$DEST/$name" ]; then
    echo "跳过（已就位）: $name"
    continue
  fi
  rm -rf "$DEST/$name"
  cp -R "$skill_dir" "$DEST/$name"
  echo "已安装: $name"
  installed=$((installed + 1))
done

if [ "$installed" -eq 0 ]; then
  echo "警告: 未安装任何 skill（$SKILLS_SRC 下无 superpowers-* 目录）" >&2
  exit 1
fi

echo "完成: $installed 个 skill 已安装到 $DEST"
