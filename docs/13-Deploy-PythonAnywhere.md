# 13 Deployment Guide: PythonAnywhere (free Beginner plan)

Decision recorded 2026-10-20: host on PythonAnywhere free. Pricing and limits read from the vendor pages on 2026-10-20.
Status: **prepared and bundle-tested locally; not deployed.** Deploying creates an account and publishes the app, so it is the owner's step.

## 1. Fit with the free plan

| Item | Free plan (vendor page, 2026-10-20) | This app |
|---|---|---|
| Web apps | 1, at `USERNAME.pythonanywhere.com` | 1 |
| Web workers | 1 | One search takes 6-14 s, so a second visitor waits |
| CPU allowance | 100 seconds per day | Measured locally: 2.2 to 3.5 CPU-seconds per cold search, so about 30-45 fresh searches per day. PythonAnywhere's CPU speed was **not** measured |
| Storage | 512 MB | Bundle is 135 KB; dependencies about 100 MB |
| Outbound internet | Allowlisted hosts only | The allowlist lists `api.open-meteo.com`, `nominatim.openstreetmap.org`, `router.project-osrm.org`; map tiles load in the visitor's browser |
| Python | Python 3.12 and 3.13 exist on the `innit` system image | Needs 3.12 or newer for Django 6.1.2 |
| Docker | Not available | Not needed; plain WSGI |

Not verified: whether free web apps need a periodic "extend" click (check the Web tab for an expiry notice), the maximum request time,
and whether new accounts get the `innit` image (check Account tab, "System Image").

## 2. Prepare the bundle (done)

`deploy/truck-routing-bundle.zip` (git-ignored, rebuild with `python scripts/make_bundle.py` after `npm run build`).
It unpacks to `truck-routing/backend/` and contains the built frontend. Tested by unzipping into a clean folder and
requesting `/api/health`, `/` and both assets (all OK).

## 3. Steps (replace USERNAME with your PythonAnywhere username)

**A. Account.** Go to pythonanywhere.com, click **Pricing & signup**, click **Create a Beginner account**, pick a username
(it becomes your web address), confirm your email, log in.

**B. Upload.** Click the **Files** tab. Under "Upload a file" click **Upload a file**, choose
`D:\Dev\truck-weather-routing\deploy\truck-routing-bundle.zip`. It lands in `/home/USERNAME`.

**C. Install.** Click the **Consoles** tab, under "Start a new console" click **Bash**. Type each line and press Enter:

```bash
unzip -o truck-routing-bundle.zip
mkvirtualenv --python=/usr/bin/python3.12 truck-venv
pip install -r truck-routing/backend/requirements.txt
python -c "import secrets; print(secrets.token_urlsafe(64))"
```

Copy the long text the last line prints (the secret key). If `python3.12` is not found, run `ls /usr/bin/python3*` and use
the highest 3.12 or 3.13 path.

**D. Create the web app.** Click the **Web** tab, **Add a new web app**, **Next** (domain page), choose **Manual configuration**
(not "Django"), choose **Python 3.12**, **Next**.

**E. Point it at the code.** On the Web tab:
1. "Virtualenv": click "Enter path to a virtualenv", type `truck-venv`, click the tick.
2. "Code": set **Source code** and **Working directory** to `/home/USERNAME/truck-routing/backend`.

**F. Settings file.** On the Web tab click the **WSGI configuration file** link (`/var/www/USERNAME_pythonanywhere_com_wsgi.py`).
Delete everything, paste this, replace the three capitalised values, click **Save**:

```python
import os
import sys

path = "/home/USERNAME/truck-routing/backend"
if path not in sys.path:
    sys.path.insert(0, path)

os.environ["DJANGO_SETTINGS_MODULE"] = "config.settings"
os.environ["DJANGO_SECRET_KEY"] = "PASTE_THE_KEY_FROM_STEP_C"
os.environ["DJANGO_ALLOWED_HOSTS"] = "USERNAME.pythonanywhere.com"
os.environ["HTTP_USER_AGENT"] = "weather-aware-truck-routing/1.0 (contact: YOUR_EMAIL)"

from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()
```

The key stays in this file on PythonAnywhere only; it is not in the repository. Nominatim asks for a User-Agent with a contact address.

**G. Go live.** Back on the Web tab click the big green **Reload USERNAME.pythonanywhere.com** button. Open
`https://USERNAME.pythonanywhere.com/api/health` (should show `{"status": "ok"}`), then the main address and run a search.

**H. If something fails.** Web tab, "Log files", open the **Error log** and **Server log**. Common causes: a typo in
`USERNAME`, wrong virtualenv name, or `DJANGO_ALLOWED_HOSTS` not matching the address.

## 4. Updating later

Rebuild the bundle, upload it again (step B), run `unzip -o truck-routing-bundle.zip` in a Bash console, click **Reload**.

## 5. Not set on purpose

`DJANGO_FORCE_HTTPS` is left off because it was not verified how PythonAnywhere forwards the HTTPS header; turning it on
wrongly could cause a redirect loop. Set it only after testing.
