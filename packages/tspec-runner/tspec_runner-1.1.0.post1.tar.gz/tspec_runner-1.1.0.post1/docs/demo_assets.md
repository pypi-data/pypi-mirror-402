# Demo assets update flow
JP: README と PyPI のデモ画像/アニメーション更新手順

This guide keeps README (GitHub) and PyPI demo assets in sync.
JP: README と PyPI のデモ表示を同じ手順で更新するための手順書です。

## 1) Rules
- Store assets under `docs/assets/`
- README.md uses relative paths; README.rst uses raw GitHub URLs
- Verify no personal data appears in captures
- Size guideline: GIF < 500KB, PNG < 300KB
JP:
- 画像は `docs/assets/` に置く
- README.md は相対パス、README.rst は raw GitHub URL を使う
- 画像に個人情報が映らないことを確認
- サイズ目安: GIF は 500KB 以内、PNG は 300KB 以内

## 2) Unity MCP demo update
Prereqs:
- Unity Editor running
- MCP for Unity HTTP server running (e.g., `http://localhost:8080/mcp`)
JP:
- Unity Editor 起動
- MCP for Unity の HTTP サーバ起動（例: `http://localhost:8080/mcp`）

Steps:
1. Run MCP actions (create objects / apply materials / create prefabs)
2. Capture PNGs via `manage_scene(action="screenshot")`
3. Copy PNGs into `docs/assets/`
4. Generate GIF with Pillow
JP:
1. MCP 操作でオブジェクト生成・マテリアル適用・Prefab 作成などを実行
2. `manage_scene(action="screenshot")` で PNG を作成
3. PNG を `docs/assets/` へコピー
4. Pillow で GIF を生成

Example (GIF generation):
```python
from PIL import Image
from pathlib import Path

root = Path("docs/assets")
frames = [Image.open(root / f"unity-mcp-step{i}.png") for i in (1, 2, 3)]
frames[0].save(
    root / "unity-mcp-demo.gif",
    save_all=True,
    append_images=frames[1:],
    duration=900,
    loop=0,
)
```

## 3) Blender MCP demo update
Prereqs:
- Blender MCP addon enabled
- MCP server started (UI Connect)
JP:
- Blender MCP addon 有効化
- Blender MCP サーバ起動（UI で Connect）

Steps:
1. Use `execute_code` to create/modify objects and materials
2. Use `get_viewport_screenshot` to save PNGs
3. Convert PNG sequence to GIF
JP:
1. `execute_code` でオブジェクト生成・モデリング・マテリアル変更
2. `get_viewport_screenshot` で PNG を保存
3. 連番 PNG を GIF に変換

## 4) README update
- README.md uses `docs/assets/...`
- README.rst uses raw GitHub URLs
- Update captions when new demos are added
JP:
- README.md の画像リンクは `docs/assets/...`
- README.rst は raw GitHub URL
- 新しいデモを追加した場合は説明文も追記

## 5) PyPI visibility
- PyPI renders README.rst
- Repository must be public for raw URLs
JP:
- PyPI は README.rst を表示
- raw URL 表示のため、リポジトリは public が必要
