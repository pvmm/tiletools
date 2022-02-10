#!/usr/bin/env python3

import sys
import os
import subprocess


def main():
    if len(sys.argv) != 4:
        sys.exit("usage: %s big_image_file tile_dimensions tilemap_prefix" % sys.argv[0])

    cmd = "magick --help > /dev/null"
    if os.system(cmd) != 0:
        sys.exit("Install ImageMagick first or put magick in your path")

    cmd = "identify > /dev/null"
    if os.system(cmd) != 0:
        sys.exit("Install ImageMagick first or put identify in your path")

    if not '/' in sys.argv[3]:
        sys.exit("You must specify a different output directory")

    tile_dir = sys.argv[3][0:sys.argv[3].index('/')]
    if os.path.exists(tile_dir):
        sys.exit("Output directory already exists")

    print(f"Creating subdirectory {tile_dir}...")
    os.mkdir(tile_dir)

    cmd = "magick %s +repage -crop %s %s%%04d.png" % (sys.argv[1], sys.argv[2], sys.argv[3])    
    ec = os.system(cmd)

    count = 0
    chksums = {}
    for filename in os.listdir(tile_dir):
        f = os.path.join(tile_dir, filename)
        chksum = subprocess.check_output(['identify', '-verbose', '-format', '%#', f]).strip()
        if chksum in chksums:
            count += 1
            print(f"Deleting file {f} already accounted for...")
            cmd = f"echo {f} >> {tile_dir}/removed.txt"
            os.system(cmd)
            os.remove(f)
        else:
            chksums[chksum] = True

    print(f"Removed {count} files")

if __name__ == "__main__":
    main()

