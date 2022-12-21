#!/usr/bin/env python3


import sys, math, os
from PIL import Image

from itertools import chain



step = 1
TILE_WIDTH = 8
TILE_HEIGHT = 8


def print_help():
    script = os.path.split(sys.argv[0])[1]
    print('Usage:\n')
    print(f'    {script} input_images -- output_image width step\n');
    print('          input_images: list of input images')
    print('          output_image: result of wrapping around')
    print('                 width: width of the output image')
    print('                  step: next tile offset in pixels (1, 2 or 4)\n')
    sys.exit()


# wrap around the model1 tile into model2
def wraparound(model1, model2, new_images):
    tile = model1

    for i in range(1, TILE_HEIGHT // step):
        new_im = Image.new('RGB', (TILE_WIDTH, TILE_HEIGHT))

        for x in range(TILE_WIDTH):
            for y in range(0, TILE_HEIGHT):
                # Calculate the new y position for the pixel
                new_y = y + i * step

                # wrap around
                tile = model2 if new_y >= TILE_HEIGHT else model1
                new_y %= TILE_HEIGHT

                # Get the pixel at the current position
                pixel = tile.getpixel((x, y))

                # Set the pixel at the new position in the new image
                new_im.putpixel((x, new_y), pixel)

        # Add new tile to the list of new images
        new_images[i].append(new_im)


if '--help' in sys.argv or len(sys.argv) < 4:
    print_help();

# get parameters even if the '--' separator is not specified.
if '--' in sys.argv:
    inputs = sys.argv[1:sys.argv.index('--')]
    try:
        output, new_width, step = sys.argv[sys.argv.index('--') + 1:]
    except ValueError:
        print('** missing parameter **\n')
        print_help();
else:
    try:
        inputs = sys.argv[1:2]
        output, new_width, step = sys.argv[2:4]
    except ValueError:
        print('** missing parameter **\n')
        print_help();

new_width = int(new_width)
step = int(step)

if new_width == 0:
    print('** width should be a number greater than zero **\n')
    print_help();

if new_width % TILE_WIDTH:
    print(f'** width should be divisible by {TILE_WIDTH} **\n')
    print_help();

if not step in [1, 2, 4]:
    print('** step should be 1, 2 or 4 **\n')
    print_help();

new_images = [[] for x in range(TILE_HEIGHT // step)]
wrap_tile = None

# Open the original images
for file in inputs:
    im = Image.open(file)

    # Get the width and height of the image
    width, height = im.size

    for x_ in range(0, width, TILE_WIDTH):
        for y_ in range(height, 0, -TILE_HEIGHT):
            tmp = im.crop((x_, y_ - TILE_HEIGHT, x_ + TILE_WIDTH, y_));
            new_images[0].append(tmp)
            if y_ == height:
                wrap_tile = tmp
            if height > TILE_HEIGHT and y_ - TILE_HEIGHT > 0:
                # Iterate over the number of new tiles to create
                for i in range(step, TILE_HEIGHT // step):
                    new_im = im.crop((x_, y_ - i - TILE_HEIGHT, x_ + TILE_WIDTH, y_ - i))
                    # Add new tile to the list of new images
                    new_images[i].append(new_im)
            else:
                wraparound(tmp, wrap_tile, new_images)

    im.close()

# flatten the results
flatten = list(chain(*new_images))
new_height = math.ceil(len(flatten) * 8 / int(new_width)) * 8

# Create a new image to store the resulting tiles
result_im = Image.new('RGB', (new_width, new_height))

# Paste each new image into the result image
x = y = 0

for new_im in flatten:
    if x == new_width:
        x = 0
        y += TILE_HEIGHT
    result_im.paste(new_im, (x, y))
    x += TILE_WIDTH

# Save the result image
result_im.save(output)
print('New image "%s" created from %i original tiles, resulting in a total of %i tiles in a %ix%i configuration.'
      % (output, len(new_images[0]), len(flatten), new_width, new_height))

