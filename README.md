# Gmail-Cleaner
A command line tool written in Python that works with the Gmail API to help you organize and clean up your Gmail inbox efficiently.

## Introduction
This script helps you clean up and organize your Gmail inbox. Over the years, our inboxes get crammed with different kinds of unwanted content: numerous newsletters we subscribed to but never read, annoying advertisements in all shapes and colors, and so on. My inbox, for example, became full of notifications from various job portals like LinkedIn. As I couldn't find an easy way to clean up my Gmail inbox with the standard Gmail web client, I created my own method for 'spring-cleaning' my inbox.

The tool includes various functions that let you manage emails from specific senders, mark them as spam, or organize them with labels - all with efficient batch processing to handle large mailboxes.

## Prerequisites
To run this script, you'll need:
1. Python (3.6 or newer, tested with Python 3.9)
2. A Google account with Gmail enabled
3. UV for package management (recommended) or pip

### Enabling the Gmail API
You need to enable the Gmail API for this tool to work:
- Create a [Google Cloud Platform project with the API enabled](https://developers.google.com/workspace/guides/create-project)
- Create the [necessary credentials used for OAuth authorization](https://developers.google.com/workspace/guides/create-credentials) 

### Installing dependencies
With UV (recommended):
```bash
uv pip install --system
```

With pip:
```bash
pip install --upgrade google-api-python-client google-auth-httplib2 google-auth-oauthlib
```

## Installation
Clone the repository:

```bash
git clone https://github.com/mxngls/Gmail-Cleaner.git
```

## Usage
1. Copy the JSON file (credentials.json) created when you enabled the Gmail API into the source folder
2. Switch to the src folder and run the script:

```bash
python3 gmailCleaner.py
```

The script offers the following options:
- Show the most common senders
- Move messages from a specific sender to trash (uses batch processing)
- Move messages from a specific sender to the spam folder
- Move all messages from spam to the trash
- Move messages matching a specific label to trash
- Add a label to emails matching a specified sender

## Key Features
- **Batch Processing**: All operations use Gmail's batch API to optimize performance and stay within API rate limits
- **Smart Retry Logic**: Implements exponential backoff with jitter for handling rate limit errors
- **Incremental Updates**: Uses historyId tracking to efficiently process only new changes
- **Real-time Progress**: Shows operation status with detailed progress bars
- **Resource-friendly**: Optimized to work within Gmail API quota limits
- **Modern Dependency Management**: Uses UV for reproducible builds with dependency locking
- **Code Quality**: Implements Ruff for linting and maintaining code standards

## Development
For contributors and developers:
- The project uses UV for dependency management with a `pyproject.toml` file
- Ruff is configured for linting to maintain code quality
- Dependencies are locked in `uv.lock` to ensure reproducible builds

## Known Limitations
- The tool respects Gmail's API rate limits and will automatically retry operations when limits are reached
- For very large mailboxes, operations may take some time due to API quotas

## License
This project is licensed under the terms of the MIT license.
