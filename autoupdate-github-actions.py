from __future__ import annotations

import argparse
import operator
import os.path
import subprocess
from typing import Literal
from typing import Sequence

import yaml
from all_repos import autofix_lib
from all_repos.grep import repos_matching


def if_one_exists(paths: Sequence[str]) -> str | Literal[False]:
    '''Returns the first path that exists, or False if none exist.'''
    for path in paths:
        if os.path.exists(path):
            return path
    return False


def find_repos(config) -> set[str]:
    return (
        repos_matching(config, ('', '--', '.github/workflows/*.yaml'))
        | repos_matching(config, ('', '--', '.github/workflows/*.yml'))
    )


def apply_fix() -> None:
    exists = if_one_exists(
        (
            '.github/dependabot.yml',
            '.github/dependabot.yaml',
        ),
    )
    if exists:
        with open(exists) as f:
            yaml_content = yaml.safe_load(f.read())
    else:
        yaml_content = {
            'version': 2,
            'updates': [],
        }

    exists_file = exists or '.github/dependabot.yml'
    if not any(
        map(
            operator.itemgetter('package-ecosystem'),
            yaml_content['updates'],
        ),
    ):
        yaml_content['updates'].append(
            {
                'package-ecosystem': 'github-actions',
                'directory': '/',
                'schedule': {
                    'interval': 'daily',
                },
            },
        )

    with open(exists_file, 'w') as f:
        f.write(yaml.dump(yaml_content))
    if not exists:
        subprocess.check_output(('git', 'add', '--intent-to-add', exists_file))


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    autofix_lib.add_fixer_args(parser)
    args = parser.parse_args(argv)

    autofix_lib.assert_importable('yaml', install='pyyaml')
    # If a version was necessary uncomment the following line
    # autofix_lib.require_version_gte('pyyaml', 'x.y.z')

    repos, config, commit, autofix_settings = autofix_lib.from_cli(
        args,
        find_repos=find_repos,
        msg='enable dependabot GitHub actions updates',
        branch_name='gha-updates',
    )
    autofix_lib.fix(
        repos, apply_fix=apply_fix, config=config, commit=commit,
        autofix_settings=autofix_settings,
    )
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
