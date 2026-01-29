"""Sample command module - random sampling."""
import logging
import random
import sys

from iterable.helpers.detect import open_iterable

from ..common.iterable import DataWriter
from ..utils import get_file_type, get_option

ITERABLE_OPTIONS_KEYS = ['tagname', 'delimiter', 'encoding', 'start_line', 'page']


def get_iterable_options(options):
    """Extract iterable-specific options from options dictionary."""
    out = {}
    for k in ITERABLE_OPTIONS_KEYS:
        if k in options.keys():
            out[k] = options[k]
    return out


class Sampler:
    """Sampler command handler - random sampling."""
    def __init__(self):
        pass

    def sample(self, fromfile, options=None):
        """Randomly select rows using reservoir sampling algorithm."""
        if options is None:
            options = {}
        logging.debug('Processing %s', fromfile)
        iterableargs = get_iterable_options(options)
        n = get_option(options, 'n')
        percent = get_option(options, 'percent')
        to_file = get_option(options, 'output')

        # Determine sample size
        sample_size = None
        if n:
            sample_size = int(n)
        elif percent:
            # Need to count first to calculate percentage
            count = 0
            iterable = open_iterable(fromfile, mode='r', iterableargs=iterableargs)
            try:
                for _ in iterable:
                    count += 1
            finally:
                iterable.close()
            sample_size = max(1, int(count * float(percent) / 100))

        if sample_size is None or sample_size <= 0:
            logging.error('Sample size (--n or --percent) is required')
            return

        # Reservoir sampling
        iterable = open_iterable(fromfile, mode='r', iterableargs=iterableargs)
        reservoir = []
        count = 0

        try:
            for item in iterable:
                count += 1
                if len(reservoir) < sample_size:
                    # Fill reservoir
                    reservoir.append(item)
                else:
                    # Replace elements with gradually decreasing probability
                    j = random.randint(0, count - 1)
                    if j < sample_size:
                        reservoir[j] = item

                if count % 100000 == 0:
                    logging.debug('sample: processed %d records', count)
        finally:
            iterable.close()

        items = reservoir

        if to_file:
            to_type = get_file_type(to_file)
            if not to_type:
                logging.error('Output file type not supported')
                return
            out = open(to_file, 'w', encoding='utf8')
        else:
            to_type = 'jsonl'
            out = sys.stdout

        # Extract fieldnames from items for CSV output
        fieldnames = None
        if to_type == 'csv' and items:
            if isinstance(items[0], dict):
                fieldnames = list(items[0].keys())

        writer = DataWriter(out, filetype=to_type, fieldnames=fieldnames)
        writer.write_items(items)

        if to_file:
            out.close()

        logging.debug('sample: processed %d records, sampled %d', count, len(items))
