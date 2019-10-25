# studip-sync (Fork)

Download and synchronize files from Stud.IP -- the campus management platform deployed at several German universities.
Note that this fork currently only works at the *University of Göttingen*.

## Installation

1. `git clone https://github.com/lenke182/studip-sync`
2. Install all needed dependencies
3. Run `./studip_sync.py --init` (see Configuration)
4. Schedule a cron job or manually run `./studip_sync.py` to sync your data.

## Configuration

Create a new configuration file. The command below tries to detect all courses that are visible on the "My Courses" Page
in Stud.IP. So make sure that the subcategories you want to include are expanded and the proper semester(s) is/are
selected.

```shell
./studip_sync.py --init
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

### Full sync instead of incremental sync

StudIP-Sync check if new files have been edited since the last sync to limit the data which needs to be downloaded on every sync.
If you don't want this happen and prefer to always download all data, use:
```shell
./studip_sync.py --full
```


### Running studip-sync manually
```shell
# Synchronizes files to /path/to/sync/dir
# and uses a non-default location for the config file
./studip_sync.py -c ./config.json /path/to/sync/dir

# Reads all parameters from ~/.config/studip-sync/config.json
./studip_sync.py
```

### Automation using a cron job
Run `crontab -e` and add the following lines:
```
# Run at 8:00, 13:00 and 19:00 every day.
0 8,13,19 * * *  /path/to/studip-sync/studip_sync.py
```
