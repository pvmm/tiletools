#!/usr/bin/env python3

import sys
import os
import re
import json

import subprocess
from subprocess import DEVNULL, STDOUT, check_call, CalledProcessError

from collections import OrderedDict
from io import StringIO
from PIL import Image


debug = lambda *x: None


def main():
    if len(sys.argv) != 5:
        sys.exit(f'usage: {sys.argv[0]} big_image_file tile_dimensions tilemap_prefix tileset_dimensions')

    try:
        check_call(['convert', '-help'], stdout=DEVNULL, stderr=STDOUT)
    except FileNotFoundError:
        sys.exit('Install ImageMagick or put magick in your path')

    try:
        check_call(['identify', '-help'], stdout=DEVNULL, stderr=STDOUT)
    except FileNotFoundError:
        sys.exit('Install ImageMagick or put identify in your path')

    try:
        check_call(['convert', '-help'], stdout=DEVNULL, stderr=STDOUT)
    except FileNotFoundError:
        sys.exit('Install ImageMagick or put convert in your path')

    if not os.path.exists(sys.argv[1]):
        sys.exit(f'File {sys.argv[1]} not found')
    with Image.open(sys.argv[1]) as image:
        image_w, image_h = image.size

    if not (tile_dim := re.search('(\d+)x(\d+)', sys.argv[2])):
        sys.exit('Wrong tile dimensions, <number>x<number> expected')
    else:
        tile_w, tile_h = int(tile_dim.group(1)), int(tile_dim.group(2))
    if min(tile_w, tile_h) <= 0:
        sys.exit('Tile dimensions should be greater than zero')

    if not os.sep in sys.argv[3]:
        sys.exit('Must specify output directory')
    else:
        tile_dir = sys.argv[3][0:sys.argv[3].index(os.sep)]
        tile_prefix = sys.argv[3][sys.argv[3].index(os.sep) + 1:]

    if os.path.exists(tile_dir):
        sys.exit('Output directory already exists')

    if not (tileset_dim := re.search('(\d+)x(\d+)', sys.argv[4])):
        sys.exit('Wrong tileset dimensions, <number>x<number> expected')
    else:
        tileset_w, tileset_h = int(tileset_dim.group(1)), int(tileset_dim.group(2))
    if min(tileset_w, tileset_h) <= 0:
        sys.exit('Tileset dimensions should be greater than zero')

    debug(f'Creating subdirectory {tile_dir}...')
    os.mkdir(tile_dir)

    debug('Cropping tiles from image...')
    check_call(['convert', sys.argv[1], '+repage', '-crop', sys.argv[2], f'{sys.argv[3]}%04d.png'])

    deleted = 0
    chksums = OrderedDict()
    tiles = []

    with open(os.path.join(tile_dir, 'removed.txt'), 'a+') as output:
        for filename in sorted(os.listdir(tile_dir)):
            tile_num = match.group(0) if (match := re.search("[0-9]+", filename)) else None
            if tile_num is None: continue
            path = os.path.join(tile_dir, filename)
            chksum = subprocess.check_output(['identify', '-verbose', '-format', '%#', path]).strip()
            if chksum in chksums:
                deleted += 1
                debug(f'Deleting file {path}: identical tile already accounted for')
                print(path, file=output)
                os.remove(path)
            else:
                chksums[chksum] = tile_num
            tiles.append(list(chksums.keys()).index(chksum) + 1)

    line = 0
    cmd = ['convert']

    for key, value in chksums.items():
        if line == 0:
            cmd.append('(')
        cmd.append(os.path.join(tile_dir, f'{tile_prefix}{value}.png'))
        line += 1
        if line == tileset_w // tile_w:
            cmd.extend(['+append', ')'])
            line = 0
    if line > 0:
        cmd.extend(['+append', ')'])

    tmp = os.path.join(tile_dir, f'tileset{sys.argv[4]}.png')
    cmd.extend(['-background', 'black', '-append', tmp])
    check_call(cmd)

    tiled = {
        'compression_level': -1,
        'editorsettings':
            {
                'export':
                    {
                        'target': '.'
                    },
            },
        'nextlayerid': 2,
        'nextobjectid': 0,
        'width': image_w // tile_w,
        'height': image_h // tile_h,
        'infinite': False,
        'tilewidth': tile_w,
        'tileheight': tile_h,
        'orientation': 'orthogonal',
        'renderorder': 'right-down',
        'tiledversion': '1.3.1',
        'type': 'map',
        'version': 1.2,
        'tilesets':
            [
                {
                    'columns': tileset_w // tile_w,
                    'firstgid': 1,
                    'image': f'tileset{sys.argv[4]}.png',
                    'imagewidth': tileset_w,
                    'imageheight': tileset_h,
                    'margin': 0,
                    'name': tile_prefix,
                    'spacing': 0,
                    'tilecount': (image_w // tile_w) * (image_h // tile_h) - deleted,
                    'tilewidth': tile_w,
                    'tileheight': tile_h,
                },
            ],
        'layers':
            [
                {
                    'id': 1,
                    'name': 'Map',
                    'opacity': 1,
                    'width': image_w // tile_w,
                    'height': image_h // tile_h,
                    'type': 'tilelayer',
                    'visible': True,
                    'x': 0,
                    'y': 0,
                    'data': tiles,
                }
            ],
    }
    with open(os.path.join(tile_dir, 'map.json'), 'w') as jsonmap:
        jsonmap.write(json.dumps(tiled))
    debug(f'Removed {deleted} files')

if __name__ == '__main__':
    main()

