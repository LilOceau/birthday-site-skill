# 最小检查示例

这个目录演示 skill 所需的最小工程形状、内容数据和资源检查结果。它不是完整生日网站，没有信封动画、日期解锁、看图器、Live 播放或真实媒体导入。

素材为自制 SVG 色块与几何图形，日期、标题、问答均为虚构。两张图片被相册与拼贴复用，因此不需要个人照片。

## 运行

需要 Python 3.11+ 和 PATH 中可调用的 Node.js。在**仓库根目录**执行：

```text
python birthday-site-workflow/scripts/inspect_site.py --site examples/minimal-site
```

关键输出应为：

```json
{
  "counts": {
    "albums": 1,
    "media": 2,
    "live": 0,
    "videos": 0,
    "collages": 1,
    "quiz": 1
  },
  "distFiles": 4,
  "missingReferences": [],
  "invalidReferences": [],
  "externalReferences": []
}
```

命令还会输出 `distBytes`。需要逐文件大小与 SHA256 时增加 `--output .local/minimal-inspection.json`；输出文件不能已存在，也不能放进被检查工程中。

可选：执行下面的命令，再打开终端显示的本地地址，查看静态资源说明页。按 Ctrl+C 停止服务。

```text
python -m http.server 8765 --bind 127.0.0.1 --directory examples/minimal-site/dist
```

## 文件角色

- `dist/content.js`：1 个日期、2 张静态图、1 张拼贴、1 道文字问答；答案索引从 0 开始。
- `dist/assets/`：两张本仓库生成的 SVG；查询参数和片段示例用于演示引用检查会去掉 URL 的 `?` / `#` 部分。
- `import-options.json`：展示媒体分类与编号映射字段；空配置不导入任何素材。
- `import-materials.py`：仅满足检查器的工程识别条件。直接执行会返回状态码 2 并说明缺少真实导入器，不会读写媒体。

## 接入真实项目时

先提供目标工程自己的导入器与网页实现，再使用 skill 的完整流程。不要把这个识别标记复制到正式项目以覆盖已有脚本。引用存在检查不等同于媒体、交互和发布验证。
