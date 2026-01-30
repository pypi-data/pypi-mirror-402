#!/usr/bin/env python3

import argparse
import os
import re
import subprocess
import sys
from urllib.parse import urlparse


def git(*args) -> str:
    return subprocess.check_output(["git", *args]).decode().strip()


class HostConfig:
    def __init__(self, commit: str, file: str, line: str, range: str):
        self.commit = commit
        self.file = file
        self.line = line
        self.range = range

    @classmethod
    def load(cls, url) -> "HostConfig":
        try:
            raw_cfg = git("config", "--get-urlmatch", "weblink", url)
        except subprocess.CalledProcessError as e:
            if e.returncode == 1:
                raise KeyError(f'Missing weblink section for "{url}"')
            else:
                raise

        cfg = {}

        for line in raw_cfg.splitlines():
            key, val = line.split(maxsplit=1)
            # remove "weblink." prefix
            key = key.split(".", maxsplit=1)[1]
            cfg[key] = val

        try:
            return cls(cfg["commit"], cfg["file"], cfg["line"], cfg["range"])
        except KeyError as e:
            raise KeyError(f'No "{e.args[0]}" value set for [weblink "{url}"]')


# Extra configs can be added to ~/.gitconfig without a need to modify this file:
#
#     [weblink "https://your-forge.com"]
#         commit = "{host}/{repo}/commit/{rev}"
#         file = "{host}/{repo}/blob/{rev}/{path}"
#         line = "{host}/{repo}/blob/{rev}/{path}#L{line}"
#         range = "{host}/{repo}/blob/{rev}/{path}#L{range_begin}-L{range_end}"
#
HOST_CONFIGS = {
    "https://github.com": HostConfig(
        commit="{host}/{repo}/commit/{rev}",
        file="{host}/{repo}/blob/{rev}/{path}",
        line="{host}/{repo}/blob/{rev}/{path}#L{line}",
        range="{host}/{repo}/blob/{rev}/{path}#L{range_begin}-L{range_end}",
    ),
    "https://gitlab.com": HostConfig(
        commit="{host}/{repo}/-/commit/{rev}",
        file="{host}/{repo}/-/blob/{rev}/{path}",
        line="{host}/{repo}/-/blob/{rev}/{path}#L{line}",
        range="{host}/{repo}/-/blob/{rev}/{path}#L{range_begin}-L{range_end}",
    ),
    "https://git.kernel.org": HostConfig(
        commit="{host}/{repo}.git/commit/?id={rev}",
        file="{host}/{repo}.git/tree/{path}?id={rev}",
        line="{host}/{repo}.git/tree/{path}?id={rev}#n{line}",
        range="{host}/{repo}.git/tree/{path}?id={rev}#n{range_begin}",
    ),
    "https://codeberg.org": HostConfig(
        commit="{host}/{repo}/commit/{rev}",
        file="{host}/{repo}/src/commit/{rev}/{path}",
        line="{host}/{repo}/src/commit/{rev}/{path}#L{line}",
        range="{host}/{repo}/src/commit/{rev}/{path}#L{range_begin}-L{range_end}",
    ),
    # Generic for Gitiles (JGit repository browser)
    "https://gerrit.googlesource.com": HostConfig(
        commit="{host}/{repo}/+/{rev}",
        file="{host}/{repo}/+/{rev}/{path}",
        line="{host}/{repo}/+/{rev}/{path}#{line}",
        # It seems, multi-line links are not supported:
        # https://issues.gerritcodereview.com/issues/40004573
        range="{host}/{repo}/+/{rev}/{path}#{range_begin}",
    ),
}


# Transformations for remote url -> web repo url.
# The url is normalized to the form: "https://host/repo",
# with trailing ".git" suffix stripped.
REPO_URL_PATTERNS = {
    # https://github.com/git/git.git -> https://github.com/git/git
    r"(https://.*?)(?:\.git)?": r"\1",
    # Note that latter url is not a valid link, but it is valid as an internal representation:
    # git://git.kernel.org/pub/scm/git/git.git -> https://git.kernel.org/pub/scm/git/git
    r"git://(.+)/(.+?)(?:\.git)?": r"https://\1/\2",
    # git@github.com:git/git.git -> https://github.com/git/git
    r"git@(.+):(.+?)(?:\.git)?": r"https://\1/\2",
    # ssh://user@gerrit.googlesource.com:29418/plugins/lfs -> https://gerrit.googlesource.com/plugins/lfs
    r"ssh://(.+?)@(.+?):(\d+)/(.+?)(?:\.git)?": r"https://\2/\4",
}


def get_repo_url(url: str) -> str:
    for pattern, template in REPO_URL_PATTERNS.items():
        match = re.fullmatch(pattern, url)
        if match:
            return match.expand(template)

    raise KeyError(f'No matching pattern for "{url}"')


def get_host_config(host: str) -> HostConfig:
    if host in HOST_CONFIGS:
        return HOST_CONFIGS[host]
    else:
        return HostConfig.load(host)


def get_commit_link(host: str, repo: str, rev: str) -> str:
    cfg = get_host_config(host)
    return cfg.commit.format(host=host, repo=repo, rev=rev)


def get_file_link(host: str, repo: str, rev: str, path: str) -> str:
    cfg = get_host_config(host)
    return cfg.file.format(host=host, repo=repo, rev=rev, path=path)


def get_line_link(host: str, repo: str, rev: str, path: str, line: int) -> str:
    cfg = get_host_config(host)
    return cfg.line.format(host=host, repo=repo, rev=rev, path=path, line=line)


def get_range_link(
    host: str, repo: str, rev: str, path: str, range_begin: int, range_end: int
) -> str:
    cfg = get_host_config(host)
    return cfg.range.format(
        host=host,
        repo=repo,
        rev=rev,
        path=path,
        range_begin=range_begin,
        range_end=range_end,
    )


def repo_relative_path(path):
    """
    Normalize path relative to the current repo:
    - ./foo -> foo
    - /home/user/src/repo/foo -> foo  (when cwd is /home/user/src/repo)
    """
    path = os.path.realpath(path)
    toplevel = git("rev-parse", "--show-toplevel")
    return os.path.relpath(path, start=toplevel)


def nearest_revision(path):
    return git("log", "-1", "--pretty=%H", "--", path)


def main():
    parser = argparse.ArgumentParser(
        description="If you have multiple remotes in your repo, but most often need to generate\n"
        + "links only for one of them, then such remote can be set as a default:\n"
        + "\n"
        + "    git config --local weblink.remote <remote>",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "file",
        nargs="?",
        metavar="FILE[:LINE]",
        help="Path to a file to give a link to."
        + 'Can contain a line or line range after a colon, e.g. "foo/bar:10-20"',
    )

    rev_group = parser.add_mutually_exclusive_group()
    rev_group.add_argument(
        "-r",
        "--rev",
        help="revision (default: HEAD). See gitrevision(7) for details.",
    )
    rev_group.add_argument(
        "-n",
        "--nearest",
        action="store_true",
        help="when revision is not specified, try to use the revision of latest commit that changed the file",
    )

    parser.add_argument(
        "-R",
        "--remote",
        help='remote. If not provided, uses weblink.remote setting from the repo config. Falls back to "origin".',
    )
    args = parser.parse_args()

    if not args.file and not args.rev:
        parser.error("either -r/--rev or FILE must be provided")

    if args.remote:
        remote = args.remote
    else:
        remote = git(
            "config", "--local", "--default", "origin", "--get", "weblink.remote"
        )

    try:
        remote_url = git("remote", "get-url", remote)
    except subprocess.CalledProcessError as e:
        sys.exit(e.returncode)

    if args.rev:
        rev = git("rev-parse", args.rev)
    else:
        rev = git("rev-parse", "HEAD")

    repo_url = get_repo_url(remote_url)
    url = urlparse(repo_url)
    host = f"{url.scheme}://{url.netloc}"
    repo = url.path.lstrip("/")

    if not args.file:
        print(get_commit_link(host, repo, rev))
        sys.exit(0)

    if ":" not in args.file:
        file_in_repo = repo_relative_path(args.file)
        if args.nearest:
            # Use provided path as-is, as git is called from cwd, not from repo root
            rev = nearest_revision(args.file)
        print(get_file_link(host, repo, rev, file_in_repo))
        sys.exit(0)

    file, line = args.file.split(":")
    file_in_repo = repo_relative_path(file)

    if args.nearest:
        # Use provided path as-is, as git is called from cwd, not from repo root
        rev = nearest_revision(file)

    if "-" in line:
        range_begin, range_end = map(int, line.split("-", maxsplit=1))
        print(get_range_link(host, repo, rev, file_in_repo, range_begin, range_end))
    else:
        line = int(line)
        print(get_line_link(host, repo, rev, file_in_repo, line))


if __name__ == "__main__":
    main()
