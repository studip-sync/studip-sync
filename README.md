# studip-sync (Fork)

[![Snap Status](https://build.snapcraft.io/badge/woefe/studip-sync.svg)](https://build.snapcraft.io/user/woefe/studip-sync)

Download and synchronize files from Stud.IP -- the campus management platform deployed at several German universities.
Note that this fork currently only works at the University of Göttingen.

## Installation

### Installation as snap

1. If not yet installed, [install snapd](https://docs.snapcraft.io/core/install)
2. `sudo snap install --edge studip-sync`
3. `sudo snap connect studip-sync:home`

**Important Note**: If you install studip-sync as a snap, you cannot use `~` to reference your home directory in the
config file. If you ignore this note, the files will be synced to `snap/studip-sync/current/...`

**Limitation**: The snap can only write to non-hidden directories in you home directory. If you omit Step 3, it cannot
write to your home directory at all.

### Installation on Arch Linux
Install [studip-sync-git](https://aur.archlinux.org/packages/studip-sync-git/) from the AUR.

## Configuration

Create a new configuration file. The command below tries to detect all courses that are visible on the "My Courses" Page
in Stud.IP. So make sure that the subcategories you want to include are expanded and the proper semester(s) is/are
selected.

```shell
studip-sync --init
```
Next, review the generated configuration file (its path is printed in the last line of above command).

**Hint**: You can create subdirectories (e.g. for lectures and exercises) by using slashes (`/`) in `save_as`.

### Example

```json
{
    "user": {
        "login": "bob42",
        "password": "password"
    },
    "destination": "/home/bob/Documents/Uni",
    "courses": [{
            "course_id": "3dcb76de95b5d8148de3cb72340ade55",
            "save_as": "Computer Networks and Energy Systems/Übung",
            "sync_only": ["daad713cca2f27a0f022c34d84d3c605", "141a4c2ac3bd5b9f8321355192feead8"]
        },
        {
            "course_id": "ccf6c313af0b558d3f3e457d890aff5c",
            "save_as": "Typen und Programmiersprachen/Vorlesung"
        },
        {
            "course_id": "b307cdc24c65dc487be23a22b557a8c5",
            "save_as": "Typen und Programmiersprachen/Übung"
        },
        {
            "course_id": "2081a259c8b2dc1adb4bf2048d3b2a85",
            "save_as": "Wireless Security"
        }
    ]
}
```
The `destination` option is optional, if you specify it on the commandline.
If you omit the `login` or `password`, studip-sync will ask for them interactively.
To find the `course_id` of a course, navigate to the overview page of a course in your browser and copy the `cid` parameter from the URL Bar.
The `sync_only` parameter is optional and allows you to sync only the specified subdirectories.

## Usage
### Running studip-sync manually
```shell
# Synchronizes files to /path/to/sync/dir
# and uses a non-default location for the config file
studip-sync -c ./config.json /path/to/sync/dir

# Reads all parameters from ~/.config/studip-sync/config.json
studip-sync
```

### Automation using a cron job
Run `crontab -e` and add the following lines:
```
# Run at 8:00, 13:00 and 19:00 every day.
0 8,13,19 * * *  studip-sync
```
