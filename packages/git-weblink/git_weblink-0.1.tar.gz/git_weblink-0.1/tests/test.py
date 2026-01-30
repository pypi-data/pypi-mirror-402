#!/usr/bin/env python3

import unittest
from git_weblink import get_repo_url, get_commit_link, get_line_link


class TestGitWeblink(unittest.TestCase):
    def test_get_repo_url(self):
        self.assertEqual(
            get_repo_url("git@github.com:git/git.git"), "https://github.com/git/git"
        )
        self.assertEqual(
            get_repo_url("https://github.com/git/git.git"), "https://github.com/git/git"
        )
        self.assertEqual(
            get_repo_url("git@github.com:torvalds/linux.git"),
            "https://github.com/torvalds/linux",
        )
        self.assertEqual(
            get_repo_url("git@github.com:torvalds/linux"),
            "https://github.com/torvalds/linux",
        )
        self.assertEqual(
            get_repo_url(
                "https://git.kernel.org/pub/scm/linux/kernel/git/stable/linux.git"
            ),
            # This is not a valid repo link on it's own because of the stripped ".git",
            # but this should be fixed in the host config
            "https://git.kernel.org/pub/scm/linux/kernel/git/stable/linux",
        )
        self.assertEqual(
            get_repo_url(
                "git://git.kernel.org/pub/scm/linux/kernel/git/stable/linux.git"
            ),
            # This is not a valid repo link on it's own because of the stripped ".git",
            # but this should be fixed in the host config
            "https://git.kernel.org/pub/scm/linux/kernel/git/stable/linux",
        )

    def test_get_commit_link(self):
        self.assertEqual(
            get_commit_link(
                "https://github.com",
                "fish-shell/fish-shell",
                "eb336889b7bcb88eb0e1f3dd678ae52275280186",
            ),
            "https://github.com/fish-shell/fish-shell/commit/eb336889b7bcb88eb0e1f3dd678ae52275280186",
        )
        self.assertEqual(
            get_commit_link(
                "https://gitlab.com",
                "gitlab-org/gitlab",
                "089916ca9f8d7a32dffa5ac2996ee3651bbfebe7",
            ),
            "https://gitlab.com/gitlab-org/gitlab/-/commit/089916ca9f8d7a32dffa5ac2996ee3651bbfebe7",
        )
        self.assertEqual(
            get_commit_link(
                "https://git.kernel.org",
                # Not a valid path on it's own, but valid as an internal representation
                "pub/scm/linux/kernel/git/torvalds/linux",
                "3c8ba0d61d04ced9f8d9ff93977995a9e4e96e91",
            ),
            "https://git.kernel.org/pub/scm/linux/kernel/git/torvalds/linux.git/commit/?id=3c8ba0d61d04ced9f8d9ff93977995a9e4e96e91",
        )

    def test_get_line_link(self):
        self.assertEqual(
            get_line_link(
                "https://git.kernel.org",
                # Not a valid path on it's own, but valid as an internal representation
                "pub/scm/linux/kernel/git/torvalds/linux",
                "3c8ba0d61d04ced9f8d9ff93977995a9e4e96e91",
                "include/linux/kernel.h",
                814,
            ),
            "https://git.kernel.org/pub/scm/linux/kernel/git/torvalds/linux.git/tree/include/linux/kernel.h?id=3c8ba0d61d04ced9f8d9ff93977995a9e4e96e91#n814",
        )


if __name__ == "__main__":
    unittest.main()
