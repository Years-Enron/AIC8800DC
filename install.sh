#!/usr/bin/env bash
# AIC8800DC/FC 一键安装脚本 —— 绿联 CM760-35262 USB 无线网卡 Linux 驱动
#
# 用法：
#   sudo ./install.sh            # 全自动：装依赖→固件→udev→DKMS 编译安装→加载→自检
#   sudo ./install.sh --no-deps  # 跳过自动安装内核头文件/编译工具
#
# 幂等：可重复运行；重跑会覆盖旧固件、重建 DKMS、重新加载模块。
set -euo pipefail

PKG="aic8800-ref"
VER="1.0"
KVER="$(uname -r)"
SRC="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
AUTO_DEPS=1
[ "${1:-}" = "--no-deps" ] && AUTO_DEPS=0

step(){ printf '\n\033[1;36m==> %s\033[0m\n' "$1"; }
ok(){   printf '  \033[32m✓\033[0m %s\n' "$1"; }
warn(){ printf '  \033[33m!\033[0m %s\n' "$1"; }
err(){  printf '  \033[31m✗\033[0m %s\n' "$1" >&2; }

# ---- 0. 取得 root ----
if [ "$(id -u)" -ne 0 ]; then
	echo "需要 root 权限，正在用 sudo 重新运行…"
	exec sudo -E bash "$0" "$@"
fi

echo "=================================================="
echo " AIC8800DC/FC 驱动安装 (绿联 CM760-35262)"
echo " 内核: ${KVER}    架构: $(uname -m)"
echo "=================================================="

# ---- 1. 依赖：内核头文件 + 编译工具 ----
step "检查编译依赖"
need_deps=0
[ -d "/lib/modules/${KVER}/build" ] || { warn "缺内核头文件 /lib/modules/${KVER}/build"; need_deps=1; }
command -v make >/dev/null 2>&1 || { warn "缺 make"; need_deps=1; }
command -v gcc  >/dev/null 2>&1 || { warn "缺 gcc";  need_deps=1; }

install_deps(){
	if   command -v apt-get >/dev/null 2>&1; then
		apt-get update -y && apt-get install -y dkms build-essential "linux-headers-${KVER}" || \
		apt-get install -y dkms build-essential linux-headers-"$(dpkg --print-architecture)"
	elif command -v dnf >/dev/null 2>&1; then
		dnf install -y dkms make gcc "kernel-devel-${KVER}" || dnf install -y dkms make gcc kernel-devel
	elif command -v pacman >/dev/null 2>&1; then
		pacman -Sy --noconfirm dkms base-devel linux-headers
	elif command -v zypper >/dev/null 2>&1; then
		zypper --non-interactive install dkms make gcc kernel-default-devel
	else
		return 1
	fi
}

if [ "$need_deps" = 1 ]; then
	if [ "$AUTO_DEPS" = 1 ]; then
		warn "尝试自动安装依赖（需要联网）…"
		if install_deps; then ok "依赖安装完成"; else
			err "没识别出包管理器，请手动安装：内核头文件 + dkms + make + gcc"; exit 1
		fi
	else
		err "依赖缺失且指定了 --no-deps，请先手动安装内核头文件/编译工具"; exit 1
	fi
fi
[ -d "/lib/modules/${KVER}/build" ] || { err "仍找不到内核头文件，装完请确认 /lib/modules/${KVER}/build 存在"; exit 1; }
ok "内核头文件与编译工具就绪"

# ---- 2. 固件 ----
step "安装固件到 /lib/firmware/aic8800DC"
cp -rf "${SRC}/fw/aic8800DC" /lib/firmware/
ok "固件已就位（每次插卡从内存加载，不烧录）"

# ---- 3. udev 规则（自动弹出“驱动盘”切到 Wi-Fi 模式）----
step "安装 udev 规则并重载"
cp -f "${SRC}/tools/aic.rules" /etc/udev/rules.d/aic.rules
udevadm control --reload
udevadm trigger || true
ok "udev 规则已安装"

# ---- 4. 编译并安装模块（DKMS 优先，随内核升级自动重建）----
dkms_path(){ command -v dkms >/dev/null 2>&1; }
install_via_dkms(){
	local dst="/usr/src/${PKG}-${VER}"
	rm -rf "$dst"; mkdir -p "$dst"
	tar -C "$SRC" --exclude=.git -cf - . | tar -C "$dst" -xf -
	dkms remove -m "$PKG" -v "$VER" --all >/dev/null 2>&1 || true
	dkms add    -m "$PKG" -v "$VER"
	dkms build  -m "$PKG" -v "$VER"
	dkms install -m "$PKG" -v "$VER" --force
}
install_via_make(){
	make -C "${SRC}/drivers/aic8800" clean >/dev/null 2>&1 || true
	make -C "${SRC}/drivers/aic8800"
	make -C "${SRC}/drivers/aic8800" install
}

step "编译并安装内核模块"
if dkms_path; then
	if install_via_dkms; then ok "DKMS 安装成功（内核升级会自动重建）"; else
		warn "DKMS 失败，回退到普通 make 安装"; install_via_make; ok "make 安装成功"
	fi
else
	warn "未安装 dkms，使用普通 make 安装（内核升级后需重跑本脚本）"
	install_via_make; ok "make 安装成功"
fi

# ---- 5. 加载模块 ----
step "加载驱动"
modprobe -r aic8800_fdrv 2>/dev/null || true
modprobe -r aic_load_fw  2>/dev/null || true
depmod -a
modprobe aic_load_fw
modprobe aic8800_fdrv
ok "模块已加载：aic_load_fw, aic8800_fdrv"

# ---- 6. 自检 ----
step "自检"
[ -e /dev/aicudisk ] && { eject /dev/aicudisk 2>/dev/null || true; ok "已弹出存储盘，切换到 Wi-Fi 模式"; }
for _ in $(seq 1 15); do
	lsusb 2>/dev/null | grep -qi 'a69c:88de' && break
	sleep 1
done
if lsusb 2>/dev/null | grep -qi 'a69c:88de'; then
	ok "检测到 Wi-Fi 模式设备 a69c:88de"
elif lsusb 2>/dev/null | grep -qi 'a69c:5721\|a69c:5722'; then
	warn "设备还在存储盘模式，稍等几秒或重新插拔一次 USB"
else
	warn "没检测到 a69c 设备，请确认网卡已插好"
fi
wlan="$(ip -o link show 2>/dev/null | awk -F': ' '/wl/{print $2}' | head -1)"
if [ -n "$wlan" ]; then
	ok "无线网卡接口已出现：${wlan}"
else
	warn "暂未看到 wl* 接口；可 dmesg | tail 看加载日志，或重新插拔网卡"
fi

echo
echo "=================================================="
ok "安装完成！"
echo "  查看接口:  ip link / iw dev"
echo "  查看日志:  dmesg | grep -i aic | tail"
echo "  卸载:      sudo ./uninstall.sh"
echo "=================================================="
