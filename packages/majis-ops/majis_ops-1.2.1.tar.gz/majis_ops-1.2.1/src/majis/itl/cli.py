"""ITL CLI module."""

import json
import sys
from argparse import ArgumentParser
from pathlib import Path

from ..misc import read_evf
from .export import save_itl, save_itl_csv, save_itl_eps, save_itl_json, save_itl_xlsm
from .reader import read_itl


def cli(argv: list | None = None):
    """ITL command line interface."""
    parser = ArgumentParser(description='MAJIS ITL toolbox')
    parser.add_argument(
        'itl',
        help='Input ITL filename(s). If multiple files are provided '
        'they will be concatenated.',
        nargs='*',
        metavar='input.[itl|json]',
    )
    parser.add_argument(
        '-o',
        '--output',
        help='Output filename, it could be either ITL, JSON, CSV or XLSM. '
        'If none provided, the results will be displayed (only for ITL, JSON and CSV).',
        metavar='output.[itl|json|csv|xlsm]',
        default='',
    )
    parser.add_argument(
        '-f',
        '--force',
        action='store_true',
        help='Overwrite the output file if already exists.',
    )
    parser.add_argument(
        '-t',
        '--time-ref',
        help='Input events time reference(s). '
        'If multiple values are required use an `events.evf` file.',
        metavar='"YYYY-MM-DDTHH:MM:SS REF_NAME (COUNT = N)"',
    )
    parser.add_argument(
        '-r',
        '--relative-to',
        help='Reference time to be used for relative time output.',
        metavar='"YYYY-MM-DDTHH:MM:SS REF_NAME (COUNT = N)"',
    )
    parser.add_argument(
        '--timeline',
        help='Original timeline to append. '
        'If no explicit `--output` is provided new observations '
        'will be append in this file.',
        metavar='timeline.xlsm',
    )
    parser.add_argument(
        '--header',
        help='ITL custom file header.',
        metavar='"# my-custom-header"',
    )
    parser.add_argument(
        '--overlap',
        action='store_true',
        help='Allow blocks overlap.',
    )
    parser.add_argument(
        '--json',
        action='store_true',
        help='Display the ITL as JSON.',
    )
    parser.add_argument(
        '--csv',
        action='store_true',
        help='Display the ITL as CSV.',
    )
    parser.add_argument(
        '--csv-sep',
        help='CSV separator (default: ";")',
        default=';',
        metavar='separator',
    )

    args, _ = parser.parse_known_args(argv)

    refs = read_evf(args.time_ref)

    events = [read_itl(itl, refs=refs, flat=True) for itl in args.itl]

    if args.output:
        fout = Path(args.output)

        if not args.force and fout.exists():
            raise FileExistsError(args.output)

        match fout.suffix.lower():
            case '.itl':
                kwargs = {'header': args.header}
            case '.json':
                kwargs = {}
            case '.csv':
                kwargs = {'sep': args.csv_sep}
            case '.xlsm':
                kwargs = {'timeline': args.timeline}
            case _:
                raise ValueError(
                    'Only `.itl`|`.json`|`.csv`|`.xlsm` extension are accepted '
                    f'(not `{fout.suffix}`)'
                )

        save_itl(
            fout,
            *events,
            ref=args.relative_to,
            overlap=args.overlap,
            **kwargs,
        )

        sys.stdout.write(f'ITL saved in: {fout}\n')

    elif args.timeline:
        save_itl_xlsm(
            None,
            *events,
            timeline=args.timeline,
            ca_ref=args.relative_to,
            overlap=args.overlap,
        )
        sys.stdout.write(f'ITL appended to: {args.timeline}\n')

    elif args.json:
        sys.stdout.write(
            json.dumps(
                save_itl_json(None, *events, overlap=args.overlap),
                indent=2,
            )
            + '\n'
        )

    elif args.csv:
        sys.stdout.write(
            '\n'.join(save_itl_csv(None, *events, overlap=args.overlap, sep=args.csv_sep))
            + '\n'
        )

    else:
        sys.stdout.write(
            '\n'.join(
                save_itl_eps(
                    None,
                    *events,
                    ref=args.relative_to,
                    overlap=args.overlap,
                    header=args.header,
                )
            )
            + '\n'
        )
