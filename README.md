tiletools
=========

Formerly known as `tilegen.py`, `tiletools` is a collection of tile-managing tools grouped together in a single repository. 


tilegen.py
==========

Splits big image into smaller tiles, checks MD5 signature for repeated images, and deletes them if found. After the purge, a new smaller tileset is created according to specified dimensions. **Requires PIL and Python 3.10 to work.** Usage is best explained by example:

``` 
./tilegen.py ./sample/maniac.png -- 16x16 result 256x192
```

will create `result` directory and, inside it, a 256x192 tileset called `tileset256x192.png` composed of n 16x16 tiles that fits inside `sample/maniac.png`. Identical tiles are removed if found, so the actual number of tiles may be smaller than that. A *Tiled*-compatible `map.json` that uses the tileset will also be created.

Now you can specify multiple images in input and this script will generate unique tiles from all of them, but it's the last image used as input that will create a map.json tilemap. These multiple files are separated from the rest of the parameters by a '--'. If no '--' is found, the previous behaviour of a single input file is considered for compatibility.

![Tiled with generated sample map](/docs/tiled.png "Tiled with generated sample map")


map.py
======

[ubox](https://gitlab.com/reidrac/ubox-msx-lib) version of `map.py` is also included, but with the additional option `--transpose` to encode the map in a transposed matrix layout in memory. This is necessary if your game needs to scroll the screen horizontally. `map.py` creates a C or assembly version of `map.json` and `map_conf.json` files.


vwrap.py
========

`vwrap.py` script creates vertically wrapped around copies of the input tiles and stack them side by side in the output file. Wrapping around is useful for pixel-level scrolling in games on the MSX1, like Konami's Pippols. `width` defines the output image width. If the tiles won't fit, `vwrap.py` will wrap to the next 8 lines. If step is 1, the resulting image contains 8 times the amount of input tiles. Step can be 1 (8 times), 2 (4 times) and 4 (2 times). `direction` defines the direction of the vertical update, up or down.


How to create transition tiles between two or more tiles
--------------------------------------------------------

There are two types of tiles in a tileset:

* horizontal aligned tiles will wrap around themselves, not considering transition tiles;
* vertical aligned tiles will be considered as transitional tiles and `vwrap.py` will create transitional tiles between them;

You shouldn't mix vertical and horizontal tiles in the same file.


Usage
-----

```
./vwrap.py <input_files...> -- <direction> <output_file> <width> <step>
```

For instance, considering the two tiles below:

![wrapped tile (input)](/docs/input.png "wrapped tile (input)")

calling:

```
./vwrap.py input.png -- up output.png 136 1
```

will result in:

![wrapped tile (output)](/docs/output.png "wrapped tile (output)")


TODO
----

Some features I may write some day:

* ~~Remove ImageMagick dependency;~~
* ~~Allow multiple input files;~~
* Create separated tilebanks when tilesets are bigger than 256 and use the screen region to decide which tilebank to use;
* Detection of near-identical tiles; 
* Detection of color-swapped tiles;
