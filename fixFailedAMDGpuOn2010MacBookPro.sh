#!/bin/bash

GRUP_FILE="/boot/grub/grub.cfg"
BACKUP_FILE="grub_backup.cfg"
MODIFIED_FILE="grub_modified.cfg"

# Make a copy for backup
echo "Make a copy of grup.cfg"
cp -v ${GRUP_FILE} ${BACKUP_FILE}

awk '
    BEGIN {
        in_load_video_function = 0;
    }

    $1 ~ /^linux$/ {
       print $0, "i915.lvds_channel_mode=2 i915.modeset=1 i915.lvds_use_ssc=0"
       next
    }

    in_load_video_function == 1 && $1 ~ /^}$/ {
        in_load_video_function = 0
        print "  outb 0x728 1"
        print "  outb 0x710 2"
        print "  outb 0x740 2"
        print "  outb 0x750 0"
    }

    $2 ~ /^load_video$/ {
        in_load_video_function = 1
    }

    {
        print $0
    }
' ${GRUP_FILE} 2>&1 > ${MODIFIED_FILE}

# Show the modification
echo "This is the change..."
diff -u ${GRUP_FILE} ${MODIFIED_FILE}

# Update the grup file
echo "Copy modified grub to boot ..."
cp -v ${MODIFIED_FILE} ${GRUP_FILE}
