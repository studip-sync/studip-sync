# studip-sync

Download and synchronize files and media from Stud.IP -- the campus management platform deployed at several German universities.
Note that this fork currently only works at the *University of Göttingen*.

## Installation

1. `git clone https://github.com/lenke182/studip-sync`
2. Install all needed dependencies
3. Then run `./studip_sync.py -d /path/to/files -m /path/to/media` to sync files to `/path/to/files` and media to `/path/to/media`. (see Usage)

To create a permanent configuration:

1. Run `./studip_sync.py --init` (see Configuration)
2. Schedule a cron job or manually run `./studip_sync.py` to sync your data.

## Configuration

To create a new configuration file execute:

```shell
./studip_sync.py --init
```

### Example

```json
{
    "user": {
        "login": "bob42",
        "password": "password"
    },
    "files_destination": "/home/bob/Documents/Uni",
    "media_destination": "/home/bob/Videos/Uni",
}

```

The `files_destination` and `media_destination` option are optional. If you omit one of them, the corresponding feature is disabled. You can also specify both options on the commandline. (Using `-d` implies automatically `--full` if no config is present)
If you omit the `login` or `password`, studip-sync will ask for them interactively.

## Usage

### Full sync instead of incremental sync

studip-sync checks if new files have been edited since the last sync to limit the data which needs to be downloaded on every sync.
If you don't want this happen and prefer to always download all data, use:
```shell
./studip_sync.py --full
```

### Only sync the last semester

To sync only the last semester and skip older courses, use the `--recent` flag. (This option will be ignored if `--full` is supplied).
```shell
./studip_sync.py --recent
```

### Running studip-sync manually
```shell
# Synchronizes files to /path/to/sync/dir
# and uses a non-default location for the config file
./studip_sync.py -c ./config.json -d /path/to/sync/dir

# Reads all parameters from ~/.config/studip-sync/config.json
./studip_sync.py
```

### Automation using a cron job
Run `crontab -e` and add the following lines:
```
# Run at 8:00, 13:00 and 19:00 every day.
0 8,13,19 * * *  /path/to/studip-sync/studip_sync.py
```
