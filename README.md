# studip-sync

## Installation
Klone das Repo
```
git clone https://github.com/popeye123/studip-sync
cd studip-sync
```
Abhängigkeiten installieren
```shell
# Ubuntu/Debian
sudo apt-get install curl p7zip-full rsync

# OpenSUSE
sudo zypper in curl p7zip rsync

# Arch Linux
sudo pacman -S --needed p7zip rsync curl
```

Kopiere das Skript und die Config Dateien an die entsprechenden Stellen.
**Achtung:** Wenn du die `*.conf` Dateien an eine andere Stelle kopieren willst,
musst du das studip-sync Skript anpassen.
```shell
cp studip-sync /usr/bin
mkdir /etc/studip-sync.conf.d
cp user.conf /etc/studip-sync.conf.d
cp courses.conf /etc/studip-sync.conf.d
chown -R $USER /etc/studip-sync.conf.d
chmod 600 /etc/studip-sync.conf.d/*
```

## Konfiguration
Einstellen von Benutzername und Passwort
```shell
nano /etc/studip-sync.conf.d/user.conf
```

Veranstaltungen und Links zu deren Hauptordnern eintragen
```shell
nano /etc/studip-sync.conf.d/courses.conf
```

## Verwendung
### Manuelle Synchronisation
Der übergebene Pfad **muss** ein absoluter Pfad sein (beginnend mit `/`).
```shell
studip-sync /path/to/sync/dir
```

### Cron Job erstellen
`crontab -e` aufrufen und folgende Zeilen einfügen:
```
# Run at 8:00, 13:00 and 19:00 every day.
0 8,13,19 * * *  studip-sync /path/to/sync/dir
```
