#!/usr/bin/env bash
# AIC8800DC/FC 一键卸载 —— 对应 install.sh
set -uo pipefail

PKG="aic8800-ref"
VER="1.0"
KVER="$(uname -r)"
SRC="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

ok(){   printf '  \033[32m✓\033[0m %s\n' "$1"; }
step(){ printf '\n\033[1;36m==> %s\033[0m\n' "$1"; }

if [ "$(id -u)" -ne 0 ]; then
	echo "需要 root 权限，正在用 sudo 重新运行…"
	exec sudo -E bash "$0" "$@"
fi

step "卸载模块"
modprobe -r aic8800_fdrv 2>/dev/null || true
modprobe -r aic_load_fw  2>/dev/null || true
ok "已卸载内存中的模块"

step "移除 DKMS / make 安装的模块"
if command -v dkms >/dev/null 2>&1; then
	dkms remove -m "$PKG" -v "$VER" --all 2>/dev/null || true
fi
rm -rf "/usr/src/${PKG}-${VER}"
make -C "${SRC}/drivers/aic8800" uninstall 2>/dev/null || true
rm -f "/lib/modules/${KVER}/updates/dkms/aic_load_fw.ko"* \
      "/lib/modules/${KVER}/updates/dkms/aic8800_fdrv.ko"* 2>/dev/null || true
depmod -a
ok "模块文件已清理"

step "移除固件与 udev 规则"
rm -rf /lib/firmware/aic8800DC
rm -f  /etc/udev/rules.d/aic.rules
udevadm control --reload 2>/dev/null || true
ok "固件与 udev 规则已移除"

echo
ok "卸载完成。"
