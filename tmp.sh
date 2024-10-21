#!/bin/bash

# Define paths
PATHS=("/home/sftpec/ubs/inbox/" "/home/sftpec/ubs/inbox/archive/")

# Output header
echo -e "Filename\tModified Date\tSize (bytes)\tLine Count\tRerun Needed"

# Loop through the defined paths
for PATH in "${PATHS[@]}"
do
    # Find files matching the pattern in the specified directory
    for FILE in "$PATH"transactions_*.txt "$PATH"accounts_*.txt
    do
        # Check if the file exists
        if [ -f "$FILE" ]; then
            # Get the filename, modified date, size, and line count
            FILENAME=$(basename "$FILE")
            MODIFIED_DATE=$(stat -c %y "$FILE" | cut -d'.' -f1)
            SIZE=$(stat -c %s "$FILE")
            LINE_COUNT=$(wc -l < "$FILE")

            # Check if the file contains "Error 401 Unauthorized"
            if grep -q "Error 401 Unauthorized" "$FILE"; then
                RERUN_NEEDED="Yes"
            else
                RERUN_NEEDED="No"
            fi

            # Output the information in tab-separated format
            echo -e "$FILENAME\t$MODIFIED_DATE\t$SIZE\t$LINE_COUNT\t$RERUN_NEEDED"
        fi
    done
done
