import os

RENEW_URL = os.environ.get("GAME4FREE_RENEW_URL","").strip()
COOKIE = os.environ.get("GAME4FREE_COOKIE","").strip()

ACCOUNTS = []
for line in os.environ.get("GAME4FREE_ACCOUNTS","").split("\n"):
    line = line.strip()
    if not line:
        continue
    parts = line.split("|||")
    if len(parts) >= 3:
        ACCOUNTS.append((parts[0].strip(), parts[1].strip(), parts[2].strip()))

for line in os.environ.get("GAME4FREE_ACCOUNT","").split("\n"):
    line = line.strip()
    if not line:
        continue
    parts = line.split("|||")
    if len(parts) >= 3:
        if "@" in parts[2] and not parts[1].startswith("http"):
            ACCOUNTS.append((parts[0].strip(), "https://control.gaming4free.net/server/" + parts[1].strip(), parts[2].strip()))

SERVERS = []
if RENEW_URL and COOKIE:
    server_name = "我的服务器"
    if "/server/" in RENEW_URL:
        slug = RENEW_URL.split("/server/")[1].split("/")[0]
        server_name = f"服务器-{slug[:8]}"
    SERVERS.append((server_name, RENEW_URL, COOKIE))
for name, url, cookie in ACCOUNTS:
    SERVERS.append((name, url, cookie))
