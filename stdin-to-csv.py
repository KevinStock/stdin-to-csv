import re
import csv
import argparse
import os

# Set up command line argument parsing
parser = argparse.ArgumentParser(description='Process a SQL file.')
parser.add_argument('sql_file_path', help='The path to the SQL file')
args = parser.parse_args()

# If no SQL file path is given, alert the user and stop the script
if not args.sql_file_path:
    print("No SQL file path given. Please provide a SQL file path.")
    exit()

sql_file_path = args.sql_file_path

# Check if the file exists
if not os.path.isfile(sql_file_path):
    print(f"The file {sql_file_path} does not exist.")
    exit()

# Check if the file is a SQL file
if not sql_file_path.lower().endswith('.sql'):
    print(f"The file {sql_file_path} is not a SQL file.")
    exit()

# Get the directory of the SQL file
dir_path = os.path.dirname(sql_file_path)

new_sql_file_path = os.path.join(dir_path, sql_file_path.rsplit("/", 1)[-1].rsplit(".", 1)[0] + "-edited.sql")

# Open the SQL file and read its content
with open(sql_file_path, "r") as f:
    sql_content = f.readlines()

new_sql_content = []
copying_data = False
table_name = None
column_names = None
file_counter = 0
data = []

# Buffer to store COPY command
command_buffer = ""

for line in sql_content:
    command_buffer += line
    if not copying_data:
        match = re.search(r"COPY ([\w.]+) \((.*?)\) FROM stdin;", command_buffer, re.DOTALL)
        if match:
            # This is a COPY command, remember table name and column names
            table_name = match.group(1)
            column_names = match.group(2)
            copying_data = True
            command_buffer = ""
    else:
        if line.strip() == "\\.":
            # End of data, write data to CSV file and add \COPY command to new SQL content
            csv_file_name = f"{table_name}_{file_counter}.csv"
            csv_file_path = os.path.join(dir_path, csv_file_name)
            with open(csv_file_path, "w", newline="") as csv_file:
                writer = csv.writer(csv_file)
                for row in data:
                    writer.writerow([value if value != "\\N" else "" for value in row])
            copy_command = f'\\COPY {table_name}({column_names}) FROM \'{csv_file_name}\' WITH (FORMAT csv);\n'
            if len(data) == 0:  # If no data was copied, add a comment after the COPY command
                copy_command += "-- PURPOSEFULLY LEFT EMPTY\n"
            new_sql_content.append(copy_command)
            copying_data = False
            table_name = None
            column_names = None
            data = []
            file_counter += 1
            command_buffer = ""  # Reset the buffer
        else:
            data.append(line.strip().split("\t"))

    # If we are not copying data and the buffer ends with a semicolon, this is a complete command
    if not copying_data and command_buffer.strip().endswith(';'):
        new_sql_content.append(command_buffer)
        command_buffer = ""  # Reset the buffer after appending the command

# Write new SQL content to new SQL file
with open(new_sql_file_path, "w") as f:
    f.writelines(new_sql_content)
