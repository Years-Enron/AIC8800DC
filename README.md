> **中文** · [English](README.en.md)

# 绿联 CM760-35262 Linux 驱动（AIC8800DC/FC）

**AIC8800DC/FC** USB 无线网卡的 Linux 驱动，对应 **绿联 CM760-35262** 免驱 USB 网卡（Wi-Fi 模式 USB ID `a69c:88de`）。这是厂商（绿联 / AICSemi）原始驱动，打了补丁后可在新内核上编译运行，已跟进到 **内核 7.1** 的 cfg80211 接口变化。

已在 **Linux 7.1.5（arm64）Kali** 上验证，更早也在内核 6.16（openSUSE Tumbleweed）上验证过。**普通联网、监听模式（monitor）、802.11 注入**在这块网卡上都能用。

> **说明 / 致谢。** 驱动不是我写的，代码来自绿联 CM760-35262 随卡驱动（原始出处 <https://www.lulian.cn/download/122.html>）。本仓库只是把它适配到新内核、修了几个 bug。部分修复参考了 [shenmintao/aic8800d80](https://github.com/shenmintao/aic8800d80)，基础移植来自 [idawnlight/AIC8800DC](https://github.com/idawnlight/AIC8800DC)，感谢原作者。除编译/兼容问题外恕不提供支持。

---

## 开箱即用（一条命令）

插好网卡，在仓库目录里执行：

```bash
sudo ./install.sh
```

脚本会自动完成：**装编译依赖（内核头文件 + dkms + gcc/make）→ 装固件 → 装 udev 规则 → 用 DKMS 编译安装（内核升级自动重建）→ 加载模块 → 自检网卡**。跑完 `ip link` 里就应出现 `wlan*`/`wl*` 接口，连 Wi-Fi 即可。

> 依赖需要联网安装；如果机器此刻没网，先在有网的环境装好 `linux-headers-$(uname -r)`、`dkms`、`build-essential`（或对应发行版的包），再跑脚本。
> 已装过内核头文件、不想让脚本动包管理器：`sudo ./install.sh --no-deps`。

卸载：

```bash
sudo ./uninstall.sh
```

脚本幂等，可重复执行；重跑会覆盖旧固件、重建 DKMS、重新加载模块。

---

## 硬件

- 芯片：AIC8800DC/FC，识别为 `chip_id=7, chip_sub_id=1`（即 “MCU1” 版本）。
- 网卡的 USB 身份：
  - `a69c:5721` / `a69c:5722` —— 虚拟光盘 / U 盘（“驱动盘”）模式。
  - `a69c:88de` —— Wi-Fi 模式，弹出存储盘后出现。
- 频段：本型号仅 **2.4 GHz**（无 5 GHz）。
- 固件每次插卡从 `/lib/firmware/aic8800DC/` 载入内存（不烧录到网卡）。

仓库里的 `tools/aic.rules` udev 规则会自动弹出存储盘，让芯片切到 Wi-Fi 模式。

---

## 手动安装（不想用一键脚本时）

```bash
# 1. 装固件 + udev 规则（弹出“驱动盘”切到 Wi-Fi 模式）
sudo cp -rf fw/aic8800DC /lib/firmware/
sudo cp tools/aic.rules /etc/udev/rules.d/
sudo udevadm control --reload && sudo udevadm trigger

# 2. 编译内核模块
cd drivers/aic8800
make
sudo make install

# 3. 加载
sudo depmod -a
sudo modprobe aic_load_fw
sudo modprobe aic8800_fdrv
```

### DKMS（随内核升级自动重建，推荐）

```bash
sudo cp -r . /usr/src/aic8800-ref-1.0
sudo dkms add    aic8800-ref/1.0
sudo dkms build  aic8800-ref/1.0
sudo dkms install aic8800-ref/1.0 --force
```

一键脚本 `install.sh` 默认就走 DKMS 这条路。

### 手动卸载

```bash
sudo ./uninstall_setup.sh                 # 只删固件 + udev 规则（厂商原脚本）
sudo dkms remove aic8800-ref/1.0 --all    # 若用 DKMS 装的
```

---

## 排错

| 现象 | 处理 |
| --- | --- |
| `lsusb` 只看到 `a69c:5721/5722`，没 `88de` | 还在存储盘模式。等几秒让 udev 弹盘，或手动 `sudo eject /dev/aicudisk`，再不行重新插拔一次 USB。 |
| 出现 `a69c:88dc`、加载失败 | 上次 probe 失败卡住了。**物理重新插拔**网卡（软件 detach/reattach 清不掉这个状态）。 |
| `install.sh` 报缺内核头文件 | 装 `linux-headers-$(uname -r)`（Debian/Ubuntu）/ `kernel-devel`（Fedora）/ `linux-headers`（Arch）/ `kernel-default-devel`（openSUSE）后重跑。 |
| 虚拟机里切模式失败（`error -71`） | 在**宿主机**上弹盘/切模式，再把 `88de` 设备透传给虚拟机；或把 USB 设备 detach 后重新 attach 一次。 |
| 看不到 `wl*` 接口 | `dmesg | grep -i aic | tail` 看加载日志；确认固件在 `/lib/firmware/aic8800DC/`；重新插拔网卡。 |

更多构建/兼容细节和测试结果见 [`PORTING.md`](PORTING.md)。

---

## `patches/` —— 每个修复改了什么

`drivers/` 目录里的代码**已经打好补丁**，可直接编译。`patches/` 保留的是在**厂商原始源码**基础上逐个修改的脚本，作为改动记录；每个脚本以仓库根目录为参数、改 `drivers/aic8800/aic8800_fdrv/*`，用于对着**干净的厂商源码树**重放，不是对本仓库再跑一遍。

| 脚本 | 作用 |
| --- | --- |
| `patch_linux71.py` | 内核 ≥ 7.1 的 cfg80211 / nl80211 接口移植（基于 wdev 的 key/station 操作、`radio_idx` 参数、`in_hardirq`、TDLS 字段位移）。这是能在 7.1 上编译的关键。 |
| `patch_monitor.py`、`patch_monitor2.py`、`patch_monitor3.py` | 让 `iw ... set type monitor` 成功（别把自动创建的 P2P-device vif 当成冲突的数据接口；修一个 vif/vif_el 笔误）。 |
| `patch_wext.py` | 让传统 Wireless-Extensions 的 `SIOCGIWMODE` 上报真实接口模式，使读它的工具能识别监听模式。 |
| `patch_wext_freq.py` | 从 vif chanctx 上报真实监听信道，而不是写死的值。 |
| `patch_inject.py` | 打开监听发包路径（`CONFIG_RWNX_MON_XMIT=y`），解析前对 radiotap 头做边界检查。 |
| `patch_carrier.py` | 监听接口保持 carrier 为 ON（厂商代码无条件 `netif_carrier_off`，导致 qdisc 丢掉注入帧）。 |
| `patch_rxcnt_leak.py` | 在“无消息缓冲”错误路径上保持 `rx_cnt` 平衡，使 busrx 线程持续被唤醒。 |
| `patch_mondata_null.py` | 关掉 `CONFIG_RWNX_MON_DATA` 时，守住可能解引用空 `skb_monitor` 的监听转发路径。 |

---

## 许可

内核模块声明 `MODULE_LICENSE("GPL")`，见 [`LICENSE`](LICENSE)（GPL-2.0）。`fw/` 下的固件是可再分发的厂商固件，不在 GPL 覆盖范围内。
