#/bin/sh

# This script will delete B2Share upload files older than n days.
# Usage: ./cleanup-b2share-upload-files.sh [days]

# If days is not supplied as a parameter, the default 21 is used.

# Set default age of files to delete (days)
age=21

if [ ! -z $1 ]; then
    age=$1
fi

upload_folder=CFG_SIMPLESTORE_UPLOAD_FOLDER
# Get the value of $upload_folder from invenio-local.conf first. If not found,
# search invenio.conf
ul=`cat /opt/invenio/etc/invenio-local.conf|grep $upload_folder`

if [ -z "$ul" ]; then
    ul=`cat /opt/invenio/etc/invenio.conf|grep $upload_folder`
fi

if [ -z "$ul" ]; then
    echo "B2Share upload folder definition not found in conf."
    exit
fi

# Extract everything to the right of the '='
a=`echo $ul | sed -n "/$upload_folder *= */ s^^^p" `

if [ ! -d "$a" ]; then
   echo "$a: B2Share upload folder does not exist."
   exit
fi

# find and delete files first
find $a -mtime +$age -type f -exec rm -f {} \;
find $a -mtime +$age -type d -exec rmdir {} \;



 