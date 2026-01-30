#! /usr/bin/env python3

################################################################################
"""Thingy 'git-update' command - update the repo and rebase one more branches
   against their parent branch, if this can be unambiguously determined.

   Author: John Skilleter

   Licence: GPL v3 or later

   TODO: This is a partial solution - to do things properly, we'd have to work
         out the branch tree structure, start at the bottom, pull and/or rebase
         each one working upwards.

         As it is, I'm assuming that we don't have a tree, but a bush, with
         most things branched off a main, master or develop branch, so we pull
         fixed branches first then rebase everything in no particular order.

   TODO: Avoid lots of pulls - should be able to fetch then updated each local branch.
"""
################################################################################

import os
import sys
import re
import argparse
import fnmatch
import logging

from skilleter_modules import git
from skilleter_modules import colour

################################################################################

# Help text

DESCRIPTION = 'Rebase branch(es) against their parent branch, updating both in the process'

EPILOG = \
"""The [update] section of the Git config can be used to specify the default values for the\n
--ignore and --main parameters and both config and command line can use wildcard values,\n
for example "release/*"."""

# Default names for main branches if not specified on command line or git config

DEFAULT_MAIN_BRANCHES = ['main', 'master']

################################################################################

class UpdateFailure(Exception):
    """Exception raised when a branch fails to update"""

    def __init__(self, branchname, errormsg=None) -> None:
        self.branchname = branchname
        self.errormsg = errormsg

        super().__init__()

################################################################################

def parse_command_line():
    """Parse the command line"""

    parser = argparse.ArgumentParser(description=DESCRIPTION, epilog=EPILOG)

    parser.add_argument('--default', '-d', action='store_true',
                        help='Checkout the main or master branch on completion')
    parser.add_argument('--cleanup', '-c', action='store_true',
                        help='After updating a branch, delete it if there are no differences between it and its parent branch')
    parser.add_argument('--all', '-a', action='store_true',
                        help='Update all local branches, not just the current one')
    parser.add_argument('--everything', '-A', action='store_true',
                        help='Update all local branches, not just the current one and ignore the default ignore list specified in the Git configuration')
    parser.add_argument('--parent', '-p', action='store',
                        help='Specify the parent branch, rather than trying to work it out')
    parser.add_argument('--stop', '-s', action='store_true',
                        help='Stop if a rebase problem occurs, instead of skipping the branch')
    parser.add_argument('--ignore', '-i', action='append', default=None,
                        help='List of one or more wildcard branch names not to attempt to update')
    parser.add_argument('--main', '-m', action='append',
                        help='List of one or more wildcard branch names that are considered main branches and should be pulled but not rebased onto anything')
    parser.add_argument('--verbose', '-v', action='store_true',
                        help='Enable verbose output')
    parser.add_argument('--debug', '-D', action='store_true',
                        help='Enable debug output')
    parser.add_argument('--path', '-C', nargs=1, type=str, default=None,
                        help='Run the command in the specified directory')

    return parser.parse_args()

################################################################################

def ensure_clean_worktree():
    """Exit with a message if the working tree is not clean (excluding ignored files)."""

    status = git.status_info(ignored=True, untracked=True)

    for _, state in status.items():
        if state not in ('!!', '  '):
            colour.error('Working tree is not clean - cannot update.')

################################################################################

def validate_configuration(args):
    """Validate the current configuration
    Configures logging
    Checks we are in a working tree
    Updates the ignore and main lists from the configuration"""

    # Enable logging if requested

    if args.debug:
        logging.basicConfig(level=logging.DEBUG)
    elif args.verbose:
        logging.basicConfig(level=logging.INFO)

    # Change directory, if specified

    if args.path:
        os.chdir(args.path[0])

    # Check we are in the right place

    if not git.working_tree():
        colour.error('Not in a git repo')

    # Set the default ignore list if none specified and if not using the '-A' option

    args.ignore = ','.join(args.ignore).split(',') if args.ignore else []

    if not args.everything:
        more_ignore = git.config_get('update', 'ignore')
        if more_ignore:
            args.ignore += more_ignore.split(',')

    logging.info('Ignore list: %s', ', '.join(args.ignore))

    # Set the default main branch name list

    args.main = ','.join(args.main).split(',') if args.main else []

    more_main = git.config_get('update', 'main')

    if more_main:
        args.main += more_main.split(',')
    else:
        args.main += DEFAULT_MAIN_BRANCHES

    logging.info('Main branch list: %s', ', '.join(args.main))

    # Make sure we've got no locally-modified files

    ensure_clean_worktree()

################################################################################

def find_parent_branch(args, branch):
    """Try and determine the parent of a branch
    Returns either the parent branch name or raise UpdateFailure"""

    # Miserable fail if we can't check it out

    try:
        git.checkout(branch)
    except git.GitError as exc:
        raise UpdateFailure(branch, exc.msg)

    # Determine possible parent(s)

    parents, _ = git.parents()

    # Obvious fail if we can't find any possible parents
    # Simple success if we have only ons possible
    # Otherwise, if we have multiple equally-possible parents and one matches a main branch then choose it, otherwise admit failure

    if not parents:
        raise UpdateFailure(branch, f'[RED:WARNING]: Unable to rebase [BLUE:{branch}] branch as unable to determine its parent (no obvious candidates)')

    if len(parents) == 1:
        parent = parents[0]

    else:
        for p in parents:
            if is_main_branch(args, p):
                parent = p
                break
        else:
            raise UpdateFailure(branch, f'[RED:WARNING]: Unable to rebase [BLUE:{branch}] branch as unable to determine its parent (could be any of {", ".join(parents)})')

    return parent

################################################################################

def branch_pull(results, branch, fail=True):
    """Attempt to update a branch, logging any failure except no remote tracking branch
       unless fail is False"""

    colour.write(f'Pulling updates for the [BLUE:{branch}] branch', indent=4)

    # If the branch hasn't already been pulled, try and pull it

    if branch not in results['pulled'] and branch not in results['unchanged']:
        try:
            git.checkout(branch)
            output = git.pull()

            colour.write(output, indent=4)

            lines = output if isinstance(output, list) else [output]

            if any(re.search(r'already up[- ]to[- ]date', line, re.IGNORECASE) for line in lines):
                results['unchanged'].add(branch)
            else:
                results['pulled'].add(branch)

        except git.GitError as exc:
            # Something went wrong with the pull - either there's no remote branch, or the remote
            # branch no longer exists, or the merge failed when it was pulled

            if exc.msg.startswith('There is no tracking information for the current branch.'):
                colour.write(f'[RED:WARNING]: There is no tracking information for the [BLUE:{branch}] branch.', indent=4)
                fail = False

            elif exc.msg.startswith('Your configuration specifies to merge with the ref'):
                colour.write('[RED:WARNING]: The upstream branch no longer exists', indent=4)
                fail = False

            elif 'no such ref was fetched' in exc.msg:
                colour.write(f'[RED:WARNING]: {exc.msg}', indent=4)

            elif 'could not apply' in exc.msg:
                colour.write(f'[RED:WARNING]: Local and upstream versions of [BLUE:{branch}] branch are not in sync.', indent=4)

            else:
                colour.write(f'[RED:WARNING]: Unable to merge upstream changes onto [BLUE:{branch}] branch.', indent=4)

            if git.merging():
                git.abort_merge()
            elif git.rebasing():
                git.abort_rebase()

            if fail:
                results['failed'].add(branch)

            return False

    return True

################################################################################

def branch_rebase(args, results, branch):
    """Attempt to rebase a branch"""

    # Either use the specified parent or try to determine the parent branch

    if args.parent:
        parent = args.parent
    else:
        parent = find_parent_branch(args, branch)

    colour.write(f'[BOLD:Checking if] [BLUE:{branch}] [BOLD:needs to be rebased onto] [BLUE:{parent}]')

    if parent not in results['pulled'] and parent not in results['unchanged']:
        colour.write(f'[BOLD:Updating] [BLUE:{parent}]', indent=4)

        if not branch_pull(results, parent):
            return

    if branch not in results['pulled']:
        if git.iscommit(branch, remote_only=True):
            if not branch_pull(results, branch):
                return
        else:
            results['no-tracking'].add(branch)
            return

    if git.rebase_required(branch, parent):
        colour.write(f'Rebasing [BLUE:{branch}] [BOLD:onto] [BLUE:{parent}]', indent=4)

        git.checkout(branch)
        output, status = git.rebase(parent)

        if status:
            colour.write(f'[RED:WARNING]: Unable to rebase [BLUE:{branch}] onto [BLUE:{parent}]', indent=4)

            if args.verbose:
                colour.write(output)

            results['failed'].add(branch)

            if args.stop:
                raise UpdateFailure(branch)

            git.abort_rebase()
            return

        results['rebased'].add(branch)
    else:
        colour.write(f'[BLUE:{branch}] is already up-to-date on parent branch [BLUE:{parent}]', indent=4)

        results['unchanged'].add(branch)

    if args.cleanup:
        if git.diff_status(branch, parent):
            git.checkout(parent)
            git.delete_branch(branch, force=True)

            results['deleted'].add(branch)

            colour.write(f'Deleted branch [BLUE:{branch}] as it is the same as its parent branch ([BLUE:{parent}])', indent=4)

################################################################################

def is_main_branch(args, branch):
    """Return True if a branch is 'fixed' (master, develop, release, etc.)
       and shouldn't be rebased automatically"""

    if branch.startswith('release/') or branch in ('master', 'main', 'develop'):
        return True

    if args.main:
        for main_match in args.main:
            if fnmatch.fnmatch(branch, main_match):
                return True

    return False

################################################################################

def get_main_branch(args, all_branches):
    """Return the first matching branch from the main branch list that exists,
    or return None if there are no matches."""

    for main_branch in args.main:
        for branch in all_branches:
            if fnmatch.fnmatch(branch, main_branch):
                return branch

    return None

################################################################################

def report_branches(msg, branches):
    """Report a list of branches (if any) with a message"""

    if branches:
        colour.write(newline=True)
        colour.write(msg)

        for branch in branches:
            colour.write(f'[BLUE:{branch}]', indent=4)

################################################################################

def report_results(results):
    """Report what as done"""

    # Remove deleted branches from the list of changed branches

    for entry in ('rebased', 'unchanged', 'pulled', 'failed', 'no-tracking'):
        results[entry] -= results['deleted']

    # Remove unchanged branches from the list of pulled branches

    results['pulled'] -= results['unchanged']

    # Report branch changes

    report_branches('[BOLD:The following branches have been rebased:]', results['rebased'])
    report_branches('[BOLD:The following branches were already up-to-date:]', results['unchanged'])
    report_branches('[BOLD:The following branches have been updated:]', results['pulled'])
    report_branches('[BOLD:The following branches have been deleted:]', results['deleted'])
    report_branches('[RED:WARNING:] [BOLD:The following branches failed to update:]', results['failed'])
    report_branches('[YELLOW:NOTE:] [BOLD:The following branches have been rebased, but no upstream branch exists]', results['no-tracking'])

################################################################################

def main():
    """Entry point"""

    # Handle the command line

    args = parse_command_line()

    validate_configuration(args)

    # Get the current branch

    current_branch = git.branch()

    if not current_branch:
        colour.error('No branch currently checked out - cannot update.')

    colour.write(f'[BOLD:Current branch:] [BLUE:{current_branch}]')
    colour.write('')

    # Switch the current directory in case it vanishes when we switch branches

    os.chdir(git.working_tree())

    # Optionally pull or rebase everything - pull things first, then rebase
    # the rest.

    branches = git.branches() if args.all or args.everything else [current_branch]

    logging.info('Updating %s', ', '.join(branches))

    # Filter out branches that the user wants to ignore

    for ignore in args.ignore:
        for name in branches[:]:
            if fnmatch.fnmatch(name, ignore) and name in branches:
                branches.remove(name)

    if not branches:
        colour.error('No matching branches to update')

    # List of stuff that's been done, to report in the summary

    results = {'deleted': set(), 'pulled': set(), 'failed': set(), 'rebased': set(), 'unchanged': set(), 'no-tracking': set()}

    # Firstly, git pull main branches, add others to the set of branches to rebase

    to_rebase = set()

    for branch in branches:
        if is_main_branch(args, branch):
            colour.write(f'[BOLD:Updating] [BLUE:{branch}]')
            branch_pull(results, branch)
        else:
            to_rebase.add(branch)

    # Now rebase all the branches that want to be rebased

    aborted_branch = None

    for branch in to_rebase:
        try:
            branch_rebase(args, results, branch)
        except UpdateFailure as exc:
            results['failed'].add(exc.branchname)

            if exc.errormsg:
                colour.write(exc.errormsg, indent=4)

            # If we should stop after any rebase issue, abort now, without tidying up

            if args.stop:
                aborted_branch = branch
                break
    else:
        # Return to the original branch if it still exists or a main branch otherwise

        all_branches = git.branches()

        if args.default:
            return_branch = get_main_branch(args, all_branches) or current_branch
        else:
            return_branch = current_branch if current_branch in all_branches else get_main_branch(args, all_branches)

        colour.write('')

        if return_branch:
            colour.write(f'[BOLD]Checking out the [BLUE:{return_branch}] [BOLD:branch]')

            git.checkout(return_branch)
        else:
            if args.default:
                colour.write('[BOLD]Unable to determine main branch to check out!')
            else:
                colour.write(f'[BOLD]Original current branch ([BLUE:{return_branch}]) has been deleted, unable to determine main branch to check out!')

    report_results(results)

    if aborted_branch:
        colour.write('')
        colour.write(f'[RED:WARNING]: Halted update as {aborted_branch} could not be rebased')

        sys.exit(3)

################################################################################

def git_update():
    """Entry point"""

    try:
        main()
    except KeyboardInterrupt:
        sys.exit(1)
    except BrokenPipeError:
        sys.exit(2)

################################################################################

if __name__ == '__main__':
    git_update()
