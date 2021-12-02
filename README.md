# CAF muxer

## Notes

Only works for ALAC, for a more information see [here](https://z8.re/blog/caf).

## Usage

Information needed from the source file:

- Sample rate
- Bit depth
- Sizes of the individual samples
- mdat chunk as a single bytearray
- Total duration (exact number of raw audio samples)

For examples see `examples.py`.
