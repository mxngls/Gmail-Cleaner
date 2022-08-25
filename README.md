# Gmail-Cleaner
A short command line tool written in python that works with the Gmail-API and helps you organize and clean up your gmail inbox.
## Introduction
This small script will help you clean up and organize your gmail inbox. Over the years our inbox get's crammed with
different kind of junk that no one really wished for: numerous newsletters that we for some reason subscribed to but never read,
annoying advertisments in all shapes and colors, and so on. My inbox for example got really full with notifications from various job portals
like LinkdeIn. As I didn't found an easy way to clean up my Gmail inbox with the standard Gmail web client I just created my own way 
of 'spring-cleaning' my inbox.
There are different functions included that let you delete emails from a specific sender or mark them as spam. Just try it out
and use it for yourself!
## Prerequisites
Basically there are just three things you need to run that script:
1. Python. (I used Python 3.9 but it should work with other version up from 3.6)
2. A Google account with Gmail enabled.
3. The pip package management tool.
### Enabling the Gmail API
In addition to the three prerequisites listed above you need to enable the Gmail API.
To do so just follow the instructions regarding: 
- creating a [Google Cloud Platform project with the API enabled](https://developers.google.com/workspace/guides/create-project).
- creating the [necessary credentials used for involved OAuth authorization](https://developers.google.com/workspace/guides/create-credentials) 
### Installing the google client library:
Finally the last thing to do is installing the Google client library.
To install it just run:

```pip install --upgrade google-api-python-client google-auth-httplib2 google-auth-oauthlib```

## Installation
Just click on the big green button on upper right corner or run:

```git clone https://github.com/mxngls/Gmail-Cleaner.git ```

## Usage
First copy the JSON-file (credentials.json) that is created when you enable the Gmail API into the source folder.
Then switch to the src folder and run the script with:

```python3 gmailCleaner.py```

The script offers the following options:
- Show the most common senders
- Move messages from a specific sender to trash
- Move messages from a specific sender to the spam folder
- Move all messages from spam to the trash
- Move messages matching a specific label to trash
- Add a label to emails matching a specifed sender
- Permanently delete all messages in trash

## Lisence
This project is licensed under the terms of the MIT license.
