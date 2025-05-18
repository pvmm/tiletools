#!/usr/bin/env python3

import sys
import os
import re
import json
import glob
import hashlib
import math
import subprocess
import pprint
import re
from subprocess import DEVNULL, STDOUT, check_call
from collections import OrderedDict

from PIL import Image


# debug function
if os.getenv('DEBUG'):
    debug = lambda *x: print(*x)
else:
    debug = lambda *x: None


def main():
    palette = False

    if len(sys.argv) <= 5 or '--help' in sys.argv:
        sys.exit(f'usage: {sys.argv[0]} ?--has-palette? big_image_files... -- tile_dimensions tilemap_prefix tileset_dimensions')

    if '--has-palette' in sys.argv:
        palette = True
        del sys.argv[sys.argv.index('--has-palette')]
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
    debug(f'-- image size: {image_w}x{image_h}')

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
    debug(f'-- tileset size: {tileset_w}x{tileset_h}')

    if not os.path.exists(parms[1]):
        debug(f'Creating subdirectory {parms[1]}...')
        os.makedirs(parms[1])

    debug('Cropping tiles from image...')
    deleted = 0
    chksums = OrderedDict()
    tiles = []
    for path in files:
        prefix = os.path.join(parms[1], os.path.split(os.path.splitext(path)[0])[1])
        debug(f'Creating {path} tiles...')

        image = Image.open(path)
        # autodetect palette on first line
        if (image.size[1] - 1) / tile_h == image.size[1] // tile_h:
            palimg = image.crop((0, 0, 16, 1))
            image = image.crop((0, 1, image.size[0], image.size[1]))
            #palimg.save('palette.png')
            debug('Extracted palette data')

        for y in range(0, image.size[1], tile_h):
            for x in range(0, image.size[0], tile_w):
                tile = image.crop((x, y, x + tile_w, y + tile_h)).convert("RGB")
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
    debug(f'removed {deleted} files')

    # create tileset
    real_tileset_h = max(math.ceil(len(chksums) / tile_w), tileset_h) + (1 if palette else 0)
    result_image = Image.new("RGB", (tileset_w, real_tileset_h))

    if real_tileset_h != tileset_h + (1 if palette else 0):
        debug('Real tileset height differ from the specified parameter')
    if palette:
        # put palette back on resulting image
        result_image.paste(palimg, (0, 0))

    x = y = 0
    for index, (key, tile) in enumerate(chksums.items()):
        if (index > 0) and (index % (tileset_w // tile_w) == 0):
            y += tile_h
            x = 0
        #debug('Adding tile %i to output image at (%i, %i)' % (index, x, y))
        if y + (1 if palette  else 0) >= real_tileset_h:
            print('WARNING: ** tiles don\'t fit in specified tileset height **', file=sys.stderr)
        result_image.paste(tile, (x, y + (1 if palette else 0)))
        x += tile_w

    # add last arguments to command
    if palette:
        # Add "pal" if image has a palete
        tmp = f'{prefix}-{parms[2]}.pal.png'
    else:
        tmp = f'{prefix}-{parms[2]}.png'
    result_image.save(tmp)

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
                    'image': os.path.split(tmp)[1], # remove directory
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
    with open(f'{prefix}.json', 'w') as jsonmap:
        # convert pretty print output into proper json for Tiled
        json = pprint.pformat(tiled, indent=4, width=80, compact=True)
        json = re.sub(r': True\b', ': true', json, count=0, flags=0)
        json = re.sub(r': False\b', ': false', json, count=0, flags=0)
        jsonmap.write(json.replace("'", '"'))


if __name__ == '__main__':
    main()

