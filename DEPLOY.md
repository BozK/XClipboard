# Deploying with Docker

The app runs as a single container built on the server from this repo. No image registry is involved.
Caddy stays on the host and reverse proxies to `localhost:8001`, same as before.

## Server layout

```
/srv/xclipboard/               owner: you
├── app/                       owner: you   <- this repo (git clone)
│   └── .env -> ../.env                     <- symlink so compose can read APP_UID/APP_GID
├── data/                      owner: xclipboard:xclipboard, group-writable, setgid
│   ├── db/                                 <- xclipboard.db
│   ├── files/                              <- uploaded file clips (+ thumbs/ previews)
│   └── logs/                               <- daily log files
└── .env                       owner: you, mode 600
```

Code lives in `app/` and can always be re-cloned. `data/` and `.env` are the only things that need backing up,
and keeping them outside the repo means `git clean` can never touch them.

The container runs as a dedicated `xclipboard` system user, not as you. If the app were ever compromised and
escaped the container, it would land as an unprivileged user that can't read your home directory or use Docker.
You're in the `xclipboard` group, so you can still read the DB and logs without sudo.

## First-time setup

```sh
# App user + folders
sudo adduser --system --group --no-create-home xclipboard
sudo mkdir -p /srv/xclipboard/data/db /srv/xclipboard/data/files /srv/xclipboard/data/logs
sudo chown $USER:$USER /srv/xclipboard
sudo chown -R xclipboard:xclipboard /srv/xclipboard/data
sudo chmod -R g+rwX /srv/xclipboard/data
sudo find /srv/xclipboard/data -type d -exec chmod g+s {} +
sudo usermod -aG xclipboard $USER          # log out and back in for this to apply

# Code + config
git clone git@github.com:BozK/XClipboard.git /srv/xclipboard/app
cp /srv/xclipboard/app/.env.example /srv/xclipboard/.env
chmod 600 /srv/xclipboard/.env
ln -s ../.env /srv/xclipboard/app/.env
id xclipboard                              # put the uid/gid into .env as APP_UID/APP_GID, fill in the rest
```

Create `data/` yourself before the first `up`. If Docker creates the mount folders, they're owned by root
and the container can't write to them.

`compose.yaml` refuses to run without `APP_UID`/`APP_GID` rather than silently picking a default UID.
If you see "APP_UID missing", the `.env` values or the `app/.env` symlink are missing.

Then either copy an existing database into `data/db/xclipboard.db` (and `sudo chown xclipboard:xclipboard` it),
or create a fresh one:

```sh
cd /srv/xclipboard/app
docker compose run --rm xclipboard python db/CreateTables.py
```

## Deploying changes

```sh
cd /srv/xclipboard/app && git pull && ./run.sh
```

`run.sh` runs `docker compose up -d --build`. Only changed layers rebuild, and the old container keeps serving
until the new image is built.

Occasionally pick up base image security updates (new Python/Node patch releases, Debian fixes):

```sh
docker compose build --pull && docker compose up -d
```

### One-time upgrade: file clips

The release that added file/image clips needs a new `data/files` folder and a new `ClipFiles` table.
Run this once before (or right after) the first `./run.sh` with that code. Until it's done, the clips list fails to load.

```sh
sudo install -d -o xclipboard -g xclipboard -m 2775 /srv/xclipboard/data/files
cd /srv/xclipboard/app && docker compose run --rm xclipboard python db/CreateTables.py
```

`CreateTables.py` only creates tables that are missing, so it's safe to rerun on an existing database.

## Day to day

| Task | Command (from `app/`) |
|---|---|
| Follow logs | `docker compose logs -f` |
| Status | `docker compose ps` |
| Restart | `docker compose restart` |
| Stop | `docker compose down` |
| Clean up old images | `docker image prune` (avoid `-a`, it also drops cached base images) |

## Migrating from the systemd service

1. `sudo systemctl stop xclipboard` so the database isn't mid-write, then copy `xclipboard.db` into `data/db/`
   and `sudo chown xclipboard:xclipboard` it.
2. `sudo systemctl disable xclipboard` (keep the unit file around until you're happy, for rollback).
3. `./run.sh`, then check the site through Caddy.

## Notes

- Keep the port published as `127.0.0.1:8001:8001`. A bare `8001:8001` exposes the app on every interface,
  and Docker-published ports bypass ufw rules.
- Locally you can still run without Docker via `local.sh`. `HOST`, `PORT` and `DB_PATH` default to the old values,
  and `FILES_PATH` defaults to `db/files/`.
- Uploads are capped at 25 MB per file by the app itself. Caddy has no body size limit by default, so nothing to change there.
