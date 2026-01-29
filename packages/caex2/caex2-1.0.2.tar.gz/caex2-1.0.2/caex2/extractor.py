#!/usr/bin/env python
# coding: utf-8
import logging
import tempfile
import os
from pathlib import Path

import click
from git import Repo

logging.basicConfig(format='%(message)s', level=logging.INFO)


def get_indented_blocks(episode_lines):
    indented_blocks = []
    block = []
    for line in episode_lines:
        if line.startswith('>'):
            block.append(line.strip())
        elif len(block) > 0:
            if line.startswith('{'):
                block.append(line.strip())
            indented_blocks.append(block)
            block = []
    return indented_blocks

def get_challenge_blocks(episode_lines):
    challenge_blocks = []
    block = []
    for line in episode_lines:
        if line.startswith(':'):
            if line.__contains__('challenge'):
                block.append(line.strip())
            elif line.__contains__('solution'):
                block.append(line.strip())
                challenge_blocks.append(block)
                block = []
        else:
            if len(block) > 0:
                block.append(line.strip())
    stripped_challenges = ['\n'.join(strip_challenge_new(c)) for c in challenge_blocks]
    return stripped_challenges


def strip_challenge_new(block):
    stripped_block = []
    for line in block:
        if not line.startswith(':'):
            line_stripped = line[0:].strip()
            stripped_block.append(line_stripped)
    return stripped_block

def strip_challenge_old(block):
    stripped_block = []
    for line in block:
        if not line.startswith(':'):
            line_stripped = line[0:].strip()
            if not line_stripped.startswith('{:'):
                stripped_block.append(line_stripped)
    return stripped_block


def extract_challenges_from_blocks(indented_blocks):
    challenges = [block[:-1] for block in indented_blocks if 'challenge' in block[-1]]
    stripped_challenges = ['\n'.join(strip_challenge_old(c)) for c in challenges]
    return stripped_challenges


def extract_episode(episode_lines, style='new'):
    if style == 'old':
        indented_blocks = get_indented_blocks(episode_lines)
        challenges = extract_challenges_from_blocks(indented_blocks)
    else:
        challenges = get_challenge_blocks(episode_lines)
    return challenges


def extract_challenges(episode_filepath, output_file, style):
    with open(episode_filepath) as fin:
        episode_lines = fin.readlines()
    challenges = extract_episode(episode_lines, style)

    # Write to output file
    with open(output_file, 'a') as fout:
        fout.write(f'# Episode {episode_filepath.name} \n\n')
        for block in challenges:
            fout.write(block)
            fout.write('\n\n')


def get_episode_paths(repo_dir: Path):
    
    episode_dir_opt = ['_episodes', '_episodes_rmd', 'episodes']
    styles = ['old', 'old', 'new']
    episode_dir = repo_dir / episode_dir_opt[0]
    style = styles[0]
    i = 1
    while os.path.isdir(episode_dir) == False:
        episode_dir = repo_dir / episode_dir_opt[i]
        style = styles[i]
        if i == len(episode_dir_opt):
            raise Exception(f"Episodes folder not found in: ", episode_dir_opt)
        i = i + 1

    episode_paths = sorted([path for path in episode_dir.iterdir() if path.name not in ['.gitkeep']])
    return episode_paths, style

@click.command()
@click.argument('lesson_url')
@click.option('--output', default='exercises-document.md', help='Name of output file to write to')
def main(lesson_url, output):
    """
    Extract exercises from LESSON_URL

    LESSON_URL is a carpentries lesson's Github page
    """
    open(output, 'w').close()  # Wipe output file content
    with Path(tempfile.TemporaryDirectory().name) as temp_dir:
        logging.info(f'Cloning {lesson_url} in temporary directory')
        repo_dir = temp_dir / 'repo'
        Repo.clone_from(lesson_url, repo_dir)
        episode_paths, style = get_episode_paths(repo_dir)
        logging.info(f'Found {len(episode_paths)} possible episodes')
        for episode_path in episode_paths:
            if os.path.isfile(episode_path):
                extract_challenges(episode_path, output, style)
                logging.info(f'Extracted exercises from {episode_path.name}')


if __name__ == '__main__':
    main()
