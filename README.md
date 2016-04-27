# studip-sync

## Installation

### Installation auf Arch Linux
```
cd /tmp && wget https://raw.githubusercontent.com/popeye123/studip-sync/master/PKGBUILD && makepkg -sri
```

### Andere Distros

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
```

Kopiere das Skript in einen Ordner aus deinem `$PATH`. Das Skript sucht nach
Konfigurationsdateien in `~/.config/studip-sync`. Wenn dort keine
Konfigurationsdateien gefunden werden, dann wird versucht die Konfiguration von
`/etc/studip-sync.conf.d/` zu lesen. Das Konfigurationsverzeichnis kann auch als
Kommandozeilenparameter übergeben werden.
```shell
cp studip-sync /usr/bin

# Globale Konfiguration in /etc
mkdir /etc/studip-sync.conf.d
cp user.conf /etc/studip-sync.conf.d
cp courses.conf /etc/studip-sync.conf.d
chown -R $USER /etc/studip-sync.conf.d
chmod 600 /etc/studip-sync.conf.d/*

# Lokale Konfiguration in .config
mkdir -p ~/.config/studip-sync
cp user.conf ~/.config/studip-sync # optional wenn studip-sync -i
cp courses.conf ~/.config/studip-sync
chown -R $USER ~/.config/studip-sync
chmod 600 ~/.config/studip-sync/*

```

## Konfiguration
Einstellen von Benutzername und Passwort. Nur benötigt, wenn `studip-sync` im
nicht-interaktiven Modus genutzt wird (z.B. als cronjob).
```shell
nano /etc/studip-sync.conf.d/user.conf
```

Veranstaltungen und Links zu deren Hauptordnern eintragen
```shell
nano /etc/studip-sync.conf.d/courses.conf
```

## Verwendung
### Manuelle Synchronisation
```shell
# Frage nach Passwort und Nutzername
studip-sync -i /path/to/sync/dir

# Liest Passwort und Nutzername aus /etc/studip-sync.conf.d/user.conf
studip-sync /path/to/sync/dir
```

### Cron Job erstellen
`crontab -e` aufrufen und folgende Zeilen einfügen:
```
# Run at 8:00, 13:00 and 19:00 every day.
0 8,13,19 * * *  studip-sync /path/to/sync/dir
```
