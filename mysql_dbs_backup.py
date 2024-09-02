#!/usr/bin/env python3
# mysql_dbs_backup.py
# Version: 0.1
# Author: drhdev
# License: GPL v3
#
# Description:
# This script performs a backup of specified MySQL databases, compresses each backup into a .zip file,
# manages the retention of a specified number of backups, logs its operations, and writes a status message.

import os
import subprocess
import logging
from logging.handlers import RotatingFileHandler
from datetime import datetime
import sys
import mysql.connector
import zipfile  # For zip compression
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Configuration and Settings
base_dir = os.path.dirname(os.path.abspath(__file__))  # Directory where the script is located
dump_path = os.path.join(base_dir, 'mysql_dbs_backups')  # Directory for dump files

# Backup filename configuration
# Default filename format: YYYYMMDDHHMMSS_DATABASENAME_HOSTNAME.sql.zip
backup_filename_format = "%Y%m%d%H%M%S"

# Set up logging
log_filename = os.path.join(base_dir, 'mysql_dbs_backup.log')  # Updated log file name
logger = logging.getLogger('mysql_dbs_backup.py')  # Updated logger name
logger.setLevel(logging.DEBUG)
handler = RotatingFileHandler(log_filename, maxBytes=5 * 1024 * 1024, backupCount=5)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)

# Check for verbose flag
verbose = '-v' in sys.argv

if verbose:
    # Add console handler if verbose mode is enabled
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

def setup_directories():
    """
    Ensures that the necessary directories are set up.
    """
    try:
        if not os.path.exists(dump_path):
            os.makedirs(dump_path)
            logger.info(f"Directory {dump_path} created successfully.")
    except Exception as e:
        logger.error(f"Error setting up directories: {e}")
        sys.exit(1)

def error_exit(message, backup_file=None):
    """
    Logs the error message, writes a final status to the log, and exits the script.
    """
    logger.error(message)
    write_final_status("failure", message, backup_file)
    sys.exit(1)

def check_mysqldump():
    """
    Checks if mysqldump is available in the system's PATH.
    """
    try:
        result = subprocess.run(['mysqldump', '--version'], capture_output=True, text=True, check=True)
        logger.info(f"mysqldump available: {result.stdout.strip()}")
    except subprocess.CalledProcessError as e:
        error_exit("mysqldump command is not available or failed to execute. Please ensure MySQL is installed and mysqldump is in your PATH.")
    except FileNotFoundError:
        error_exit("mysqldump command not found. Please ensure MySQL is installed and mysqldump is in your PATH.")

def check_database_connection(dbname, dbuser, dbpass, dbhost):
    """
    Checks if the database connection can be established with the provided credentials.
    Logs errors if there are connection or permission issues.
    """
    try:
        connection = mysql.connector.connect(
            host=dbhost,
            user=dbuser,
            password=dbpass,
            database=dbname
        )
        connection.close()
        logger.info(f"Successfully connected to the database '{dbname}' on host '{dbhost}'.")
    except mysql.connector.Error as err:
        error_msg = f"Database connection failed for '{dbname}': {err}"
        if err.errno == 1045:
            error_msg += " (Check your username and password)"
        elif err.errno == 1049:
            error_msg += " (Database does not exist)"
        elif err.errno == 2003:
            error_msg += " (Cannot connect to the database server)"
        write_final_status("failure", error_msg)  # Log failure for each database
        logger.error(error_msg)

def generate_backup_filename(dbname):
    """
    Generates the filename for the backup based on the default format or user setting.
    """
    current_time = datetime.now().strftime(backup_filename_format)
    backup_filename = f"{current_time}_{dbname}.sql.zip"  # Changed to .zip extension
    return os.path.join(dump_path, backup_filename), current_time

def perform_backup(dbname, dbuser, dbpass, dbhost, backup_file):
    """
    Performs the MySQL database backup and compresses the output into a .zip file.
    """
    logger.info(f"Starting backup for database '{dbname}'...")
    try:
        # Create a temporary SQL dump file
        temp_sql_file = backup_file.replace('.zip', '.sql')  # Create a .sql file first

        # Run the mysqldump command to generate the SQL dump
        command = ['mysqldump', '-h', dbhost, '-u', dbuser, f'-p{dbpass}', dbname]
        with open(temp_sql_file, 'wb') as sql_dump:
            result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
            sql_dump.write(result.stdout)

        # Compress the SQL dump into a .zip file
        with zipfile.ZipFile(backup_file, 'w', zipfile.ZIP_DEFLATED) as zipf:
            zipf.write(temp_sql_file, os.path.basename(temp_sql_file))

        # Remove the temporary .sql file after zipping
        os.remove(temp_sql_file)

        logger.info(f"Backup successful: {backup_file}")
        return "success", f"Backup successful: {backup_file}"
    except subprocess.CalledProcessError as e:
        error_msg = f"Backup failed for database '{dbname}'. Error: {e.stderr.decode('utf-8')}"
        logger.error(error_msg)
        write_final_status("failure", error_msg, backup_file)  # Log failure for each database
        return "failure", error_msg
    except PermissionError:
        error_exit(f"Permission denied: Cannot write to {backup_file}. Check your file permissions.", backup_file)
    except Exception as e:
        error_exit(f"Unexpected error during backup process: {e}", backup_file)

def clean_old_backups(dbname, max_backups):
    """
    Cleans up old backups in the specified directory based on the retention count.
    """
    try:
        files = sorted(
            [os.path.join(dump_path, f) for f in os.listdir(dump_path) if f.endswith(".zip") and dbname in f],
            key=os.path.getmtime
        )
        if len(files) > max_backups:
            for file_to_delete in files[:len(files) - max_backups]:
                try:
                    os.remove(file_to_delete)
                    logger.info(f"Deleted old backup: {file_to_delete}")
                except PermissionError:
                    logger.error(f"Permission denied: Cannot delete {file_to_delete}. Check file permissions.")
                except Exception as e:
                    logger.error(f"Error deleting old backup {file_to_delete}: {e}")
        else:
            logger.info("No old backups to delete.")
    except Exception as e:
        logger.error(f"Error cleaning old backups: {e}")

def write_final_status(status, message, backup_file=None):
    """
    Writes the final status of the backup to the log for external monitoring scripts.
    Format: FINAL_STATUS | STATUS | HOSTNAME | TIMESTAMP | DATABASE | FILENAME | MESSAGE
    """
    filename = os.path.basename(backup_file) if backup_file else "N/A"
    final_status_message = f"FINAL_STATUS | {status.upper()} | {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | {filename} | {message}"
    logger.info(final_status_message)

def main():
    """
    Main function that manages the MySQL backup process for multiple databases.
    """
    logger.info("Script started")

    # Set up necessary directories
    setup_directories()

    # Check if mysqldump is available
    check_mysqldump()

    # Get all database configurations from environment variables
    db_index = 1
    while True:
        # Dynamically construct the environment variable names
        dbname = os.getenv(f"DB{db_index}_NAME")
        dbuser = os.getenv(f"DB{db_index}_USER")
        dbpass = os.getenv(f"DB{db_index}_PASS")
        dbhost = os.getenv(f"DB{db_index}_HOST", "localhost")  # Default to localhost if not set
        max_backups = int(os.getenv(f"DB{db_index}_MAX_BACKUPS", 3))  # Default to 3 if not set

        # Break the loop if no more databases are defined
        if not dbname:
            break

        logger.info(f"Processing database: {dbname}")

        # Check database connection
        check_database_connection(dbname, dbuser, dbpass, dbhost)

        # Generate backup filename
        backup_file, backup_time = generate_backup_filename(dbname)

        # Perform MySQL backup
        status, message = perform_backup(dbname, dbuser, dbpass, dbhost, backup_file)

        # Write final status to the log for each database
        write_final_status(status, message, backup_file)

        # Clean up old backups
        logger.info(f"Checking for old backups to delete for database: {dbname}...")
        clean_old_backups(dbname, max_backups)

        # Increment the index to move to the next database
        db_index += 1

    logger.info("Script finished")

if __name__ == "__main__":
    main()
