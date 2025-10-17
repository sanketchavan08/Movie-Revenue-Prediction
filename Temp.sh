#!/bin/bash

HOST=
PORT="5022"

# Output header
echo "Sr.No,Location,Filename,Modified Date,Size (KB),Line Count"

# Create an array to hold output lines
OUTPUT_LINES=()

# Loop through each remote directory
for REMOTE_DIR in "${REMOTE_PATHS[@]}"; do
    # Fetch file listing
    OUTPUT=$(sftp -q -oBatchMode=yes -oPort=$PORT ${USER}@${HOST} -b - <<EOF
cd $REMOTE_DIR
ls -l
exit
EOF
)

    # Parse and extract file details
    while read -r line; do
        [[ "$line" != -* ]] && continue  # skip non-file lines

        SIZE=$(echo "$line" | awk '{print $5}')
        MONTH=$(echo "$line" | awk '{print $6}')
        DAY=$(echo "$line" | awk '{print $7}')
        TIME_OR_YEAR=$(echo "$line" | awk '{print $8}')
        FILENAME=$(echo "$line" | awk '{for(i=9;i<=NF;i++) printf $i " "; print ""}' | sed 's/ *$//')

        CURRENT_YEAR=$(date +%Y)
        if [[ "$TIME_OR_YEAR" =~ : ]]; then
            MODIFIED_DATE="$MONTH $DAY $TIME_OR_YEAR $CURRENT_YEAR"
        else
            MODIFIED_DATE="$MONTH $DAY $TIME_OR_YEAR"
        fi

        SIZE_KB=$((SIZE / 1024))

        # Inbox or Archive
        if [[ "$REMOTE_DIR" == *Archive* ]]; then
            LOCATION="Archive"
        else
            LOCATION="Inbox"
        fi

        # Skip fetching line count for performance
        LINE_COUNT="NA"

        # Append to output array
        OUTPUT_LINES+=("$LOCATION,$FILENAME,$MODIFIED_DATE,$SIZE_KB,$LINE_COUNT")

    done <<< "$(echo "$OUTPUT" | grep '^-' )"
done

# ---- Display results ----
SR_NO=1
for LINE in "${OUTPUT_LINES[@]}"; do
    echo "$SR_NO,$LINE"
    ((SR_NO++))
done
