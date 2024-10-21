#!/bin/bash

# Define paths
PATHS=("/home/sftpec/ubs/inbox/" "/home/sftpec/ubs/inbox/archive/")

# Output header
echo "Sr. No,Location,Filename,Modified Date,Size (KB),Line Count,Rerun Needed"

# Create an array to store output lines
OUTPUT_LINES=()

# Loop through the defined paths
for PATH in "${PATHS[@]}"
do
    # Find files matching the pattern in the specified directory
    for FILE in "$PATH"transactions_*.txt "$PATH"accounts_*.txt
    do
        # Check if the file exists
        if [ -f "$FILE" ]; then
            # Get the filename, modified date, size in KB, and line count
            FILENAME=$(/usr/bin/basename "$FILE")
            MODIFIED_DATE=$(/usr/bin/stat -c %y "$FILE" | /usr/bin/cut -d'.' -f1)
            SIZE=$(/usr/bin/stat -c %s "$FILE")
            SIZE_KB=$((SIZE / 1024))
            LINE_COUNT=$(/usr/bin/wc -l < "$FILE")

            # Determine the location (Inbox or Archive)
            if [[ "$PATH" == *"inbox/archive"* ]]; then
                LOCATION="Archive"
            else
                LOCATION="Inbox"
            fi

            # Check if the file contains "Error 401 Unauthorized"
            if /usr/bin/grep -q "Error 401 Unauthorized" "$FILE"; then
                RERUN_NEEDED="Yes"
            else
                RERUN_NEEDED="No"
            fi

            # Add the information to the output array
            OUTPUT_LINES+=("$LOCATION,$FILENAME,$MODIFIED_DATE,$SIZE_KB,$LINE_COUNT,$RERUN_NEEDED")
        fi
    done
done

# Display the output with Sr. No
SR_NO=1
for LINE in "${OUTPUT_LINES[@]}"
do
    echo "$SR_NO,$LINE"
    SR_NO=$((SR_NO + 1))
done
