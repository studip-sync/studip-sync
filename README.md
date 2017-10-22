# studip-sync

## Installation

### Installation on Arch Linux
```
pacaur -S studip-sync-git
```

### Other Distros

Install dependencies
```shell
# Ubuntu/Debian
sudo apt install python3-selenium python3-requests rsync phantomjs
```

Clone this repository and install studip-sync
```shell
git clone https://github.com/woefe/studip-sync
cd studip-sync
sudo python3 setup.py install
```

## Configuration

Copy the example configuration file to `~/.config/studip-sync/config.json` and configure your courses, username,
password and synchronization directory.

```shell
cp config.json ~/.config/studip-sync/config.json
```

The `user` and `destination` options are optional, if you specify them on the commandline. To find out the `course_id`
of a course, navigate to the overview page of a course in your browser and copy the `cid` parameter from the URL Bar. A
configuration file might look like this:
```json
{
    "user": {
        "login": "bob42",
        "password": "password"
    },
    "destination": "~/Documents/Uni",
    "courses": [{
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

## Usage
### Running studip-sync manually
```shell
# Reads login info from stdin and synchronizes files to /path/to/sync/dir
# and uses a non-default location for the config file
studip-sync -i -c ./config.json /path/to/sync/dir

# Reads all parameters from ~/.config/studip-sync/config.json
studip-sync
```

### Automation using a cron job
Run `crontab -e` and add the following lines:
```
# Run at 8:00, 13:00 and 19:00 every day.
0 8,13,19 * * *  studip-sync
```
