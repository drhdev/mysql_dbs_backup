# mysql_dbs_backup

`mysql_dbs_backup.py` is a Python script designed to back up multiple MySQL databases sequentially. The script performs the following actions:

- Connects to each specified MySQL database using credentials provided in a `.env` file.
- Backs up each database to a compressed `.zip` file.
- Retains a specified number of backups for each database and deletes older ones based on the retention settings.
- Logs all operations, including successful backups and any errors encountered during the process.

## Features

- Supports backing up multiple databases with different credentials and host settings.
- Configurable backup retention for each database.
- Logs detailed information for each backup operation, including success and error statuses.
- Easy setup using environment variables defined in a `.env` file.

## Installation

To install the `mysql_dbs_backup.py` script from its GitHub repository and set it up on an Ubuntu server, follow the steps below:

### Step 1: Clone the Repository

Open your terminal and navigate to the desired directory (e.g., `/home/user/python`). Clone the repository:

```bash
git clone https://github.com/drhdev/mysql_dbs_backup.git
cd mysql_dbs_backup
```

### Step 2: Set Up a Virtual Environment

Create and activate a virtual environment to isolate the dependencies:

```bash
python3 -m venv venv
source venv/bin/activate
```

### Step 3: Install Dependencies

Install the required Python packages using the `requirements.txt` file:

```bash
pip install -r requirements.txt
```

### Step 4: Configure the `.env` File

Create a `.env` file in the root of the project directory with the following format, specifying the credentials and settings for each database:

```plaintext
# MySQL credentials and settings for each database
DB1_NAME=database1
DB1_USER=user1
DB1_PASS=password1
DB1_HOST=localhost
DB1_MAX_BACKUPS=3

DB2_NAME=database2
DB2_USER=user2
DB2_PASS=password2
DB2_HOST=localhost
DB2_MAX_BACKUPS=5

DB3_NAME=database3
DB3_USER=user3
DB3_PASS=password3
DB3_HOST=127.0.0.1
DB3_MAX_BACKUPS=2

# Add more databases as needed with sequential numbering (DB4, DB5, etc.)
```

### Step 5: Running the Script

To run the backup script manually, activate your virtual environment and execute the script:

```bash
source venv/bin/activate
python mysql_dbs_backup.py -v
```

### Step 6: Automate Backups with a Cron Job (Optional)

To automate the backup process, you can set up a cron job to run the script at a specified interval (e.g., daily at midnight). Open the cron configuration:

```bash
crontab -e
```

Add the following line to schedule the script:

```bash
0 0 * * * /home/user/python/mysql_dbs_backup/venv/bin/python /home/user/python/mysql_dbs_backup/mysql_dbs_backup.py >> /home/user/python_dbs_backup/backup.log 2>&1
```

### Logs

All operations, including successful backups and errors, are logged in the `mysql_dbs_backup.log` file located in the script's directory.

## Troubleshooting

- Ensure that the MySQL credentials in the `.env` file are correct and that the specified MySQL servers are accessible.
- Check the `mysql_dbs_backup.log` file for detailed error messages if backups fail.
- Ensure that `mysqldump` is installed on the server and is accessible in the system’s PATH.

## License

This script is licensed under the GPL v3 license. See the LICENSE file for more details.

## Contributing

Contributions are welcome! Please feel free to open issues or submit pull requests to enhance the script.

---

Feel free to reach out for support or feedback on how this script can be improved further.
