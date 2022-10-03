#!/usr/bin/env python3

import argparse
import json
import glob
import os
import re
from textwrap import indent


arg_names = {
    's': 'steps',
    'W': 'width',
    'H': 'height',
    'C': 'cfg_scale',
    'A': 'sampler',
    'F': 'full_precision',
    'S': 'seed',
    'G': 'gfpgan_strength',
    'I': 'init_img',
}

def main():
    """
    Search the dream log file for a given prompt, returning metadata for any
    matching images
    """
    arg_parser = create_argv_parser()
    opt = arg_parser.parse_args()

    if opt.progress_images and not opt.json:
        raise argparse.ArgumentTypeError('--progress-images option requires --json option too')

    if opt.outdir:
        current_outdir = opt.outdir

    # TODO support dream_web_log.txt (but the file format is different)
    log_path = os.path.join(os.path.dirname(__file__), '..', current_outdir, 'dream_log.txt')

    prompt_regex = re.compile(opt.prompt)
    json_matches = []

    with open(log_path) as f:
        while True:
            line = f.readline()
            if not line:
                break

            match = re.search(r'^([^\:]+): "([^"]+)" (.*)', line)
            image = match.group(1)
            prompt = match.group(2)

            if prompt_regex.search(prompt):
                if not opt.json:
                    print(line, end='')
                else:
                    data = {
                        'image': image,
                        'prompt': prompt,
                    }
                    args_raw = match.group(3)
                    args_matches = re.finditer(r'-([a-zA-Z]{1}) ?([^ ]+)', args_raw)

                    for arg_match in args_matches:
                        arg = arg_match.group(1)
                        try:
                            arg_name = arg_names[arg]
                        except KeyError:
                            arg_name = arg
                        value = arg_match.group(2)
                        data[arg_name] = value

                    if opt.progress_images:
                        # Progress images match the same image number
                        image_n = os.path.basename(image).split('.')[0]
                        progress_dir = os.path.join(os.path.dirname(__file__), '..', current_outdir, 'intermediates')
                        progress_images_full = glob.glob(os.path.join(progress_dir, f'{image_n}.*'))
                        progress_images = [os.path.join(current_outdir, 'intermediates', os.path.basename(f)) for f in progress_images_full]
                        data['progress_images'] = progress_images

                    json_matches.append(data)

    if opt.json:
        print(json.dumps(json_matches, indent=2))



def create_argv_parser():
    parser = argparse.ArgumentParser(
        description='Search a stable diffusion dream log file for an image'
    )
    parser.add_argument('prompt', help='Prompt to search for, in regex form')
    parser.add_argument(
        '--json',
        action='store_true',
        help='Output the results in JSON',
    )
    parser.add_argument(
        '--outdir',
        '-o',
        type=str,
        default='outputs/img-samples',
        help='Directory used to save generated images and a log of prompts and seeds. Default: outputs/img-samples',
    )
    parser.add_argument(
        '--progress-images',
        action='store_true',
        help='Include progress images. Requires --json too.',
    )
    return parser


if __name__ == '__main__':
    main()
