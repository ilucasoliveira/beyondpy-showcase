# app/grader/git_lite/help.py (BeyondPy): part of the Git simulator used by the Git lessons.

"""What Git says about a command it does not have: "The most similar command is" (help.c).

Each command gets a distance from the typed one (levenshtein.c, with Git's weights: swapping
two letters 0, changing one 2, adding one 1, removing one 3); a common command that starts
with the typed word gets 0. The closest ones are suggested if they are close enough (less
than 7).
"""

# `git --list-cmds=builtins,main,others` of Git 2.56 for Windows: the builtins, the programs
# of its exec-path and the git-* programs of its PATH.
COMMANDS = """
add am annotate apply archive askpass askyesno backfill bisect blame branch bugreport bundle
cat-file check-attr check-ignore check-mailmap check-ref-format checkout checkout--worker
checkout-index cherry cherry-pick citool clean clone column commit commit-graph commit-tree
config count-objects credential credential-cache credential-cache--daemon
credential-helper-selector credential-manager credential-store credential-wincred daemon
describe diagnose diff diff-files diff-index diff-pairs diff-tree difftool difftool--helper
fast-export fast-import fetch fetch-pack filter-branch fmt-merge-msg for-each-ref
for-each-repo format-patch format-rev fsck fsck-objects fsmonitor--daemon gc
get-tar-commit-id grep gui gui--askpass gui--askyesno gui.tcl hash-object help history hook
http-backend http-fetch http-push imap-send index-pack init init-db interpret-trailers
last-modified lfs log ls-files ls-remote ls-tree mailinfo mailsplit maintenance merge
merge-base merge-file merge-index merge-octopus merge-one-file merge-ours merge-recursive
merge-recursive-ours merge-recursive-theirs merge-resolve merge-subtree merge-tree mergetool
mktag mktree multi-pack-index mv name-rev notes pack-objects pack-redundant pack-refs
patch-id pickaxe prune prune-packed pull push quiltimport range-diff read-tree rebase
receive-pack reflog refs remote remote-ext remote-fd remote-ftp remote-ftps remote-http
remote-https repack replace replay repo request-pull rerere reset restore rev-list rev-parse
revert rm send-email send-pack sh-i18n--envsubst shortlog show show-branch show-index
show-ref sparse-checkout stage stash status stripspace submodule submodule--helper subtree
survey switch symbolic-ref tag unpack-file unpack-objects update update-git-for-windows
update-index update-ref update-server-info upload-archive upload-archive--writer upload-pack
url-parse var verify-commit verify-pack verify-tag version web--browse whatchanged worktree
write-tree
""".split()

# The commands `git help` lists ("These are common Git commands").
COMMON = set(
    """
clone init add mv restore rm bisect diff grep log show status backfill branch commit history
merge rebase reset switch tag fetch pull push
""".split()
)

_SIMILARITY_FLOOR = 7


def levenshtein(first: str, second: str, swap=0, change=2, add=1, remove=3) -> int:
    before = [0] * (len(second) + 1)
    row = [j * add for j in range(len(second) + 1)]
    for i in range(len(first)):
        new = [(i + 1) * remove] + [0] * len(second)
        for j in range(len(second)):
            new[j + 1] = row[j] + change * (first[i] != second[j])
            if (
                i > 0
                and j > 0
                and first[i - 1] == second[j]
                and first[i] == second[j - 1]
                and new[j + 1] > before[j - 1] + swap
            ):
                new[j + 1] = before[j - 1] + swap
            new[j + 1] = min(new[j + 1], row[j + 1] + remove, new[j] + add)
        before, row = row, new
    return row[len(second)]


def unknown(command: str) -> str:
    """What Git prints for `git <command>` when it has no such command."""
    scored = []
    for candidate in sorted(COMMANDS):
        if candidate in COMMON and candidate.startswith(command):
            scored.append((0, candidate))
        else:
            scored.append((levenshtein(command, candidate) + 1, candidate))
    scored.sort()
    count = 0
    while count < len(scored) and scored[count][0] == 0:
        count += 1
    if count >= len(scored):
        best = _SIMILARITY_FLOOR + 1
    else:
        best = scored[count][0]
        count += 1
        while count < len(scored) and scored[count][0] == best:
            count += 1
    out = f"git: '{command}' is not a git command. See 'git --help'.\n"
    if best < _SIMILARITY_FLOOR:
        title = "The most similar command is" if count == 1 else "The most similar commands are"
        out += f"\n{title}\n" + "".join(f"\t{name}\n" for _, name in scored[:count])
    return out
