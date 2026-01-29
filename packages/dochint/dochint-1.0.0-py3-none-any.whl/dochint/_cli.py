from . import exceptions, processor
import argparse
import os
import sys
prog = os.path.basename(sys.argv[0])

def get_and_validate_args():
    parser = argparse.ArgumentParser(prog=prog, usage=(f'{prog} [-h|--help] '
                                     +'NAME... [OPTIONS...]'))
    parser.add_argument('name', type=str, nargs='+', metavar='NAME',
        help='Input file names.')
    parser.add_argument('--output', '-o', type=str,
        help=('Output file  (if input is single file) or directory (if input '
              +'is multiple files and --output-single-file is not set).'))
    parser.add_argument('--output-single-file', action='store_true',
        help='Output a single file for multi-file input.')
    parser.add_argument('--source-dir', '--src-dir', '-d',
                        type=str, default='.',
        help='Directory to look for input files in.')
    parser.add_argument('--set-numbering', '-n', type=str, nargs=2,
        action='append', metavar=('NAME', 'NUMBERING'), default=[],
        help='Set the chapter numbering (or lettering) for a file.')
    parser.add_argument('--prefix', '-p', type=str, default='\\',
        help='Prefix for macro commands.')
    parser.add_argument('--text-macro', '-t', type=str, nargs=2,
        action='append', metavar=('MACRO', 'TO_TEXT'), default=[],
        help='Define an extra text macro. Can be used multiple times.')

    args = parser.parse_args()

    # make sure input files exist

    for name in args.name:
        fpath = f'{args.source_dir}/{name}'
        if not os.path.isfile(fpath):
            print(f'{prog}: error: file \'{fpath}\' does not exist.',
                  file=sys.stderr)
            exit(-1)

    # make sure output destination is valid

    if args.output is not None:
        if len(args.name) == 1 or args.output_single_file:
            output_dir = os.path.dirname(args.output)
            output_dir = '.' if output_dir=='' else output_dir
            if not os.path.isdir(output_dir):
                print((f'{prog}: error: output directory \'{output_dir}\' '
                       +'does not exist.'), file=sys.stderr)
                exit(-1)
        else: # len(args.name) > 1 and not args.output_single_file
            if not os.path.isdir(args.output):
                print((f'{prog}: error: output directory \'{args.output}\' '
                       +'does not exist.'), file=sys.stderr)
                exit(-1)

            output_normpath = os.path.normpath(args.output)
            source_normpath = os.path.normpath(args.source_dir)
            if output_normpath == source_normpath:
                print((f'{prog}: error: output directory \'{args.output}\' '
                       +'cannot be the same as --source-dir.'),
                      file=sys.stderr)
                exit(-1)
    else: # args.output is None
        if len(args.name) > 1:
            print((f'{prog}: error: cannot output multiple files to STDOUT '
                   +'unless --output-single-file is set.'), file=sys.stderr)
            exit(-1)

    # raise warning if --output-single-file set for single-file input

    if len(args.name) == 1 and args.output_single_file:
        print((f'{prog}: warning: --output-single-file '
               +'is ignored for single-file input.'), file=sys.stderr)

    # make sure numberings/letterings are correct

    if len(args.name) > 1:
        for name, numbering in args.set_numbering:
            if name not in args.name:
                print(f'{prog}: error: \'{name}\' is not an input file name.',
                      file=sys.stderr)
                exit(-1)
            if not (numbering.isnumeric() or numbering.isalpha()):
                print((f'{prog}: error: \'{numbering}\' '
                       +'is not a valid numbering.'), file=sys.stderr)
                exit(-1)
    else:
        if len(args.set_numbering) > 0:
            print((f'{prog}: warning: --set-numbering '
                   +'is ignored for single-file input.'), file=sys.stderr)

    # args have been validated

    return args

def read_with_error(fpath, mode='r'):
    try:
        with open(fpath, mode) as f:
            result = f.read()
    except OSError:
        print(f'{prog}: error: failed to read file \'{fpath}\'.',
              file=sys.stderr)
        exit(-1)
    return result

def write_with_error(fpath, data, mode='w'):
    try:
        with open(fpath, mode) as f:
            f.write(data)
    except OSError:
        print(f'{prog}: error: failed to write file \'{fpath}\'.',
              file=sys.stderr)
        exit(-1)

def extra_macros_dict(macro_list):
    macros = {}
    for macro, text in macro_list:
        macros[macro] = text
    return macros

def process_text_or_texts(multiple, text_or_texts,
                          numberings, prefix, extra_macros, cwd):
    try:
        if multiple:
            processed = processor.process_texts(text_or_texts,
                numberings=numberings, prefix=prefix,
                extra_macros=extra_macros, cwd=cwd)
        else:
            processed = processor.process_text(text_or_texts, prefix=prefix,
                extra_macros=extra_macros, cwd=cwd)
    except exceptions.MacroCommandError as e:
        print(f'{prog}: error: invalid macro \'{prefix}{e.message}\'.',
              file=sys.stderr)
        exit(-1)
    except exceptions.MacroEmptyError:
        print(f'{prog}: error: file ends with macro prefix \'{prefix}\'.',
              file=sys.stderr)
        exit(-1)
    except exceptions.IncompleteMacroError as e:
        print(f'{prog}: error: incomplete macro \'{prefix}{e.message}\'.',
              file=sys.stderr)
        exit(-1)
    except exceptions.LaTeXMathsError as e:
        print(f'{prog}: error: invalid LaTeX maths notation ({e.message}).',
              file=sys.stderr)
        exit(-1)
    except exceptions.CrossrefNotFoundError as e:
        print(f'{prog}: error: {e.message}')
        exit(-1)
    except exceptions.CrossrefExistsError as e:
        print(f'{prog}: error: {e.message}')
        exit(-1)
    except exceptions.CitationError as e:
        print(f'{prog}: error: {e.message}')
        exit(-1)
    except exceptions.BibTeXError as e:
        print(f'{prog}: error: invalid BibTeX input ({e.message}).',
              file=sys.stderr)
        exit(-1)
    except exceptions.FootnoteError as e:
        print((f'{prog}: error: footnote set but never printed '
               +f'({e.message}).'), file=sys.stderr)
        exit(-1)

    return processed

def do_single_file(args):
    name = args.name[0]
    fpath = f'{args.source_dir}/{name}'
    text = read_with_error(fpath)
    extra_macros = extra_macros_dict(args.text_macro)
    processed = process_text_or_texts(False, text,
        None, args.prefix, extra_macros, args.source_dir)

    if args.output is None:
        sys.stdout.write(processed)
        sys.stdout.flush()
    else:
        write_with_error(args.output, processed)

def get_input_texts(args):
    input_texts = []
    for name in args.name:
        fpath = f'{args.source_dir}/{name}'
        text = read_with_error(fpath)
        input_texts.append((name, text))
    return input_texts

def do_multiple_files(args):
    input_texts = get_input_texts(args)
    extra_macros = extra_macros_dict(args.text_macro)
    numberings = {name: numbering for (name, numbering) in args.set_numbering}
    processed_texts = process_text_or_texts(True, input_texts,
        numberings, args.prefix, extra_macros, args.source_dir)

    if args.output is None: # and args.output_single_file
        for name, text in processed_texts.items():
            sys.stdout.write(text)
        sys.stdout.flush()
        return

    if args.output_single_file:
        concatenated_text = ''
        for name in args.name:
            text = processed_texts[name]
            concatenated_text += text
        write_with_error(args.output, concatenated_text)
    else:
        for name, text in processed_texts.items():
            output_fpath = f'{args.output}/{name}'
            write_with_error(output_fpath, text)

def main():
    args = get_and_validate_args()
    if len(args.name) == 1:
        do_single_file(args)
    else:
        do_multiple_files(args)
