# studip-sync

[![studip-sync](https://snapcraft.io/studip-sync/badge.svg)](https://snapcraft.io/studip-sync)

Download and synchronize files and media from Stud.IP -- the campus management platform deployed at several German universities.

Note that this project currently only supports the *University of Göttingen* and the *University of Passau* but 
could work at other universities with similar authentication methods.

## Installation

### Using pipx (recommended)
Make sure you have [pipx](https://pipx.pypa.io) installed.
Then run
```shell
pipx install git+https://github.com/studip-sync/studip-sync.git
```

### From source

1. `git clone https://github.com/studip-sync/studip-sync`
2. Install all needed dependencies
3. Then run `./studip_sync.py -d /path/to/files -m /path/to/media` to sync files to `/path/to/files` and media to `/path/to/media`. (see Usage)

To create a permanent configuration:

1. Run `./studip_sync.py --init` (see Configuration)
2. Schedule a cron job or manually run `./studip_sync.py` to sync your data.

### As a snap package

1. If not yet installed, [install snapd](https://docs.snapcraft.io/core/install)
2. `sudo snap install --beta studip-sync`
3. `sudo snap connect studip-sync:home`

**Important Note**: If you install studip-sync as a snap, you cannot use `~` to reference your home directory in the
config file. If you ignore this note, the files will be synced to `snap/studip-sync/current/...`

**Limitation**: The snap can only write to non-hidden directories in you home directory. If you omit Step 3, it cannot
write to your home directory at all.

### On Arch Linux (AUR)
Install [studip-sync-git](https://aur.archlinux.org/packages/studip-sync-git/) from the AUR.

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
    "base_url": "https://studip.uni-goettingen.de"
}

```

The `files_destination` and `media_destination` option are optional. If you omit one of them, the corresponding feature is disabled. You can also specify both options on the commandline. (Using `-d` implies automatically `--full` if no config is present)
If you omit the `login` or `password`, studip-sync will ask for them interactively.

## Usage

### Full sync instead of incremental sync

studip-sync checks if new files have been edited since the last sync to limit the data which needs to be downloaded on every sync.
If you don't want this to happen and prefer to always download all data, use:
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
# and uses a non-default location for the config file (here: ./config.json)
./studip_sync.py -c ./ -d /path/to/sync/dir

# Reads all parameters from ~/.config/studip-sync/config.json
./studip_sync.py
```

### Automation using a cron job
Run `crontab -e` and add the following lines:
```
# Run at 8:00, 13:00 and 19:00 every day.
0 8,13,19 * * *  /path/to/studip-sync/studip_sync.py
```


## Plugin support

studip-sync supports the feature to load plugins to enable more features.

To enable a plugin run `studip-sync --enable-plugin PLUGIN` and to disable `studip-sync --disable-plugin PLUGIN`.
To reconfigure a plugin run `studip-sync --reconfigure-plugin PLUGIN`.

### Google Tasks API

This plugin can add a new task on each successful media download into a list at Google Tasks. 

To use this plugin you need to have a Google Cloud project with Tasks API enabled.
Download the `credentials.json` from Google Cloud and place it at `.config/studip-sync/google-tasks/credentials.json`.
Then run `studip-sync --enable-plugin google-tasks` and authenticate this plugin over OAuth with your Google account.
Finally, enter the task list id of your specified task list. For this you need to create a task list at Google Tasks first.


## History
* **2020 - today**: [@lenke182](https://github.com/lenke182) has taken over development and maintenance of the project.
* **2015 - 2019**: Developed and maintained by [@woefe](https://github.com/woefe). During that time studip-sync was compatible with Stud.IP deployed at University of Passau.

