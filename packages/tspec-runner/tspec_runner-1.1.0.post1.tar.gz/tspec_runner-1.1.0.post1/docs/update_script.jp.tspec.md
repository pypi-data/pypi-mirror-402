# 更新取り込み（PowerShell update.ps1）

このファイルは編集可能で、内容は ` ```tspec ` ブロックにあります。

```tspec
manual:
  id: update-script
  title: 更新取り込み（PowerShell update.ps1）
  tags:
  - update
  - powershell
  - git
  summary: update.ps1 を使って zip などからリポジトリを更新する。
  prerequisites:
  - Windows PowerShell / PowerShell 7
  - git が利用可能
  steps:
  - title: 1) update.ps1 を使う（repo直下で）
    body: .\scripts\update.ps1 -ZipPath "$HOME\Downloads\tspec-runner-<version>.zip"
      -RepoDir .
  - title: 2) ZipPath 省略（Downloadsから最新を自動選択）
    body: .\scripts\update.ps1 -RepoDir .
  - title: 3) install版から取り出す（任意）
    body: 'tspec asset list

      tspec asset update.ps1 --to .'
  troubleshooting:
  - title: not a git repository
    body: git init / commit を先に行う。
  references: []
```
