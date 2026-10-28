import sys,re
p=sys.argv[1]+"/drivers/aic8800/aic8800_fdrv/aicwf_wext_linux.c"; s=open(p).read()
m=re.search(r"(static int aicwf_get_mode\(struct net_device \*dev, struct iw_request_info \*a,\s*union iwreq_data \*wrqu, char \*b\)\n\{)(.*?)\n\}\n", s, re.S)
assert m
body='''

	AICWFDBG(LOGTRACE, "%s Enter", __func__);

	switch (dev->ieee80211_ptr ? dev->ieee80211_ptr->iftype : NL80211_IFTYPE_UNSPECIFIED) {
	case NL80211_IFTYPE_STATION:
	case NL80211_IFTYPE_P2P_CLIENT:
		wrqu->mode = IW_MODE_INFRA; break;
	case NL80211_IFTYPE_ADHOC:
		wrqu->mode = IW_MODE_ADHOC; break;
	case NL80211_IFTYPE_AP:
	case NL80211_IFTYPE_P2P_GO:
		wrqu->mode = IW_MODE_MASTER; break;
	case NL80211_IFTYPE_MONITOR:
		wrqu->mode = IW_MODE_MONITOR; break;
	default:
		wrqu->mode = IW_MODE_AUTO; break;
	}
	return 0;
'''
s=s[:m.start()]+m.group(1)+body+"}\n"+s[m.end():]
if "#include <net/cfg80211.h>" not in s:
    s=s.replace('#include "aicwf_wext_linux.h"','#include <net/cfg80211.h>\n#include "aicwf_wext_linux.h"',1)
open(p,"w").write(s); print("wext patched",p)
