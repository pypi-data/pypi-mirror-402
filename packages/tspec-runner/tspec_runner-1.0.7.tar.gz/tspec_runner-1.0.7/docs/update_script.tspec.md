# 更新取り込みスクリプト（PowerShell）

```tspec
manual:
  id: update-script
  title: "更新取り込み（PowerShell update.ps1）"
  tags: [update, powershell, git]
  summary: |
    配布zipを既存リポジトリに取り込む際の事故（上書き、タグ忘れ）を減らすための補助。
    ブランチ作成→zip展開→commit→tag を一括で行う。
  prerequisites:
    - "Windows PowerShell / PowerShell 7"
    - "git が利用可能"
  steps:
    - title: "1) update.ps1 を使う（repo直下で）"
      body: |
        .\scripts\update.ps1 -ZipPath "$HOME\Downloads\tspec-runner-<version>.zip" -RepoDir .
    - title: "2) ZipPath 省略（Downloadsから最新を自動選択）"
      body: |
        .\scripts\update.ps1 -RepoDir .
    - title: "3) install版から取り出す（任意）"
      body: |
        tspec asset list
        tspec asset update.ps1 --to .
  troubleshooting:
    - title: "not a git repository"
      body: |
        先に git init / commit を作ってから利用する。
```

## 設定/手順まとめ
- run: `.\scripts\update.ps1 -ZipPath "<zip>" -RepoDir .`
- optional: `tspec asset update.ps1 --to .` でスクリプト抽出
