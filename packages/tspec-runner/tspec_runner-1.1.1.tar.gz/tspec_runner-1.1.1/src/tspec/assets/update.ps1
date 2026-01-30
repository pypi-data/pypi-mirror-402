param(
  [Parameter(Mandatory=$false)]
  [string]$ZipPath,

  [Parameter(Mandatory=$false)]
  [string]$RepoDir = ".",

  [Parameter(Mandatory=$false)]
  [string]$Branch,

  [Parameter(Mandatory=$false)]
  [string]$Tag,

  [Parameter(Mandatory=$false)]
  [string]$CommitMessage
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Fail([string]$msg) {
  Write-Host "ERROR: $msg" -ForegroundColor Red
  exit 1
}

function Get-TspecVersionSortKey([string]$ver) {
  # PEP440-ish: a < b < rc < stable
  if ($ver -match '^(?<rel>\d+(?:\.\d+)*)(?:(?<pre>a|b|rc)(?<pren>\d+))?$') {
    $relParts = $Matches['rel'].Split('.') | ForEach-Object { [int]$_ }

    # normalize to 4 components
    $parts = @($relParts + 0,0,0,0)
    $parts = $parts[0..3]

    $rank = switch ($Matches['pre']) {
      'a'  { 0 }
      'b'  { 1 }
      'rc' { 2 }
      default { 3 } # stable
    }
    $preN = if ($Matches['pren']) { [int]$Matches['pren'] } else { 0 }

    $relKey = ($parts | ForEach-Object { $_.ToString('D6') }) -join '.'
    return "{0}|{1}|{2}" -f $relKey, $rank.ToString('D2'), $preN.ToString('D6')
  }

  # fallback (keeps function total-orderable)
  return "ZZZZZZ|00|000000|$ver"
}

function LatestZipFromDownloads() {
  $dl = Join-Path $HOME "Downloads"
  if (-not (Test-Path $dl)) { return $null }

  $zs = Get-ChildItem -Path $dl -Filter "tspec-runner-*.zip" -File -ErrorAction SilentlyContinue
  if ($null -eq $zs -or $zs.Count -eq 0) { return $null }

  $candidates = foreach ($z in $zs) {
    $v = GuessVersionFromFilename $z.Name
    if ($null -ne $v) {
      [pscustomobject]@{
        FullName  = $z.FullName
        Version   = $v
        SortKey   = Get-TspecVersionSortKey $v
        LastWrite = $z.LastWriteTime
      }
    }
  }

  if ($null -eq $candidates -or $candidates.Count -eq 0) {
    # fallback: newest file
    return ($zs | Sort-Object LastWriteTime -Descending | Select-Object -First 1).FullName
  }

  # pick by version; tie-break by timestamp
  $best = $candidates | Sort-Object SortKey, LastWrite | Select-Object -Last 1
  return $best.FullName
}

function GuessVersionFromFilename([string]$path) {
  $name = [System.IO.Path]::GetFileName($path)

  # accepts: tspec-runner-<version>[-suffix].zip
  if ($name -match '^tspec-runner-(?<rest>.+?)\.zip$') {
    $rest = $Matches['rest']

    # cut only version-like prefix from the rest
    # examples:
    #  - 0.4.0a5
    #  - 0.4.0a5-neko-mcp  -> 0.4.0a5
    #  - 1.2.3             -> 1.2.3
    if ($rest -match '^(?<ver>\d+(?:\.\d+)*(?:(?:a|b|rc)\d+)?)') {
      return $Matches['ver']
    }

    # if it doesn't look like a version, return the raw rest as a last resort
    return $rest
  }

  return $null
}


# Resolve repo dir
$repo = Resolve-Path -Path $RepoDir
Push-Location $repo

try {
  if (-not (Test-Path ".git")) { Fail "not a git repository: $repo (run git init first)" }

  if ([string]::IsNullOrWhiteSpace($ZipPath)) {
    $ZipPath = LatestZipFromDownloads
    if ([string]::IsNullOrWhiteSpace($ZipPath)) { Fail "ZipPath not specified and no tspec-runner-*.zip found in Downloads" }
  }
  $ZipPath = Resolve-Path -Path $ZipPath

  if (-not (Test-Path $ZipPath)) { Fail "zip not found: $ZipPath" }

  $ver = GuessVersionFromFilename $ZipPath
  if ([string]::IsNullOrWhiteSpace($ver)) { $ver = "unknown" }

  if ([string]::IsNullOrWhiteSpace($Tag)) {
    if ($ver -ne "unknown") { $Tag = "v$ver" } else { $Tag = "vupdate" }
  }
  if ([string]::IsNullOrWhiteSpace($Branch)) {
    $Branch = "upgrade/$Tag"
  }
  if ([string]::IsNullOrWhiteSpace($CommitMessage)) {
    $CommitMessage = "upgrade: apply $Tag"
  }

  Write-Host "Repo:   $repo"
  Write-Host "Zip:    $ZipPath"
  Write-Host "Branch: $Branch"
  Write-Host "Tag:    $Tag"

  git switch -c $Branch

  Expand-Archive -Force -Path $ZipPath -DestinationPath "."

  git add -A
  git commit -m $CommitMessage
  git tag $Tag

  Write-Host "Done. Now run:" -ForegroundColor Green
  Write-Host "  uv pip install -e `".\[dev]`""
}
finally {
  Pop-Location
}
