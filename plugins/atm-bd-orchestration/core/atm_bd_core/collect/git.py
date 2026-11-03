"""Read remote branch and ancestry facts through the command port."""


from atm_bd_types import Ancestry, CollectError, FactKind, RemoteBranch

from ._errors import READ_ERRORS


def remote_branches(runner):
    argv = ["git", "ls-remote", "--heads", "origin"]
    try:
        result = runner.run(argv, None)
        if result.code:
            raise ValueError(result.stderr or f"exit {result.code}")
        branches = []
        for line in result.stdout.splitlines():
            head, ref = line.split("\t", 1)
            if len(head) != 40 or any(c not in "0123456789abcdefABCDEF" for c in head) or not ref.startswith("refs/heads/"):
                raise ValueError(f"invalid remote branch: {line}")
            branches.append(RemoteBranch(ref.removeprefix("refs/heads/"), head))
        return branches, None
    except READ_ERRORS as error:
        return None, CollectError(FactKind.REMOTE_BRANCHES, argv, str(error), "Check remote access and retry the command.")


def ancestry(runner, pairs):
    facts = []
    for below, above in pairs:
        argv = ["git", "merge-base", "--is-ancestor", below, above]
        try:
            result = runner.run(argv, None)
            if result.code not in (0, 1):
                raise ValueError(result.stderr or f"exit {result.code}")
            facts.append(Ancestry(below, above, result.code == 0))
        except READ_ERRORS as error:
            return None, CollectError(FactKind.ANCESTRY, argv, str(error), "Fetch the relevant refs and retry the command.")
    return facts, None
