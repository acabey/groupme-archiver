#!/usr/bin/env python3

import requests
import json
import os
import os.path
import argparse
import sys
from collections import OrderedDict

ATTACHMENTS_DIRECTORY = "attachments/"
PROFILES_DIRECTORY = "profiles/"
MESSAGES_FILE = "messages.json"

VERBOSE = False
DEBUG = False

BASEURL = "https://api.groupme.com/v3"

def main():

    global VERBOSE
    global DEBUG

    parser = argparse.ArgumentParser()

    parser.add_argument('-g', '--group', nargs=1, type=str, metavar='group', help='Group Name', required=True)
    parser.add_argument('-t', '--token', nargs=1, type=str, metavar='token', help='GroupMe API Token', required=True)
    parser.add_argument('-d', '--directory', nargs=1, type=str, metavar='directory', help='Base chat directory')
    #parser.add_argument('-a', '--attachments', nargs=1, type=str, metavar='group', help='Directory to store attachments')
    #parser.add_argument('-p', '--profile', nargs=1, type=str, metavar='group', help='Directory to store profile pictures')
    #parser.add_argument('--no-store-attachments', action='store_true', help='Do not save attachments')
    #parser.add_argument('--no-store-profile-pictures', action='store_true', help='Do not save profile pictures')
    parser.add_argument('--verbose', action='store_true', help='Verbose output')
    parser.add_argument('--debug', action='store_true', help='Debug output')

    args = parser.parse_args()

    # Assign vars
    GROUP_NAME = args.group[0]
    if GROUP_NAME == '':
        eprint('Group Name must be provided')
        sys.exit(1)

    TOKEN = args.token[0]
    if TOKEN == '':
        eprint('Token must be provided')
        sys.exit(1)

    if args.directory:
        OUTPUT_DIRECTORY = args.directory[0]
    else:
        # Base output directory needs trailing slash
        OUTPUT_DIRECTORY = GROUP_NAME + '/'

    VERBOSE = args.verbose
    DEBUG = args.debug

    # Make directories
    directory = os.path.dirname(OUTPUT_DIRECTORY + ATTACHMENTS_DIRECTORY)
    if not os.path.exists(directory):
        os.makedirs(directory)

    directory = os.path.dirname(OUTPUT_DIRECTORY + PROFILES_DIRECTORY)
    if not os.path.exists(directory):
        os.makedirs(directory)

    # Check if overwriting message file
    if os.path.isfile(OUTPUT_DIRECTORY + MESSAGES_FILE):
        # File exists, notify and exit
        eprint('Message file already exists')
        sys.exit(1)

    # Get group ID
    groupid = getGroupID(GROUP_NAME, TOKEN)

    # Failed to find group
    if groupid == None:
        return 1

    # Get messages
    messages = getMessages(groupid, TOKEN)

    # Write messages file
    vprint('Writing to message file: ' + OUTPUT_DIRECTORY + MESSAGES_FILE)
    with open(OUTPUT_DIRECTORY + MESSAGES_FILE, 'w') as outfile:  
        json.dump({'messages' : messages}, outfile, indent=4, separators=(',', ': '))

    # Write attachments
    saveAttachments(messages, OUTPUT_DIRECTORY + ATTACHMENTS_DIRECTORY)

    # Write profile images
    saveProfiles(messages, OUTPUT_DIRECTORY + PROFILES_DIRECTORY)


# Get the numeric group ID for a given group name
# Returns None if not found
# Requests groups page by page until found or end
def getGroupID(groupName, token):

    PER_PAGE = 200
    PAGE = 1

    groupRequestURL = BASEURL + '/groups'
    r = addParameters(groupRequestURL, {
        'token' : token})

    req_params = {'per_page' : PER_PAGE}

    vprint('Requesting groups: ' + r)

    result = requests.get(r, params = req_params)

    jsonresult = result.json()

    # Check if authorized
    if result.status_code == 401:
        eprint('Unauthorized: invalid token')
        return None

    # Check if invalid
    if result.status_code != 200 or result == None:
        eprint('getGroupID response invalid')
        return None

    if jsonresult['response'] == None:
        eprint('getGroupID json result invalid')
        return None

    # Find the group by name
    for group in jsonresult['response']:
        if group['name'] == groupName:
            #print(group['name'] + ' : ' + group['id'])
            vprint('Found group ID: ' + group['id'])
            return group['id']

    eprint('Failed to find group: ' + groupName)
    return None

# Get all messages for a group ID in JSON
def getMessages(groupID, token):

    requestURL = BASEURL + '/groups/' + str(groupID) + '/messages'

    # Make first request
    vprint('Making first request: ' + requestURL)

    r = addParameters(requestURL, {
        'token' : token})

    req_params = {'limit' : 100}

    result = requests.get(r, params = req_params)
    jsonresult = result.json()

    res = jsonresult
    count = 1

    while jsonresult['response'] != None:

        vprint('Making request ' + str(count) + ': ' + requestURL)

        # Add to running results
        messages = jsonresult['response']['messages']
        res['response']['messages'] += messages

        # Get earliest ID
        lastid = messages[-1]['id']
        vprint(str(count) + ' : ' + str(lastid))

        req_params['before_id'] = lastid

        # Make next request
        result = requests.get(r, params = req_params)

        # Check if last message
        if result.status_code == 304 or result == None:
            vprint('End of messages')
            break

        jsonresult = result.json()
        count +=1 

    # De-duplicate
    vprint('Deduplicating messages')
    d = res['response']['messages']
    res['response']['messages'] = [i for n, i in enumerate(d) if i not in d[n + 1:]]
    # Return
    return res

# Save attachments
def saveAttachments(messages, directory):
    vprint('Saving attachments in: ' + directory)

    for message in messages['response']['messages']:
        if message['attachments'] != []:
            for attachment in message['attachments']:
                if attachment['type'] != 'image':
                    vprint("Unsupported type " + attachment['type'] + " on: " + message['id'])
                    continue
                if attachment['type'] == 'image':
                    url = attachment['url']
                    filename = url[url.rfind("/") + 1:]

                    with open(directory + filename, 'wb') as handle:
                        response = requests.get(url, stream=True)
         
                        if not response.ok:
                            eprint(response)
         
                        for block in response.iter_content(1024):
                            if not block:
                                break
                            handle.write(block)

                    vprint('Wrote ' + filename)
    return

# Save attachments
def saveProfiles(messages, directory):
    
    vprint('Saving profiles in: ' + directory)

    avatarlist = []

    for message in messages['response']['messages']:
        temp = message['avatar_url']
        if temp != None:
            if not temp in avatarlist:
                avatarlist.append(temp)

    for avatar in avatarlist:
        url = avatar
        filename = url[url.rfind("/") + 1:]

        vprint(url + " : " + filename)

        with open(directory + filename, 'wb') as handle:
            response = requests.get(url, stream=True)
        
            if not response.ok:
                eprint(response)
        
            for block in response.iter_content(1024):
                if not block:
                    break
                handle.write(block)
        
        vprint('Wrote ' + filename)

    return

# Add a dictionary of key / value pairs
def addParameters(baseurl, paramDict):
    res = baseurl + ''
    for key in paramDict.keys():
        res += '?' + str(key) + '=' + str(paramDict[key])
    return res

# Add an HTTP ? = key value parameter to a request URL
def addParameter(baseurl, paramID, paramValue):
    return baseurl + '?' + paramID + '=' + paramValue

# Print verbose
def vprint(*args, **kwargs):
    global VERBOSE
    if VERBOSE:
        print(*args, file=sys.stdout, **kwargs)

# Print an error
def eprint(*args, **kwargs):
    print(*args, file=sys.stderr, **kwargs)

# Run main
if __name__ == '__main__':
    main()
