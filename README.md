# studip-sync

Download and synchronize files from Stud.IP -- the campus management platform deployed at several German universities.
Note that studip-sync currently only works at the University of Passau.

## Installation

### Installation on Arch Linux
```
pacaur -S studip-sync-git
```

### Other Distros

Install rsync
```shell
# Ubuntu/Debian
sudo apt install rsync
```

Install PhantomJS. In some cases PhantomJS can be installed from your distribution's repositories. However, on Ubuntu
the version from the repo is not compatible with studip-sync. It is therefore recommended to download and install
PhantomJS manually.
```shell
# Recommended: Download and install manually
# Note: This won't work on 32bit or ARM Architectures.
wget https://bitbucket.org/ariya/phantomjs/downloads/phantomjs-2.1.1-linux-x86_64.tar.bz2
tar xf phantomjs-2.1.1-linux-x86_64.tar.bz2
sudo cp phantomjs-2.1.1-linux-x86_64/bin/phantomjs /usr/bin

# Alternatively: Install from repo (Good luck, this might not work!!)
sudo apt install phantomjs
```

Clone this repository and install studip-sync
```shell
git clone https://github.com/woefe/studip-sync
cd studip-sync

# Install globally
sudo ./setup.py install

# Install for the current user
./setup.py install --user
```

## Configuration

Copy the example configuration file to `~/.config/studip-sync/config.json` and configure your courses, username,
password and synchronization directory.

```shell
cp config.json ~/.config/studip-sync/config.json
```

The `user` and `destination` options are optional, if you specify them on the commandline. To find out the `course_id`
of a course, navigate to the overview page of a course in your browser and copy the `cid` parameter from the URL Bar.
The `sync_only` parameter is optional and allows you to sync only the specified subdirectories. A configuration file
might look like this:

```json
{
    "user": {
        "login": "bob42",
        "password": "password"
    },
    "destination": "~/Documents/Uni",
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
