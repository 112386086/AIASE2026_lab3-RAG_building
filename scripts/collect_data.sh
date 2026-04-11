#!/usr/bin/env bash
# scripts/collect_data.sh
# 用途：收集 OpenBMC 相關文件到 data/raw/
# 規格：對齊 SDD_RAG.md v3.0 (支援冪等性、--force 參數、--no-cone 模式、容錯機制)

set -euo pipefail

DATA_RAW="data/raw"
FORCE=0

# ─────────────────────────────────────────────────────────────────────────────
# 1. 冪等性檢查
# ─────────────────────────────────────────────────────────────────────────────
if [[ "${1:-}" == "--force" ]]; then
    FORCE=1
fi

if [[ $FORCE -eq 0 && -d "$DATA_RAW/openbmc-docs" && "$(ls -A "$DATA_RAW/openbmc-docs" 2>/dev/null)" ]]; then
    echo "[*] Data already exists in $DATA_RAW. Skipping download."
    echo "    (Use 'bash collect_data.sh --force' to force re-download)"
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
# 2. 輔助函數：Git Clone (加入容錯機制)
# ─────────────────────────────────────────────────────────────────────────────
clone_export_full_repo() {
    local repo_url="$1"
    local export_dir="$2"
    local workdir
    workdir="$(mktemp -d "$TMP_ROOT/repo.XXXXXX")"

    echo "[*] Cloning ${repo_url} (full shallow clone) ..."
    # 移除 >/dev/null，並加入 if ! 判斷，避免 set -e 中斷腳本
    if ! git clone --depth 1 "$repo_url" "$workdir"; then
        echo "  -> [Error] Failed to clone $repo_url. Skipping." >&2
        return
    fi

    rm -rf "$workdir/.git"
    mkdir -p "$export_dir"
    cp -R "$workdir/." "$export_dir/"
}

clone_export_sparse() {
    local repo_url="$1"
    local export_dir="$2"
    shift 2
    local paths=("$@")
    local workdir
    workdir="$(mktemp -d "$TMP_ROOT/repo.XXXXXX")"

    echo "[*] Cloning ${repo_url} (sparse) ..."
    if ! git clone --depth 1 --filter=blob:none --sparse "$repo_url" "$workdir"; then
        echo "  -> [Error] Failed to clone $repo_url. Skipping." >&2
        return
    fi
    
    if ! git -C "$workdir" sparse-checkout init --no-cone; then
        echo "  -> [Error] Failed to init sparse-checkout. Skipping." >&2
        return
    fi
    
    if ! git -C "$workdir" sparse-checkout set "${paths[@]}"; then
        echo "  -> [Error] Failed to set sparse-checkout paths. Skipping." >&2
        return
    fi

    rm -rf "$workdir/.git"
    mkdir -p "$export_dir"

    for path in "${paths[@]}"; do
        local clean_path="${path%/}"
        if [ -e "$workdir/$clean_path" ]; then
            mkdir -p "$export_dir/$(dirname "$clean_path")"
            cp -R "$workdir/$clean_path" "$export_dir/$clean_path"
        else
            echo "  -> [Warning] Path not found in repo: $clean_path" >&2
        fi
    done
}

# ─────────────────────────────────────────────────────────────────────────────
# 3. 執行步驟
# ─────────────────────────────────────────────────────────────────────────────

# 1) openbmc/docs
clone_export_full_repo "https://github.com/openbmc/docs.git" "$DATA_RAW/openbmc-docs"

# 2) openbmc/bmcweb
clone_export_sparse "https://github.com/openbmc/bmcweb.git" "$DATA_RAW/bmcweb" docs README.md

# 3) openbmc/phosphor-dbus-interfaces
clone_export_sparse "https://github.com/openbmc/phosphor-dbus-interfaces.git" "$DATA_RAW/phosphor-dbus-interfaces" yaml README.md

# 4) openbmc/entity-manager
clone_export_sparse "https://github.com/openbmc/entity-manager.git" "$DATA_RAW/entity-manager" configurations docs README.md

# 5) openbmc/linux (⚠️ 巨大 Repo)
echo "[*] Cloning openbmc/linux (This might take a moment due to repo size)..."
clone_export_sparse "https://github.com/openbmc/linux.git" "$DATA_RAW/linux-devicetree" arch/arm/boot/dts/aspeed Documentation/devicetree/bindings/gpio

# 6) openbmc/phosphor-gpio-monitor
clone_export_sparse "https://github.com/openbmc/phosphor-gpio-monitor.git" "$DATA_RAW/phosphor-gpio-monitor" README.md

# 7) IBM Power10 OpenBMC 文件
echo "[*] Fetching IBM Power10 OpenBMC documentation..."
mkdir -p "$DATA_RAW/supplementary"
IBM_URL="https://www.ibm.com/docs/zh-tw/power10/7063-CR2?topic=tool-basic-commands-functionality-openbmc"
IBM_OUT="$DATA_RAW/supplementary/ibm_power10_openbmc.md"
TMP_HTML="$TMP_ROOT/ibm_temp.html"

if command -v pandoc >/dev/null 2>&1; then
    echo "  -> Downloading HTML to temporary file..."
    if curl -sSL "$IBM_URL" -o "$TMP_HTML"; then
        echo "  -> Converting HTML to Markdown..."
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