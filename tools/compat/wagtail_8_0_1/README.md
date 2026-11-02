# P0-BLOCKER-01 最小只读审查附件

**仅用于隔离实验审查，尚未正式采用；不得安装到正式 Conda/生产环境。**
正式依赖仍以仓库 `pyproject.toml` 为准。本附件不改变依赖或正式环境，
不包含 wheel、上游完整源码或大日志，也不执行迁移或连接任何外部服务。

来源为 `artifacts/P0-BLOCKER-01-20261102` 中已测 v2 补丁和 scaffold：

- 上游 `wagtail/wagtail` commit `19ea8b53a660ef65d0e275a03c05dea6118c2f82`：
  Redirects、Documents、Locales、Snippets 的 API v3 启动保护。
- 上游 commit `123e88ddd5f73378f73ed5c4ce6dc234425db0d0`：
  仅移植 Images 启动保护，不移植该提交的其他功能。
- 官方 sdist `wagtail-8.0.1.tar.gz` SHA256：
  `819865a10bce86b16288cfaefa4195b90ffb5e7ac494fb18659e7be099ef386f`。
- 已测 wheel `wagtail-8.0.1+wb2next.apiv3guard.2-py3-none-any.whl` SHA256：
  `0a593d987088d3f8ab4a4ca8fae097b61fa931701c6f556542dbcf1f9ca1a5b5`。
- 补丁 SHA256：
  `1d91c2dd724b4f9a20f3abbd52f245ccb88040d9ce2fced1d5d7f371b2d3cf75`；
  与实验成功补丁逐字节相同，含五处 AppConfig 保护和实验版本标记。

`provenance.json` 提供上述机器可读来源。wheel 哈希仅标识既有已测产物，
不承诺重建时 ZIP 时间戳或哈希完全相同。

`test_startup_compatibility.py` 保留原 20 项合同测试，
使用 `Path(__file__).resolve().parents[3]` 定位当前仓库。
辅助 `blocker01_locales_settings.py` 只在子进程启用 Locales，不修改项目设置。
文件守卫在原临时 ROOT 写白名单基础上收紧为禁止文件写入/变更；
项目和 Django 导入前仍安装 `tools.e2_no_io_guard`。
原有 Mock 仅保留 FTS5 能力探测为 False、`socket.has_ipv6=False`；
不 Mock schema/API，不发送 signal，不调用数据库或 Storage。
这是 E2 守卫下的启动合同证据，不代表完整 P0 E2、迁移图或真实服务验收。

以下 Bash/WSL 示例仅供审查者在单独获授权的可丢弃环境中手工复现，
本次附件整理不重复构建。所有 `/absolute/...` 必须人工替换成明确绝对路径；
`WORK` 必须是仓库、旧站和正式环境之外尚不存在的目录。
`SDIST` 必须是人工准备的原始归档，不能直接信任来源不明的解包目录。
不自动下载、不使用 `--unsafe-paths`，也不在正式 site-packages 上应用补丁。

```bash
set -euo pipefail
REPO=/absolute/path/to/review-worktree
ATTACH="$REPO/tools/compat/wagtail_8_0_1"
SDIST=/absolute/path/to/wagtail-8.0.1.tar.gz
WORK=/absolute/path/to/new-disposable-review-directory
BASE_PYTHON=/absolute/path/to/dependency-ready-python3.13
WHEELHOUSE=/absolute/path/to/prepared-offline-build-wheels

printf '%s  %s\n' \
  819865a10bce86b16288cfaefa4195b90ffb5e7ac494fb18659e7be099ef386f \
  "$SDIST" | sha256sum --check --strict -
printf '%s  %s\n' \
  1d91c2dd724b4f9a20f3abbd52f245ccb88040d9ce2fced1d5d7f371b2d3cf75 \
  "$ATTACH/wagtail-8.0.1-api-v3-startup-v2.patch" | sha256sum --check --strict -
mkdir -- "$WORK"  # 已存在即停止，避免覆盖其他实验
tar --extract --gzip --file="$SDIST" --directory="$WORK" --no-same-owner
SOURCE="$WORK/wagtail-8.0.1"
# 解包目录必须位于任何 Git 仓库之外，避免 apply 的仓库前缀语义。
if git -C "$SOURCE" rev-parse --show-toplevel >/dev/null 2>&1; then
  printf '%s\n' 'STOP: choose an extraction directory outside all Git repositories' >&2
  exit 1
fi
git -C "$SOURCE" apply --check -- "$ATTACH/wagtail-8.0.1-api-v3-startup-v2.patch"
git -C "$SOURCE" apply -- "$ATTACH/wagtail-8.0.1-api-v3-startup-v2.patch"

# BASE_PYTHON 已具备本项目当前依赖。--system-site-packages 只读复用
# 当前基础依赖；安装命令始终指向新 venv，不能指向正式环境解释器。
"$BASE_PYTHON" -B -m venv --system-site-packages "$WORK/build-env"
"$BASE_PYTHON" -B -m venv --system-site-packages "$WORK/test-env"
export PIP_REQUIRE_VIRTUALENV=true PIP_NO_INDEX=1 PIP_DISABLE_PIP_VERSION_CHECK=1
# WHEELHOUSE 须预先具备构建依赖；原实验使用 setuptools 80.9.0。
"$WORK/build-env/bin/python" -B -m pip install \
  --no-index --no-deps --no-cache-dir --find-links "$WHEELHOUSE" setuptools==80.9.0
"$WORK/build-env/bin/python" -B -m pip wheel \
  --no-index --no-deps --no-build-isolation --no-cache-dir \
  --wheel-dir "$WORK/dist" "$SOURCE"
WHEEL="$WORK/dist/wagtail-8.0.1+wb2next.apiv3guard.2-py3-none-any.whl"
sha256sum -- "$WHEEL"  # 记录新产物哈希；不要冒充上述既有测试 wheel
"$WORK/test-env/bin/python" -B -m pip install \
  --no-index --no-deps --ignore-installed --no-cache-dir "$WHEEL"
"$WORK/test-env/bin/python" -B -m pip check
"$WORK/test-env/bin/python" -B "$ATTACH/test_startup_compatibility.py"
"$WORK/test-env/bin/python" -B "$ATTACH/test_startup_compatibility.py" --locales
```

遇到缺失依赖、守卫违规或测试失败即停止并报告，不自动补装或放宽守卫。
两套配置必须分别在新进程运行，各自应执行 20 项且无失败/跳过，
`guard_active=true`、`guard_violations=0`、`api_module_present=false`。
既有隔离环境可直接用其 `bin/python -B` 执行最后两条测试命令，
无需重装任何包；正式环境仅允许只读复用。
