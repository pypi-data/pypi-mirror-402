
"""
import datetime
from tqdm.utils import disp_trim
from tqdm_tag.tqdm_tag import ColoredBar
bar_format = "{l_bar}{bar}{r_bar}"
colors = ['red', 'red', 'red', 'red', 'red', 'red', 'red', 'red', 'red', 'red', 'red', 'red', 'red', 'red', 'red', 'red', 'red', 'red', 'red', 'red', 'red', 'red', 'red']

format_dict = {'n': 1, 'n_fmt': '1', 'total': 2, 'total_fmt': '2', 'elapsed': '00:05', 'elapsed_s': 5.00053858757019, 'ncols': 58, 'desc': '', 'unit': 'it', 'rate': 5.00053858757019, 'rate_fmt': ' 5.00s/it', 'rate_noinv': 0.199978458817555, 'rate_noinv_fmt': ' 0.20it/s', 'rate_inv': 5.00053858757019, 'rate_inv_fmt': ' 5.00s/it', 'postfix': '', 'unit_divisor': 1000, 'colour': 'red', 'remaining': '00:05', 'remaining_s': 5.00053858757019, 'l_bar': ' 50%|', 'r_bar': '| 1/2 [00:05<00:05,  5.00s/it]', 'eta': datetime.datetime(2026, 1, 18, 16, 8, 51, 927938), 'nrows': 33, 'item_status': [0, 0], 'status_to_tag': {0: 'default'}, 'default_status': 0, 'tag_to_color': {'default': 'red'}}


bar = ColoredBar(
    0.4,
    23,
    charset=ColoredBar.UTF, # , ColoredBar.ASCII, else ascii or ColoredBar.UTF
    # colour=colour,
    segment_colours=colors,
    **format_dict,
)
res = bar_format.format(bar=bar, **format_dict)
print(disp_trim(res, 100))
"""