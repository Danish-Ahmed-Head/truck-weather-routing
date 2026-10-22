# 13 Deployment Guide: PythonAnywhere (free Beginner plan)

Decision recorded 2026-10-20: host on PythonAnywhere free. Pricing and limits read from the vendor pages on 2026-10-20.
Status: **deployed and verified 2026-10-20; updated and re-verified 2026-10-21 (commit f13fea0)** at https://danish12ahmed.pythonanywhere.com (health check OK, full search returned 3 routes).

## 1. Fit with the free plan

| Item | Free plan (vendor pages, 2026-10-20) | This app |
|---|---|---|
| Web apps | 1, at `USERNAME.pythonanywhere.com` | 1 |
| Web workers | 1 | One search takes 6-14 s, so a second visitor waits |
| CPU allowance | 100 seconds per day | Setup (installs, build) plus one search used 32.9 s. A cold search cost 2.2 to 3.5 CPU-seconds locally; PythonAnywhere's own cost per search was not measured separately |
| Storage | 512 MB | Repository, virtualenv and build are well under the quota (temporary Node tooling is deleted after the build) |
| Outbound internet | Allowlisted hosts only | The allowlist includes `api.open-meteo.com`, `nominatim.openstreetmap.org`, `router.project-osrm.org`, `github.com`, `pypi.org`, `registry.npmjs.org` |
| Python | 3.12 and 3.13 on the `innit` system image | Python 3.12.8 |
| Expiry | **Site is disabled after one month unless you click "Run until 1 month from today" on the Web tab** | Currently set to expire Fri 2026-11-20 |

Not verified: the maximum request time on the free plan.

## 2. What was done (and why it differs from the first draft of this guide)

The first draft assumed uploading a zip. The built-in browser used for the deployment has no file-upload tool, and the PythonAnywhere
page blocks cross-origin fetches by its content security policy, so the code was pulled from the public GitHub repository instead.
The frontend build is not in git, so it was built on the server with Node 24 installed from PyPI (`nodejs-wheel`), then the Node
tooling was removed.

1. Clone: `git clone https://github.com/Danish-Ahmed-Head/truck-weather-routing.git` (home folder).
2. Virtualenv: `mkvirtualenv --python=/usr/bin/python3.12 truck-venv`, then `pip install -r truck-weather-routing/backend/requirements.txt`.
3. Frontend build: `python3.12 -m venv ~/nodeenv`, `~/nodeenv/bin/pip install nodejs-wheel`, put `~/nodeenv/bin` on PATH,
   `cd truck-weather-routing/frontend && npm ci && npm run build` (writes `backend/frontend_dist`, about 11 s install, 0.3 s build).
   Then `rm -rf ~/nodeenv ~/truck-weather-routing/frontend/node_modules`.
4. Web tab: Add a new web app, accept the domain, Manual configuration, Python 3.12.
5. Web tab Code section: Source code and Working directory `/home/USERNAME/truck-weather-routing/backend`; Virtualenv `truck-venv`.
6. WSGI file `/var/www/USERNAME_pythonanywhere_com_wsgi.py`: adds the backend folder to `sys.path`, sets `DJANGO_SETTINGS_MODULE=config.settings`,
   `DJANGO_ALLOWED_HOSTS=USERNAME.pythonanywhere.com`, a `HTTP_USER_AGENT` that links to the repository, and `DJANGO_SECRET_KEY`.
   The key was generated on the server by a short script that wrote the file directly and then deleted itself, so the key was never displayed or typed.
7. Reload the web app, then check `/api/health` and run a search.

## 3. Updating later

In a Bash console: `cd ~/truck-weather-routing && git pull`. If the frontend changed, rebuild it as in step 3 (or ask for the bundle route
using `scripts/make_bundle.py` and the Files tab upload). Then click **Reload** on the Web tab.

Verified on 2026-10-21 (twice): in the Bash console run `cd ~/truck-weather-routing && git pull origin master`, then
`python3.12 -m venv ~/nodeenv && ~/nodeenv/bin/pip install -q nodejs-wheel && export PATH=$HOME/nodeenv/bin:$PATH && cd frontend && npm ci && npm run build`,
then `rm -rf ~/nodeenv ~/truck-weather-routing/frontend/node_modules`, then Reload. It takes about two minutes, mostly the pip install.
Backend-only changes need only the pull and Reload. Check the update took effect by comparing the `assets/index-*.js` name in the page source
with the new build, and `curl -I` for new headers. Do not rebuild on the day of a review if the CPU meter is high (100 s per day).

## 4. Keeping it alive

Log in at least once a month and click **Run until 1 month from today** on the Web tab. PythonAnywhere emails a reminder a week before.

## 5. If something fails

Web tab, Log files: Error log and Server log. Common causes: a typo in the username in the WSGI paths, a wrong virtualenv name, or
`DJANGO_ALLOWED_HOSTS` not matching the address.

## 6. Not set on purpose

`DJANGO_FORCE_HTTPS` is left off because it was not verified how PythonAnywhere forwards the HTTPS header; turning it on wrongly
could cause a redirect loop. Set it only after testing.
