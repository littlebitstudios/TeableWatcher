# Teable Watcher
A Python script that uses Teable's API to detect changes to tables and sends an email when a new record is added.\
The script runs in a loop, checking for changes at a set interval. When a change is detected, an email is sent to the configured email addresses.

## Running the script
You can run this script standalone or with Docker.
### Standalone usage
Clone the repository and create a folder in the same folder as the script called `data`.\
This will hold the configuration as well as the records cache.

Copy the `example-config.yaml` file to the data folder and rename to `config.yaml`. Create another folder in the data folder called `records-cache` to hold the records cache. The records cache contains JSON files of the records in the tables that have been checked as a reference to compare to the current tables.

If using the script standalone, make sure to have Python installed on your machine and run `pip install -r requirements.txt` to install the required packages, as not all packages required are default in Python.

On newer versions of some Linux distros, it may be necessary to create a virtual environment, which will be indicated by an "externally managed environment" error. Your code editor may be able to assist you in creating virtual environments (I use [Visual Studio Code](https://code.visualstudio.com/)).

It is recommended to use `screen` or `tmux` to run the script in the background. To use `screen`:
```sh
screen -dmS teable-watcher python3 teablewatcher.py
```
If `screen` is not installed, follow instructions for your OS to install it.

### Docker usage
Create a folder somewhere on your machine to hold the container's data. In this folder, create another folder called `data`. This will hold the configuration as well as the records cache.

Copy the `example-compose.yaml` file to the top-level folder and rename to `compose.yaml`. Copy the `example-config.yaml` file to the data folder and rename to `config.yaml`. Create another folder in the data folder called `records-cache` to hold the records cache.

To start the container for the first time, run the `docker compose up -d` command. All Compose commands must be run in the same folder as the `compose.yaml` file.

To stop the container, run the `docker compose down` command.

When restarting the container, it is recommended to pull the latest image to ensure you have the most recent updates. You can do this by running:

```sh
docker compose pull && docker compose up -d
```

This command will pull the latest images and then start the container in the background.

## Configuration

Keys in the `config.yaml` file:
- teable_url: The URL of the Teable instance. This should be https://app.teable.io if you are using the official instance.
- teable_api_key: Your Teable API key. To generate this, sign into Teable and click your name (bottom left) -> Access Token -> Personal access tokens -> Create new token. Make sure to give the token all "read" scopes, and give it permission for the spaces and/or bases you want to watch.
- check_interval: The interval in seconds to check for changes. The example is set to 60 seconds.
- email_sender_settings: The settings for the email sender. This includes the SMTP server, port, username, password, and the sender email address.
   - smtp_server: The SMTP server to use. Usually this will be `smtp.` followed by the domain of the email address.
   - smtp_port: This is usually 465 or 587.
   - smtp_user: The username for the SMTP server. Usually this is the same as the sender email address.
   - smtp_pass: The password for the SMTP server.
   - sender_email: The email address to send the email from.
   - sender_name: The name that emails will appear to be from.
- receivers: A list of email addresses to send the email to.
- watched_bases: Put a Base ID here (starts with `bse`) to watch an entire base.
- ignored_tables: If watching entire bases, you can ignore individual tables by putting the base ID and table ID (starts with `tbl`) here.
- watched_tables: Put a base ID and table ID here to watch a specific table.

## Credits
This project was designed to provide notifications for [Teable](https://teable.io), an open-source GUI database. Find its GitHub repository: [teableio/teable](https://github.com/teableio/teable). Teable is licensed under a combination of MIT and AGPL-3.0 licenses. See their repository for more information.

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for the full license text.