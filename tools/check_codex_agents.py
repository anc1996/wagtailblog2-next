"""对仓库级 Codex 角色声明做离线、只读的一致性检查。

本工具不启动代理、不调用 MCP、不检查底层模型身份，也不证明权限隔离。
它只验证 TOML 可解析、角色注册表与角色文件一致，并拒绝把旧仓库路径
带入新站治理配置。
"""

from __future__ import annotations

import argparse
import sys
import tomllib
from pathlib import Path


REQUIRED_ROLES = ("terra", "sol", "gemini")
FORBIDDEN_REFS = (
    "wagtailblog2-unified-external-content-search",
    "feature/unified-external-content-search",
)


def load_toml(path: Path) -> dict:
    """读取 UTF-8 TOML，错误由调用方转为安全的失败信息。"""
    with path.open("rb") as handle:
        value = tomllib.load(handle)
    if not isinstance(value, dict):
        raise ValueError(f"{path} 顶层必须是表")
    return value


def check_repo(repo: Path) -> list[str]:
    """返回阻断性错误列表；空列表表示静态检查通过。"""
    errors: list[str] = []
    codex = repo / ".codex"
    config_path = codex / "config.toml"
    if not config_path.is_file():
        return [f"缺少 {config_path.relative_to(repo)}"]

    try:
        config = load_toml(config_path)
    except (OSError, tomllib.TOMLDecodeError, ValueError) as exc:
        return [f"无法解析 {config_path.relative_to(repo)}: {type(exc).__name__}"]

    agents = config.get("agents")
    if not isinstance(agents, dict) or agents.get("enabled") is not True:
        errors.append("[agents] 必须存在且 enabled=true")
        agents = {}

    for role in REQUIRED_ROLES:
        registration = agents.get(role)
        if not isinstance(registration, dict):
            errors.append(f"缺少 [agents.{role}] 注册")
            continue
        config_file = registration.get("config_file")
        if not isinstance(config_file, str) or not config_file.strip():
            errors.append(f"{role} 缺少 config_file")
            continue
        role_path = (codex / config_file).resolve()
        if not role_path.is_file():
            errors.append(f"{role} 配置不存在: {config_file}")
            continue
        try:
            role_config = load_toml(role_path)
        except (OSError, tomllib.TOMLDecodeError, ValueError) as exc:
            errors.append(f"{role} 配置解析失败: {type(exc).__name__}")
            continue
        if role_config.get("name") != role:
            errors.append(f"{role} 的 name 与注册名不一致")
        if role_config.get("model") != registration.get("model"):
            errors.append(f"{role} 的 model 与注册表不一致")
        if role_config.get("model_reasoning_effort") != registration.get(
            "model_reasoning_effort"
        ):
            errors.append(f"{role} 的 model_reasoning_effort 与注册表不一致")
        for field in ("description", "developer_instructions"):
            if not isinstance(role_config.get(field), str) or not role_config[field].strip():
                errors.append(f"{role} 缺少非空 {field}")

    for path in (
        repo / "AGENTS.md",
        codex / "AGENTS_INTERACTION_PROTOCOL.md",
        codex / "README.md",
    ):
        if not path.is_file():
            errors.append(f"缺少治理文件: {path.relative_to(repo)}")

    for path in codex.rglob("*"):
        if path.is_file() and path.suffix.lower() in {".toml", ".md"}:
            try:
                content = path.read_text(encoding="utf-8")
            except UnicodeDecodeError:
                errors.append(f"治理文件不是 UTF-8: {path.relative_to(repo)}")
                continue
            for forbidden in FORBIDDEN_REFS:
                if forbidden in content:
                    errors.append(
                        f"治理文件包含旧仓库/旧分支引用 {forbidden}: {path.relative_to(repo)}"
                    )
    return errors


def main() -> int:
    """命令行入口。"""
    parser = argparse.ArgumentParser(description="检查新站 Codex 角色声明")
    parser.add_argument("--repo", default=".", type=Path)
    args = parser.parse_args()
    repo = args.repo.resolve()
    errors = check_repo(repo)
    if errors:
        print(f"[FAIL] 发现 {len(errors)} 个阻断项")
        for error in errors:
            print(f"  - {error}")
        return 1
    print("[PASS] Codex 角色配置静态一致性检查通过")
    print("[INFO] 这不是运行时模型、provider 或权限隔离证明")
    return 0


if __name__ == "__main__":
    sys.exit(main())
