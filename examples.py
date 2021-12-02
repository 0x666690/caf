from caf import CAF

# Note:
# The mdat chunk can also be loaded from the
# input file directly by using get_box_data_by_path()
# and specifying "mdat" as the path

# Example data
input_file_name = "input.mp4"
sample_rate = 44100
bit_depth = 16
total_duration = 1206787933
sample_sizes = [
    5756, 5811, 5724, 5757, 5721, 5694, 5629, 5916,
    5682, 5697, 5675, 5937, 5914, 5899, 5723, 5948,
    5799, 5780, 5639, 5810, 5826, 5789, 5550, 5468,
    5371, 5476, 5699, 6783, 6406, 6284, 6149, 5696,
    5808, 5441, 5685, 5765, 6057, 5817, 5999, 6532,
    5784, 5562, 5495, 5936, 5849, 6581, 7660, 7961,
    7745, 7576, 8637, 8983, 7434, 6829, 7058, 8073,
    8050, 7178, 7103, 7683, 8523, 8708, 8712, 8730,
    8874, 8882, 8383, 8016, 8091, 7575, 8164, 7426,
    7186, 7247, 7970, 7773, 7454, 7324, 7216, 7366
]

# Example 1
# Without old magic cookie

c = CAF()
with open("mdat.dat", "rb") as f:
    c.load_mdat_data(bytearray(f.read()))
c.sample_rate = sample_rate
c.bit_depth = 16
c.number_of_valid_frames = total_duration
c.number_of_packets = len(sample_sizes)
c.sample_sizes = sample_sizes
c.create_file()
c.write("output.caf")

# Example 2
# With magic old cookie

c = CAF()
with open("mdat.dat", "rb") as f:
    c.load_mdat_data(bytearray(f.read()))
with open(input_file_name, "rb") as f:
    c.load_input_data(bytearray(f.read()))
c.old_cookie = True
c.load_magic_cookie()
c.bit_depth = 16
c.number_of_valid_frames = total_duration
c.number_of_packets = len(sample_sizes)
c.sample_sizes = sample_sizes
c.create_file()
c.write("output.caf")
