# Deploying with Docker

The app runs as a single container built on the server from this repo. No image registry is involved.
Caddy stays on the host and reverse proxies to `localhost:8001`, same as before.

## Server layout

```
/srv/xclipboard/
├── app/          <- this repo (git clone)
├── data/
│   ├── db/       <- xclipboard.db
│   └── logs/     <- daily log files
└── .env          <- copy of .env.example, filled in
```

Code lives in `app/` and can always be re-cloned. `data/` and `.env` are the only things that need backing up,
and keeping them outside the repo means `git clean` can never touch them.

## First-time setup

```sh
sudo mkdir /srv/xclipboard
sudo chown $USER:$USER /srv/xclipboard
git clone git@github.com:BozK/XClipboard.git /srv/xclipboard/app
mkdir -p /srv/xclipboard/data/db /srv/xclipboard/data/logs
cp /srv/xclipboard/app/.env.example /srv/xclipboard/.env   # then edit it
```

Create `data/` yourself before the first `up`. If Docker creates the mount folders, they're owned by root
and the container can't write to them.

The container runs as UID 1000 so it can write to `data/`. If `id -u` prints something else, add this to
your `~/.profile` so every build uses your UID:

```sh
export APP_UID=$(id -u)
```

Then either copy an existing database into `data/db/xclipboard.db`, or create a fresh one:

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

## Day to day

| Task | Command (from `app/`) |
|---|---|
| Follow logs | `docker compose logs -f` |
| Status | `docker compose ps` |
| Restart | `docker compose restart` |
| Stop | `docker compose down` |
| Clean up old images | `docker image prune` (avoid `-a`, it also drops cached base images) |

## Migrating from the systemd service

1. `sudo systemctl stop xclipboard` so the database isn't mid-write, then copy `xclipboard.db` into `data/db/`.
2. `sudo systemctl disable xclipboard` (keep the unit file around until you're happy, for rollback).
3. `./run.sh`, then check the site through Caddy.

## Notes

- Keep the port published as `127.0.0.1:8001:8001`. A bare `8001:8001` exposes the app on every interface,
  and Docker-published ports bypass ufw rules.
- Locally you can still run without Docker via `local.sh`. `HOST`, `PORT` and `DB_PATH` default to the old values.
