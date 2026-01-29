import argparse
import logging
import signal

from . import deploy
from . import mock
from . import report
from . import serve
from . import utils

try:
    from . import aggregator
except ImportError:
    aggregator = None

parser = argparse.ArgumentParser(
    prog='scald',
)
subparser = parser.add_subparsers(
    title='Commands',
    metavar='<command>',
    dest='cmd',
)
subparser.required = True

if aggregator:
    p = utils.append_subparser(subparser, 'aggregate', aggregator.main)
    aggregator._add_parser_args(p)

p = utils.append_subparser(subparser, 'deploy', deploy.main)
deploy._add_parser_args(p)

p = utils.append_subparser(subparser, 'mock', mock.main)
mock._add_parser_args(p)

p = utils.append_subparser(subparser, 'serve', serve.main)
serve._add_parser_args(p)

p = utils.append_subparser(subparser, 'report', report.main)
report._add_parser_args(p)


def main():
    signal.signal(signal.SIGINT, signal.SIG_DFL)
    logging.basicConfig(
        level=10,
        format='%(asctime)s | %(name)s : %(levelname)s : %(message)s',
    )
    args = parser.parse_args()
    args.func(args)

if __name__ == '__main__':
    main()
