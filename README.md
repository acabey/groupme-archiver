# GroupMe Archiver / Backup Tool

Interface with GroupMe API to download and save chats / groups offline in JSON

# Usage:
    usage: archive.py [-h] -g group -t token [-d token] [--verbose] [--debug]
    
    optional arguments:
      -h, --help            show this help message and exit
      -g group, --group group
                            Group Name
      -t token, --token token
                            GroupMe API Token
      -d directory, --directory directory
                            Base chat directory
      --verbose             Verbose output
      --debug               Debug output

# Examples
    
    python3 archive.py -g "Funky Bunch" -t abcdefg

        Creates the subdirectory "Funky Bunch" relative to the working directory
        Saves "messages.json", profiles, and attachments subdirectories within

    python3 archive.py -g "Funky Bunch" -t abcdefg -d /home/test/

        If not already created, create "/home/test"
        Saves "messages.json", profiles, and attachments subdirectories within

# Issues

    - Individual chats are not at all supported
    - There is an arbitrary limit of 200 in group listing, so if your target group
    is 201st on your list of groups (201st most recently active), it will not be found
        - This can be easily fixed by implementing the API paging system rather
        than working from 1 single page
    - Bulk (multiple groups / chats) archival is not yet supported
