import itertools
from argparse import ArgumentParser, Namespace, RawTextHelpFormatter
from inspect import getmembers, isfunction
from json import dump

from json5 import load

from . import pipelines as pipeline_lib

AVAILABLE_PIPELINES = [x[1] for x in
                       getmembers(pipeline_lib, lambda x: isfunction(x) and not x.__name__.startswith('_'))
                       if not x[0].startswith('_')]


def pipeline_doc(func: callable) -> str:
    return func.__doc__.split('\n\n')[0] if func.__doc__ else ''


PIPELINE_DESCRIPTION = '\n\n'.join([
    'Available pipelines:',
    *(f'  {func.__name__}: {pipeline_doc(func)}' for func in AVAILABLE_PIPELINES)
])


def pipeline(name: str) -> callable:
    try:
        return getattr(pipeline_lib, name)
    except AttributeError as e:
        raise ValueError(f'Pipeline {name} not found') from e


DEFAULT_PIPELINES = [pipeline(s) for s in [
    'remove_bookmarks',
    'remove_comments',
    'hide_comments',
    # 'deepen_events',
    'rename_tags',
    'rename_conditionals',
    'move_y',
    'move_tags',
    'shuffle_events',
    'shuffle_conditionals',
    'add_decorations',
    'rename_decoration_ids',
    'shuffle_decorations',
]]


def arg_parse() -> Namespace:
    arg_parser = ArgumentParser(epilog=PIPELINE_DESCRIPTION, formatter_class=RawTextHelpFormatter,
                                usage='python -m rdcompiler [--help|-h] [--pretty|-P] file [--pipeline|-p [pipeline '
                                      '...]]')
    arg_parser.add_argument('file', help="File to compile")
    arg_parser.add_argument('--pipeline', '-p', help='Append a pipeline to run', choices=AVAILABLE_PIPELINES,
                            action='append', metavar='pipeline', type=pipeline, nargs='*')
    arg_parser.add_argument('--pretty', '-P', help='Pretty print the output', action='store_true')
    return arg_parser.parse_args()


def main():
    args = arg_parse()

    file_path: str = args.file

    pipelines = itertools.chain.from_iterable(args.pipeline) if args.pipeline else DEFAULT_PIPELINES

    with open(file_path, 'r', encoding='utf_8_sig') as f:
        level = load(f)

    for p in pipelines:
        p(level)

    compiled_name = file_path.removesuffix('.rdlevel') + '.c.rdlevel'
    with open(compiled_name, 'w', encoding='utf_8') as f:
        dump(level, f, indent=4 if args.pretty else None)


if __name__ == '__main__':
    main()
