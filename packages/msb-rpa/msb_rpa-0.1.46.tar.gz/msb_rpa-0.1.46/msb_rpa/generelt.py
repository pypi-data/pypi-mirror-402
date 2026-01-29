"""
Module for inserting data into ResultTable
"""
import time
import os
import glob
import random
import string
import shutil
import socket
import smtplib
from email.message import EmailMessage
import pyodbc
from msb_rpa.web import close_website_panes


def sql_insert_result(rpa_id: str,
                      executionid: str,
                      resulttype: str,
                      resultinjson: str,
                      conn_str: str,
                      resulttable: str):
    """
    Inserts a row into the given result table using the provided connection.

    Args:
        rpa_id (str): GUID for the RPA process.
        executionid (str): GUID for the execution.
        resulttype (str): Indicates the type of result.
        resultinjson (str): Result in JSON format.
        conn_str (str): Connection string for the database.
        resulttable (str): Table name in the format [schema].[table].

    Note:
        - `rpa_id` and `executionid` should be GUIDs in string format (e.g., str(uuid.uuid4())).
        - If `resulttype` is '1', `resultinjson` is converted to: {"Maskine":"<hostname>"}.
    """

    # Convert result to default format if resulttype is '1'
    if resulttype == '1':
        resultinjson = f'{{"Maskine":"{socket.gethostname()}"}}'

    # Construct the SQL statement
    sql_statement = f'''
    INSERT INTO {resulttable} (RPA_ID, ExecutionID, ResultType, ResultInJson)
    VALUES (?, ?, ?, ?)
    '''

    # Debugging output
    print("SQL Statement:", sql_statement)
    print("Values:", (rpa_id, executionid, resulttype, resultinjson))

    # Execute the insert operation
    with pyodbc.connect(conn_str) as connection:
        with connection.cursor() as cursor:
            cursor.execute(sql_statement, (rpa_id, executionid, resulttype, resultinjson))
            connection.commit()


def use_retry_logic(func, *args, max_retries: int = 3, sleep_time: int = 2, target=None, **kwargs):
    """
    Applies retry logic to a function.

    Args:
        func (callable): The function to retry.
        *args: Positional arguments to pass to the function.
        max_retries (int): Maximum number of retries (0-5). Default is 3.
        sleep_time (int): Time to sleep between retries in seconds. Default is 2.
        target (str, optional): Window title or URL for closing specific windows.
                                If None, all windows will be closed.
        **kwargs: Keyword arguments to pass to the function.
    """

    class BusinessError(Exception):
        """An empty exception used to identify errors caused by breaking business rules"""

    if not 0 <= max_retries <= 5:
        raise ValueError("max_retries must be between 0 and 5")

    last_exception = None
    for attempt in range(max_retries + 1):

        try:
            return func(*args, **kwargs)
        except BusinessError as e:
            print(f"Business error occurred: {e}")
            # Do not retry for business errors
            raise BusinessError(e) from e
        except Exception as e:
            print(f"Process failed on attempt {attempt + 1}: {e}")
            last_exception = e

        if attempt < max_retries:
            print("Retrying...")
            close_website_panes(target=target)
            time.sleep(sleep_time)
        else:
            print("All retries failed.")
            close_website_panes(target=target)
            raise Exception(f"Failed after {max_retries} retries: {last_exception}")


def delete_files_by_type(folder_path, file_extension, filename = None):
    """
    Deletes all files of a specific type from a folder.

    Parameters:
    - folder_path (str): The path to the folder from which files will be deleted.
    - file_extension (str): The file extension to filter files (e.g., 'txt', 'jpg').
    - filename (str, optional): The specific filename to search for. Defaults to None.
    """
    # Create a pattern to match files with the specified extension

    if filename:
        pattern = os.path.join(folder_path, f'{filename}.{file_extension}')
    else:
        pattern = os.path.join(folder_path, f'*.{file_extension}')

    # Use glob to find all files matching the pattern
    files_to_delete = glob.glob(pattern)

    # Iterate over the list of files and delete each one
    for file_path in files_to_delete:
        try:
            os.remove(file_path)
            print(f"Deleted: {file_path}")
        except Exception as e:
            print(f"Error deleting {file_path}: {e}")


def delete_folder(folder_path: str, folder_name: str):
    """
    Deletes a specified folder within a given directory.

    Parameters:
    - folder_path (str): The path to the directory containing the folder to be deleted.
    - folder_name (str): The name of the folder to be deleted.

    Returns:
    - None
    """
    # Define the full path to the folder to be deleted.
    folder_to_delete = os.path.join(folder_path, folder_name)

    # Check if the folder exists, then delete it.
    if os.path.exists(folder_to_delete):
        print(f"The folder '{folder_name}' exists.")
        shutil.rmtree(folder_to_delete)
        print(f"The folder '{folder_name}' has been deleted.")


def generate_password():
    """generer tilfældigt password"""
    # Define character sets
    special_chars = '!@#$%?'
    numbers = string.digits
    capital_letters = string.ascii_uppercase
    small_letters = string.ascii_lowercase

    # Select required characters
    password = [
        random.choice(special_chars) for _ in range(2)
    ] + [
        random.choice(numbers) for _ in range(2)
    ] + [
        random.choice(capital_letters) for _ in range(3)
    ] + [
        random.choice(small_letters) for _ in range(7)
    ]

    # Shuffle the list
    random.shuffle(password)

    # Convert to string
    return ''.join(password)


def basic_email(to_address: str | list[str], emne: str, html: str):
    """Sends an email to confirm a task was created in Fasit

    Args:
        to_address: Email address or list of emails to send the mail to.
        emne: Subject in the mail
        html: <html>body><p>Hej<a href=></a></p></body></html>
    """
    # Create message
    msg = EmailMessage()
    msg['to'] = to_address
    msg['from'] = "robot@friend.dk"
    msg['subject'] = emne

    # Create an HTML message with the exception and screenshot
    html_message = html

    msg.set_content("Please enable HTML to view this message.")
    msg.add_alternative(html_message, subtype='html')

    # Send message
    with smtplib.SMTP("smtp.aarhuskommune.local", 25) as smtp:
        smtp.starttls()
        smtp.send_message(msg)
