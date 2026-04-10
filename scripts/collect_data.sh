#!/usr/bin/env bash
# scripts/collect_data.sh (DEBUG MODE)
# 用途：收集 OpenBMC 相關文件，並啟用詳細除錯輸出

# set -e: 遇到錯誤即停止
# set -u: 使用未定義變數即報錯
# set -o pipefail: 管線中任一指令失敗即視為失敗
# set -x: 執行每一行指令前，先把它印出來 (!!! DEBUG !!!)
set -euo pipefail
set -x

DATA_RAW="data/raw"
FORCE=0

# ─────────────────────────────────────────────────────────────────────────────
# 1. 冪等性檢查 (Idempotency Check)
# ─────────────────────────────────────────────────────────────────────────────
if [[ "${1:-}" == "--force" ]]; then
    FORCE=1
fi

if [[ $FORCE -eq 0 && -d "$DATA_RAW/openbmc-docs" && "$(ls -A "$DATA_RAW/openbmc-docs" 2>/dev/null)" ]]; then
    echo "[*] Data already exists in $DATA_RAW. Skipping download."
    echo "    (Use './collect_data.sh --force' to force re-download)"
    exit 0
fi

if [[ $FORCE -eq 1 ]]; then
    echo "[*] Force mode enabled. Cleaning up old data..."
    rm -rf "$DATA_RAW"
fi

TMP_ROOT="$(mktemp -d)"
trap 'rm -rf "$TMP_ROOT"' EXIT
mkdir -p "$DATA_RAW"

# ─────────────────────────────────────────────────────────────────────────────
# 2. 輔助函數：Git Clone
# ─────────────────────────────────────────────────────────────────────────────
clone_export_full_repo() {
    local repo_url="$1"
    local export_dir="$2"
    local workdir
    workdir="$(mktemp -d "$TMP_ROOT/repo.XXXXXX")"

    echo "[*] Cloning ${repo_url} (full shallow clone) ..."
    # 【DEBUG】移除 >/dev/null 2>&1，顯示完整 git 輸出
    git clone --depth 1 "$repo_url" "$workdir"

    echo "DEBUG: Full clone completed. Removing .git..."
    rm -rf "$workdir/.git"
    mkdir -p "$export_dir"
    cp -R "$workdir/." "$export_dir/"
    echo "DEBUG: Full repo copied to $export_dir"
}

clone_export_sparse() {
    local repo_url="$1"
    local export_dir="$2"
    shift 2
    local paths=("$@")
    local workdir
    workdir="$(mktemp -d "$TMP_ROOT/repo.XXXXXX")"

    echo "[*] Cloning ${repo_url} (sparse) ..."
    # 【DEBUG】移除 >/dev/null 2>&1，顯示完整 git 輸出
    git clone --depth 1 --filter=blob:none --sparse "$repo_url" "$workdir"

    echo "DEBUG: Sparse clone completed. Initializing sparse-checkout..."
    git -C "$workdir" sparse-checkout init --no-cone

    echo "DEBUG: Setting sparse-checkout paths: ${paths[@]}"
    git -C "$workdir" sparse-checkout set "${paths[@]}"

    echo "DEBUG: Sparse checkout set. Removing .git..."
    rm -rf "$workdir/.git"
    mkdir -p "$export_dir"

    echo "DEBUG: Copying sparse files..."
    for path in "${paths[@]}"; do
        if [ -e "$workdir/$path" ]; then
            mkdir -p "$export_dir/$(dirname "$path")"
            cp -R "$workdir/$path" "$export_dir/$path"
        else
            echo "  -> [Warning] Path not found in repo: $path" >&2
        fi
    done
    echo "DEBUG: Sparse repo copied to $export_dir"
}

# ─────────────────────────────────────────────────────────────────────────────
# 3. 執行步驟 (對齊 SDD 3.2)
# ─────────────────────────────────────────────────────────────────────────────

# 1) openbmc/docs
clone_export_full_repo \
    "https://github.com/openbmc/docs.git" \
    "$DATA_RAW/openbmc-docs"

# 2) openbmc/phosphor-dbus-interfaces
clone_export_sparse \
    "https://github.com/openbmc/phosphor-dbus-interfaces.git" \
    "$DATA_RAW/phosphor-dbus-interfaces" \
    yaml README.md requirements.md

# 3) openbmc/bmcweb
clone_export_sparse \
    "https://github.com/openbmc/bmcweb.git" \
    "$DATA_RAW/bmcweb" \
    docs DEVELOPING.md README.md

# 4) IBM Power10 OpenBMC 文件 (Web Scraping via curl + pandoc)
# ... (這部分暫時不變) ...
echo "[*] Fetching IBM Power10 OpenBMC documentation..."
mkdir -p "$DATA_RAW/supplementary"
IBM_URL="https://www.ibm.com/docs/zh-tw/power10/7063-CR2?topic=tool-basic-commands-functionality-openbmc"
IBM_OUT="$DATA_RAW/supplementary/ibm_power10_openbmc.md"
TMP_HTML="$TMP_ROOT/ibm_temp.html"

if command -v pandoc >/dev/null 2>&1; then
    if curl -sSL "$IBM_URL" -o "$TMP_HTML"; then
        if pandoc "$TMP_HTML" -f html -t markdown -o "$IBM_OUT"; then
            echo "  -> Successfully fetched and converted IBM docs."
        else
            echo "  -> [Warning] Pandoc conversion failed. Skipping."
        fi
    else
        echo "  -> [Warning] curl failed to download the page. Skipping."
    fi
else
    echo "  -> [Warning] 'pandoc' is not installed or not in PATH. Skipping IBM docs."
fi


echo "============================================================"
echo "Done. Collected files are under: $DATA_RAW"
echo "Total files collected: $(find "$DATA_RAW" -type f | wc -l)"