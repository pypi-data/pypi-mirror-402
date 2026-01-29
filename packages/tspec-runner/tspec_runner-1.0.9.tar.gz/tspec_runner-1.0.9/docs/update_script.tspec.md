# update.ps1 manual
JP: update.ps1 マニュアル

```tspec
manual:
  id: update-script
  title: "PowerShell update.ps1 usage"
  tags: [update, powershell, git]
  summary: |
    EN: Use update.ps1 to update the repo from a zip or local path.
    JP: update.ps1 を使って zip などからリポジトリを更新する。
  prerequisites:
    - "Windows PowerShell / PowerShell 7"
    - "git"
  steps:
    - title: "1) Use update.ps1 in repo"
      body: |
        .\scripts\update.ps1 -ZipPath "$HOME\Downloads\tspec-runner-<version>.zip" -RepoDir .
    - title: "2) Choose ZipPath"
      body: |
        .\scripts\update.ps1 -RepoDir .
    - title: "3) Refresh install"
      body: |
        tspec asset list
        tspec asset update.ps1 --to .
  troubleshooting:
    - title: "not a git repository"
      body: |
        EN: run git init / commit first.
        JP: git init / commit を先に行う。
```
