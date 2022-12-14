#!/usr/bin/env python3

import sys
import os
import re
import json
import glob

import subprocess
from subprocess import DEVNULL, STDOUT, check_call

from collections import OrderedDict


debug = lambda *x: None
#debug = lambda *x: print(*x)


def main():
    if len(sys.argv) <= 5 or '--help' in sys.argv:
        sys.exit(f'usage: {sys.argv[0]} big_image_files... -- tile_dimensions tilemap_subdir tileset_dimensions')

    if '--' in sys.argv:
        files = sys.argv[1:sys.argv.index('--')]
        parms = sys.argv[sys.argv.index('--') + 1:]
    else:
        files = sys.argv[1:1+1]
        parms = sys.argv[2:]

    try:
        check_call(['convert', '-help'], stdout=DEVNULL, stderr=STDOUT)
    except FileNotFoundError:
        sys.exit('Install ImageMagick or put the `convert` executable in your path')

    try:
        check_call(['identify', '-help'], stdout=DEVNULL, stderr=STDOUT)
    except FileNotFoundError:
        sys.exit('Install ImageMagick or put the `identify` executable in your path')

    if len(files) == 0:
        sys.exit('No input file specified')

    image_w = image_h = 0
    for i, file in enumerate(files):
        if not os.path.exists(file):
            sys.exit(f'File {file} not found')
        tmp = subprocess.check_output(['identify', '-format', '%wx%h', file]).decode('utf-8')
        dim = re.search('(\d+)x(\d+)', tmp)
        w, h = int(dim.group(1)), int(dim.group(2))
        if i == len(files) - 1:
            image_w = w
            image_h = h

    if not (tile_dim := re.search('(\d+)x(\d+)', parms[0])):
        sys.exit('Wrong tile dimensions, <number>x<number> expected')
    tile_w, tile_h = int(tile_dim.group(1)), int(tile_dim.group(2))
    if min(tile_w, tile_h) <= 0:
        sys.exit('Tile dimensions should be greater than zero')

    if not (tileset_dim := re.search('(\d+)x(\d+)', parms[2])):
        sys.exit('Wrong tileset dimensions, <number>x<number> expected')
    tileset_w, tileset_h = int(tileset_dim.group(1)), int(tileset_dim.group(2))
    if min(tileset_w, tileset_h) <= 0:
        sys.exit('Tileset dimensions should be greater than zero')

    if not os.path.exists(parms[1]):
        debug(f'Creating subdirectory {parms[1]}...')
        os.mkdir(parms[1])

    debug('Cropping tiles from image...')
    for path in files:
        prefix = os.path.join(parms[1], os.path.split(os.path.splitext(path)[0])[1])
        debug(f'creating {path} tiles...')
        check_call(['convert', path, '+repage', '-crop', parms[0], f'PNG32:{prefix}_%04d_.png'])
    # count cropped files
    count = 0
    for file in os.listdir(parms[1]):
        if os.path.isfile(os.path.join(parms[1], file)):
            count += 1
    debug('%i cropped files created.' % count)

    deleted = 0
    chksums = OrderedDict()
    tiles = []

    with open(os.path.join(parms[1], 'removed.txt'), 'a+') as output:
        for i, source in enumerate(files):
            prefix = os.path.splitext(os.path.split(source)[1])[0]
            for path in sorted(glob.glob(os.path.join(parms[1], f'{prefix}_*_.png'))):
                chksum = subprocess.check_output(['identify', '-verbose', '-format', '%#', path]).strip()
                if chksum in chksums:
                    deleted += 1
                    debug(f'Deleting file {path}: identical tile already accounted for')
                    print(path, file=output)
                    os.remove(path)
                else:
                    chksums[chksum] = path
                # just generate json of last image
                if i == len(files) - 1:
                    tiles.append(list(chksums.keys()).index(chksum) + 1)
    debug(f'Removed {deleted} files')

    # create ImageMagick arguments
    line = 0
    cmd = ['convert', '(']
    for path in chksums.values():
        print('Adding %s file to output image' % path)
        if line == 0:
            cmd.append('(')
        cmd.append(path)
        line += 1
        if line == tileset_w // tile_w:
            cmd.extend(['+append', ')'])
            line = 0
    if line > 0:
        cmd.extend(['+append', ')'])
    cmd.append(')')

    # add last arguments to command
    tmp = os.path.join(parms[1], f'tileset{parms[2]}.png')
    cmd_args = ['-background', 'black', '-append', tmp]
    cmd.extend(cmd_args)
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
                    'image': f'tileset{parms[2]}.png',
                    'imagewidth': tileset_w,
                    'imageheight': tileset_h,
                    'margin': 0,
                    'name': 'tileset',
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
    with open(os.path.join(parms[1], 'map.json'), 'w') as jsonmap:
        jsonmap.write(json.dumps(tiled))

if __name__ == '__main__':
    main()

