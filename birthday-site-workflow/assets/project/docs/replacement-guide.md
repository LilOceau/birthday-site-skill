# 从演示替换成你的网站（Windows）

在线体验：[生日网站虚构演示](https://liloceau.github.io/birthday-site-skill/)。人物“小夏”、所有插画与短片均为虚构。点击信封 → 走进这一年 → 带我看一段回忆；输入 **0822** 可打开另一组相册。页面底部有源码与本教程入口。

这份教程使用 PowerShell，不需要 Bash。不了解目录结构也可以先按前四步完成本地预览；纯预览不需要 Node、Git、账号或插件。另附可用记事本打开的 [操作说明.txt](../操作说明.txt)。

## 1. 下载并创建自己的工程

安装 Python 3.11 或更新版本。打开 PowerShell，输入 `python --version`，应显示版本号；如果跳转商店或提示找不到命令，先完成 Python 安装并重新打开终端。若电脑只识别 `py`，可把下方 `python` 换成 `py`。

从 [Release](https://github.com/LilOceau/birthday-site-skill/releases/latest) 下载 `birthday-site-skill-v版本号.zip` 并解压。在解压后的文件夹中打开终端；这里应能看到 README.md 和 birthday-site-workflow 文件夹。输入：

```powershell
python .\birthday-site-workflow\scripts\create_project.py ..\my-birthday-site --recipient "小夏" --title "A day for you"
Set-Location ..\my-birthday-site
python serve.py
```

把姓名和标题换成自己的文字；目标 `my-birthday-site` 必须还不存在，如果提示已存在，请换一个新文件夹名，不要先删除旧项目。成功后打开终端显示的本地地址，通常是 http://127.0.0.1:8765 。不要双击 index.html。停止服务按 Ctrl+C；后续命令均在含 site.json 的工程目录执行。

## 2. 修改姓名、文案、颜色和栏目

先复制一份配置备份，再用记事本打开：

```powershell
Copy-Item -LiteralPath .\site.json -Destination (".\site-before-edit-" + (Get-Date -Format "yyyyMMdd-HHmmss") + ".json")
notepad .\site.json
```

主要修改 recipient（姓名）、title（标题）、year（年份）、description（简介）、letterLine / letterDescription（信纸上的文案）。保留自动生成的 id；它对应浏览器进度。welcomeDate 必须对应 content.json 中存在的相册，例如 `"06/15"`，不需要迎宾入口可写 null。

theme 改颜色，sections 控制相册 / 拼贴 / 问答显示，labels 改按钮和栏目文案。默认示例在 site.json；暖色局部配置见 site.custom.example.json。复制需要的字段即可，不要用整个示例覆盖自己的姓名和 id。完整字段见 [配置指南](customization.md)。

保存时保留 `.json` 后缀并选择 UTF-8。JSON 使用英文双引号、逗号和冒号；最后一项后面不能再加逗号，也不能写注释。每次修改后先执行：

```powershell
python validate_data.py
python build.py
```

出现 PASS 后继续；报错时根据提示的文件 / 字段检查，不要忽略错误直接上传。

## 3. 替换照片、Live 和拼贴

首次导入安装依赖，只需一次：

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
New-Item -ItemType Directory -Force -Path .\materials\my-photos\06.15, .\materials\my-photos\08.22, .\materials\my-collages
```

无需激活脚本。用资源管理器把照片**复制**到这些新目录，保留原件。每个日期目录放该日希望展示的完整素材：

```text
materials\my-photos\06.15\01-photo.jpg
materials\my-photos\06.15\02-photo.jpg
materials\my-photos\06.15\03-live.mp4
materials\my-photos\08.22\01-photo.jpg
materials\my-collages\01-collage.png
materials\my-collages\02-collage.png
```

示例文件名只是说明，不会自动创建照片。支持 JPG/JPEG、PNG、WebP、H.264 MP4。HEIC / MOV 请先另存成受支持格式；不要只改扩展名。按 01、02、03 编号，同一目录不能重复编号；长时间戳文件可在 import-options.json 的 sequence_overrides 中指定顺序。

素材准备好后执行以下命令；空目录会报错，应先放入素材：

```powershell
.\.venv\Scripts\python.exe import-materials.py --date 06.15 --source .\materials\my-photos
.\.venv\Scripts\python.exe import-materials.py --date 08.22 --source .\materials\my-photos
.\.venv\Scripts\python.exe import-collages.py --source .\materials\my-collages
python build.py --check
```

这会替换示例两天的媒体及拼贴；同一天的导入会替换该日整个 photos 列表，不是追加单张。其他日期和问答保持不变。示例 import-options.json 的 live_dates 含 `"06.15"`，因此那天所有 MP4 都按 Live 处理；需要普通视频时移除该日期，同时确保文件名不含 live。Live 静音且保留视频流，普通视频保留原音轨；建议 H.264 视频 / AAC 音频。

想用其他日期：创建对应 `MM.DD` 目录再导入；在 content.json 中删除不需要的示例相册对象，并同步 welcomeDate，最后重新校验。不要直接改 dist/content.js。相册标题、caption 照片说明可在 content.json 编辑；重新导入目标日期会重建媒体说明，宜先完成素材导入再精修。

导入前的配置会备份到 `.backups/`，来源和输出哈希会写入 manifests。旧输出不会自动删除。**隐藏某个栏目不会删除其数据，打包也会保留 dist 中已有的旧文件**；上线前逐项检查，不能用隐藏开关保护私人照片。

## 4. 替换问答

```powershell
notepad .\content.json
```

找到 quiz 数组，把题干、选项、答案和解析改成自己的内容。每题恰好四个选项：answer 为 0 对应第一项，1 对应第二项，2 对应第三项，3 对应第四项；null 表示开放题、暂不计分。

```json
{
  "question": "下一次最想去哪里？",
  "options": ["海边", "森林", "山间", "城市"],
  "answer": null,
  "explanation": "这次由你来决定。"
}
```

这是 quiz 中单题的示例，不是整个 content.json。图片选项、解析配图的完整格式见 [数据格式规范](content-model.md#quiz问答)。图片放进 dist/assets 下，配置使用 `assets/...` 相对路径。保存后再次执行 validate_data.py 和 build.py。

## 5. 替换图标与分享封面

按照 [图标与分享预览指南](sharing.md) 替换四个 branding 文件，或使用 make_branding.py。中文标题的 Windows 示例：

```powershell
.\.venv\Scripts\python.exe make_branding.py --replace --font "C:\Windows\Fonts\msyh.ttc" --subtitle "把值得记住的日子，慢慢翻给你看。"
python build.py
```

先确认该字体存在。分享卡片上的文字是 PNG 的一部分：改了 JSON 标题或配色后，还需重新生成或更换封面。`--replace` 会先备份旧图标和封面。

尚未部署时 sharing.url 保持空字符串。获得自己的 HTTPS 网址后填写完整地址，末尾加 `/`；不要把作者在线演示的网址填成你的网站。然后再次构建和上传。公开页面会输出 Open Graph / Twitter 元数据；具体聊天平台的缓存、裁切和显示效果可能不同。

## 6. 预览、打包和上传

```powershell
python validate_data.py
python build.py --check
python serve.py
```

检查姓名、信纸、两个日期、全部照片、Live 手动播放、拼贴、四个选项和答案。缩小浏览器检查手机尺寸，真正给手机用户使用时再用手机验收。检查完成按 Ctrl+C，再打包：

```powershell
python export.py .\release\birthday-site.zip
```

输出文件已存在时换个新文件名，例如 birthday-site-v2.zip；导出器不会覆盖旧包。将 ZIP 解压后的 index.html 与 assets 等文件上传到自己的静态托管，或按托管平台要求选择整个 dist 文件夹。不要把工程根目录、原始素材、.backups 或账号凭证一起上传。

仓库的 [在线演示工作流](https://github.com/LilOceau/birthday-site-skill/blob/main/.github/workflows/demo.yml) 由维护者手动启动，在全部测试通过后只发布内置虚构模板。它不用于上传你的本地私人网站，也不会随一次配置编辑自动发布。你自己的站点需要选择账号、访问范围与部署地址。

## 常见问题

- **不知道当前在哪个文件夹**：运行 `Get-Location` 和 `Get-ChildItem`，应看到 site.json、content.json、build.py。
- **端口被占用**：运行 `python serve.py --port 8766`，打开对应新端口。
- **导入提示重复编号**：同一日期的两个文件可能都叫 01，调整复制件的编号或 sequence_overrides，不改动原件。
- **JSON 报错**：检查英文引号、逗号、UTF-8 和末项尾逗号。不要把教程中的局部片段覆盖整个配置。
- **修改后没生效**：确认保存了文件、运行 build.py，再刷新；分享平台还可能缓存旧预览。
- **需要恢复**：先备份当前状态，再从同一 `.backups/时间戳/` 中恢复相应 site.json / content.json 或 branding 文件，然后构建；不同操作的备份内容不同，不要混用不相关版本。源照片仍以你保留的原件为准。
