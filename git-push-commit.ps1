<#
.SYNOPSIS
    Stage, commit, and push changes to GitHub in one go.

.DESCRIPTION
    - Verifies we are inside a Git repository.
    - Optionally creates a new branch (if you pass -NewBranch).
    - Stages all modifications (`git add -A`).
    - Commits with a supplied message (or a timestamped default).
    - Pushes the branch to the remote named “origin”.
    - Prints the URL of the latest commit on GitHub.

.PARAMETER Message
    Commit message. If omitted a default “Update <date‑time>” is used.

.PARAMETER NewBranch
    (Optional) Name of a new branch to create before committing.
    If omitted the script works on the current branch.

.PARAMETER Remote
    Remote name to push to. Default = “origin”.

.EXAMPLE
    .\git-push-commit.ps1 -Message "Fix login edge‑cases"
    .\git-push-commit.ps1 -NewBranch "feature/login-fix" -Message "Add login validation"
#>

param(
    [string]$Message,
    [string]$NewBranch,
    [string]$Remote = "origin"
)

function Fail($msg) {
    Write-Error $msg
    exit 1
}

# -------------------------------------------------
# 1️⃣  Ensure we are inside a Git repo
# -------------------------------------------------
if (-not (git rev-parse --is-inside-work-tree 2>$null)) {
    Fail "Current directory is not a Git repository."
}

# -------------------------------------------------
# 2️⃣  (Optional) create & checkout a new branch
# -------------------------------------------------
if ($NewBranch) {
    if (git rev-parse --verify $NewBranch 2>$null) {
        git checkout $NewBranch
    } else {
        git checkout -b $NewBranch
    }
    Write-Host "✅ Switched to branch: $NewBranch"
}

# -------------------------------------------------
# 3️⃣  Determine the branch name we will push
# -------------------------------------------------
$CurrentBranch = git rev-parse --abbrev-ref HEAD
Write-Host "🔀 Working on branch: $CurrentBranch"

# -------------------------------------------------
# 4️⃣  Prepare a commit message if none supplied
# -------------------------------------------------
if (-not $Message) {
    $Message = "Update $(Get-Date -Format 'yyyy‑MM‑dd HH:mm')"
}
Write-Host "📝 Commit message: $Message"

# -------------------------------------------------
# 5️⃣  Stage all changes (including deletions)
# -------------------------------------------------
git add -A
$Changes = git status --short
if (-not $Changes) {
    Write-Host "✅ No changes to commit – nothing to do."
    exit 0
}
Write-Host "📂 Files staged for commit:`n$Changes"

# -------------------------------------------------
# 6️⃣  Create the commit
# -------------------------------------------------
git commit -m "$Message"

# -------------------------------------------------
# 7️⃣  Push to the remote
# -------------------------------------------------
git push -u $Remote $CurrentBranch

# -------------------------------------------------
# 8️⃣  Show the URL of the latest commit on GitHub
# -------------------------------------------------
$RemoteUrl = git remote get-url $Remote
if ($RemoteUrl -match '^git@([^:]+):([^/]+)/(.+)\.git$') {
    $RemoteUrl = "https://$($Matches[1])/$($Matches[2])/$($Matches[3])"
}
$RemoteUrl = $RemoteUrl -replace '\.git$',''
$CommitSha = git rev-parse HEAD
$CommitUrl = "$RemoteUrl/commit/$CommitSha"

Write-Host "`n✅ Push complete! View the commit at:`n$CommitUrl" -ForegroundColor Green
