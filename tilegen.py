#!/usr/bin/env python3

import sys
import os
import re
import json
import glob
import hashlib
import math
import subprocess
from subprocess import DEVNULL, STDOUT, check_call
from collections import OrderedDict

from PIL import Image


# debug function
if os.getenv('DEBUG'):
    debug = lambda *x: print(*x)
else:
    debug = lambda *x: None


def main():
    global use_palette

    if len(sys.argv) <= 5 or '--help' in sys.argv:
        sys.exit(f'usage: {sys.argv[0]} big_image_files... -- tile_dimensions tilemap_subdir tileset_dimensions')

    if '--pal' in sys.argv:
        use_palette = True
        del sys.argv[sys.argv.index('--pal')]
    if '--' in sys.argv:
        files = sys.argv[1:sys.argv.index('--')]
        parms = sys.argv[sys.argv.index('--') + 1:]
    else:
        files = sys.argv[1:1+1]
        parms = sys.argv[2:]

    if len(files) == 0:
        sys.exit('No input file specified')

    image_w = image_h = 0
    for i, file in enumerate(files):
        if not os.path.exists(file):
            sys.exit(f'File {file} not found')
        image = Image.open(file)
    else:
        image_w, image_h = image.size
    debug(f'image size: {image_w}x{image_h}')

    if not (tile_dim := re.search(r'(\d+)x(\d+)', parms[0])):
        sys.exit('Wrong tile dimensions, <number>x<number> expected')
    tile_w, tile_h = int(tile_dim.group(1)), int(tile_dim.group(2))
    if min(tile_w, tile_h) <= 0:
        sys.exit('Tile dimensions should be greater than zero')

    if not (tileset_dim := re.search(r'(\d+)x(\d+)', parms[2])):
        sys.exit('Wrong tileset dimensions, <number>x<number> expected')
    tileset_w, tileset_h = int(tileset_dim.group(1)), int(tileset_dim.group(2))
    if min(tileset_w, tileset_h) <= 0:
        sys.exit('Tileset dimensions should be greater than zero')
    debug('tileset size: {tileset_w}x{tileset_h}')

    if not os.path.exists(parms[1]):
        debug(f'Creating subdirectory {parms[1]}...')
        os.mkdir(parms[1])

    debug('Cropping tiles from image...')
    deleted = 0
    chksums = OrderedDict()
    tiles = []
    for path in files:
        prefix = os.path.join(parms[1], os.path.split(os.path.splitext(path)[0])[1])
        debug(f'creating {path} tiles...')

        image = Image.open(path)
        for y in range(0, image.size[1], tile_h):
            for x in range(0, image.size[0], tile_w):
                tile = image.crop((x, y, x + tile_w, y + tile_h))
                chksum = hashlib.md5(tile.tobytes()).hexdigest()
                if chksum in chksums:
                    #debug(f'Deleting tile in "{path}", coordinates ({x}, {y}): identical tile already accounted for')
                    deleted += 1
                else:
                    #debug(f'Storing tile {chksum} in "{path}", coordinates ({x}, {y})')
                    chksums[chksum] = tile
                if path == files[-1]:
                    tiles.append(list(chksums.keys()).index(chksum) + 1)
    debug('%i cropped tiles created.' % len(tiles))
    debug(f'Removed {deleted} files')

    # create tileset
    real_tileset_h = max(math.ceil(len(chksums) / tile_w), tileset_h)
    if real_tileset_h != tileset_h:
        debug('real tileset height differ from the specified parameter')
    result_im = Image.new("RGB", (tileset_w, real_tileset_h))
    x = y = 0
    for index, (key, tile) in enumerate(chksums.items()):
        if (index > 0) and (index % (tileset_w // tile_w) == 0):
            y += tile_h
            x = 0
        #debug('Adding tile %i to output image' % index)
        result_im.paste(tile, (x, y))
        x += tile_w

    # add last arguments to command
    tmp = os.path.join(parms[1], f'tileset{parms[2]}.png')
    result_im.save(tmp)

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
        'width': math.ceil(image_w / tile_w),
        'height': math.ceil(image_h / tile_h),
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
                    'columns': math.ceil(tileset_w / tile_w),
                    'firstgid': 1,
                    'image': f'tileset{parms[2]}.png',
                    'imagewidth': tileset_w,
                    'imageheight': real_tileset_h,
                    'margin': 0,
                    'name': 'default',
                    'spacing': 0,
                    'tilecount': len(chksums),
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
                    'width': math.ceil(image_w / tile_w),
                    'height': math.ceil(image_h / tile_h),
                    'type': 'tilelayer',
                    'visible': True,
                    'x': 0,
                    'y': 0,
                    'data': tiles,
                }
            ],
    }
    with open(os.path.join(parms[1], 'map.json'), 'w') as jsonmap:
        jsonmap.write(json.dumps(tiled))

if __name__ == '__main__':
    main()

