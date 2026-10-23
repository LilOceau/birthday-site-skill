# 生日网站 · 可独立运行的工程

一个无前端框架、无需打包器的静态网站。包含信封开场、日期相册、Live / 普通视频、拼贴、图片问答和本地进度。示例人物“小夏”、日期与素材均为虚构，几何插画与短片由程序生成。

## 先运行

需要 Python 3.11+。在本目录执行：

```text
python build.py
python serve.py
```

打开 http://127.0.0.1:8765 ，点击信封，再点击“走进这一年”。“带我看一段回忆”打开 **06/15**；数字面板输入 **0822** 可开启第二个相册。使用 Ctrl+C 停止服务。不要用 file:// 打开网页。

仅预览和编辑文案不需要 pip、Node、账号或插件。`serve.py` 支持视频 Range 请求，默认只监听本机。需要同一局域网手机预览时，可显式使用 `python serve.py --bind 0.0.0.0`，再访问电脑的局域网 IP。

## 修改姓名、文案与内容

| 文件 | 修改内容 |
| --- | --- |
| `site.json` | recipient、title、year、description、letterLine、letterDescription；welcomeDate 是已存在的 MM/DD 或 null |
| `content.json` | memories 日期相册、collage 拼贴数组、quiz 问答数组 |
| `index.template.html` | 页面结构；花括号占位符由 build.py 转义并替换 |
| `dist/*.css`、`dist/app.js` 等 | 样式、交互源码，直接编辑并保留 |
| `import-options.json` | Live 日期和文件编号覆盖 |

完整字段、必填项、媒体类型、默认值、路径与版本兼容规则见 [数据格式规范 v1](docs/content-model.md)。三份 JSON 自带本地 Schema 引用，编辑器可提供补全和错误提示；运行 `python validate_data.py` 可只读检查配置和资源，无需额外安装依赖。

每次修改后运行 `python build.py`。构建只生成 `dist/index.html` 和 `dist/content.js`，不会重建整个 dist。**不要删除 dist**：其余 JS、CSS、媒体都是工程必需文件。构建前的生成文件会保存到 `.backups/`。

`site.id` 决定浏览器进度存储键；初始化器自动生成独立 ID。修改 ID 会开始新的进度，旧记录仍保留在浏览器中。title 最长 48 字符、recipient 最长 32 字符；较长文案需要自行预览排版。

问答答案为零起始索引 `0..3`，`null` 表示待揭晓且不计分。每题四个选项，文字或图片对象均可：

```json
{
  "question": "最喜欢哪张图？",
  "options": ["海边", "森林", "山间", "城市"],
  "answer": 0,
  "explanation": "这里填写解析。"
}
```

图片选项使用 `{"label":"海边","src":"assets/quiz/a.png","preview":"assets/quiz/a-small.webp"}`。文件放在 `dist/assets/quiz/`，四个选项按 A–D 顺序填写。可选 `explanationImages` 为包含 `src`、`alt` 的对象数组。图片路径只能引用本地 assets，不能使用外部 URL。完整可运行的数据结构见附带的 content.json。

## 配置主题、栏目与浏览行为

除了基础姓名与文案，site.json 还支持 `theme`（主要配色）、`assets`（开场与信纸素材）、`sections`（栏目与导航）、`behavior`（进度、播放、预加载、动效与提示）、`labels`（页面文案）。所有新增字段均可省略或部分覆盖，旧配置继续使用默认值。

具体字段和默认值见 [配置指南](docs/customization.md)；[site.custom.example.json](site.custom.example.json) 演示暖色主题、隐藏拼贴及只在本次访问中保存进度。将需要的配置组复制到现有 site.json，保留自己的 id 和内容，然后校验、构建、预览。

## 导入自己的素材

首次导入需要 Python 依赖；建议使用虚拟环境：

```text
python -m venv .venv
```

Windows PowerShell 使用 `.venv\Scripts\Activate.ps1`；macOS / Linux 使用 `source .venv/bin/activate`。若 PowerShell 禁止激活脚本，可直接用 `.venv\Scripts\python.exe` 替换以下命令中的 python。

```text
python -m pip install -r requirements.txt
python import-materials.py --date 06.15
python import-collages.py
python build.py --check
```

默认输入结构：

```text
materials/
  photos/
    06.15/01-seaside.png
    06.15/02-hills.png
    06.15/03-live.mp4
    08.22/01-evening.png
    08.22/02-video.mp4
  collages/
    01-journal.png
    02-journal.png
```

替换这些虚构素材，或新增 `MM.DD/` 目录。只读取该日期目录顶层 PNG/JPEG/WebP/MP4。`--source` 可以指定 photos 根目录或 collages 目录，路径含空格时加引号。HEIC、MOV 需要先另存为受支持的格式；不要覆盖原件。

照片导入必须指定 `--date MM.DD`，只更新该日期，保留其他相册、当前相册标题、拼贴和问答；同一日期目录是该相册的完整输入，移除输入文件后再次导入也会从该相册移除其条目，但旧输出文件仍保留。拼贴导入重建拼贴列表，保留相册和问答。

按文件名开头数字或末尾 `-数字` / `_数字` 排序；末尾编号优先。重复编号会中止，时间戳文件需在 import-options.json 明确指定：

```json
{
  "live_dates": ["06.15"],
  "sequence_overrides": {
    "06.15": {"20260615120000.png": 4},
    "collages": {"my-journal.png": 3}
  }
}
```

MP4 文件名包含 `live`，或所属 MM.DD 在 `live_dates` 中时，作为静音 Live；其他 MP4 为普通视频。输入视频必须是 H.264；导入保留压缩视频流并核对 SHA256，不自动转码。普通视频保留原音轨，建议 AAC；其他音频编码的播放兼容性需单独验证。图像会生成预览/缩略图，并保留原文件字节；Live 原图使用视频第一帧。

导入在内容更新前完成转换与校验；输出使用内容哈希目录，不覆盖已有不同内容。跨平台 FFmpeg 等工具可能产生不同的封装字节，这时按输出哈希保存独立版本，旧文件保持不变。配置与生成文件逐个原子写入，修改前副本在 `.backups/`，来源/输出哈希在 `manifests/`。这是可恢复的文件流程，不是跨文件数据库事务；若中断，可从同一备份目录恢复 content.json，再运行 build.py。

## 检查与打包

```text
python validate_data.py
python build.py --check
python -m pip install -r requirements-dev.txt
python -m unittest discover -s tests -v
npm ci
npx playwright install chromium
npm run test:browser
npm run test:configuration
python export.py release/birthday-site.zip
```

只读校验和构建只需 Python 标准库；Python 测试使用 requirements-dev.txt（包含导入依赖与 jsonschema），覆盖格式一致性、字段边界和导入保护；浏览器测试需要 Node.js 22+ 和 Playwright。测试使用临时工程/独立浏览器，不访问个人浏览器资料。截图保存在 `.local/`，测试自动关闭服务。可通过 `PYTHON`、`PLAYWRIGHT_MODULE`、`CHROMIUM_PATH` 环境变量选择已有运行时。手机尺寸测试不等于真实 iOS/Safari 验收。

export.py 拒绝过期构建和已有输出路径，只打包 dist 内容。它也会包含 dist 中保留的旧媒体，**导出不是隐私过滤器**；上线前检查 dist 及内容。日期解锁只是互动，所有部署资源都可以被访问，不能作为照片访问控制。

## 部署

这是静态站，可将 ZIP 解压后的文件上传到任意支持静态文件的托管。根目录已提供 netlify.toml（发布目录 dist）。Netlify 手动上传选择 dist；使用 Git 集成时，提交最新生成文件并将发布目录设为 dist，不需要 Node 构建命令。其他托管服务也应把网站放在所选站点的根目录。

若已安装并登录 Netlify CLI，可先创建预览部署，检查后再发布同一份内容；将 YOUR_SITE_ID 替换为你自己的站点 ID：

```text
netlify deploy --dir dist --site YOUR_SITE_ID
netlify deploy --dir dist --site YOUR_SITE_ID --prod
```

这些命令会上传网站，导入器和构建器不会自动发布。没有预配置的账号、站点 ID 或令牌。Sites 等插件是可选托管方式，不是运行依赖。

## 保留与清理

始终保留配置、源码、dist、原始素材、导入清单和所需回滚副本。`.work/` 是转换临时目录，确认成功后可清理；`.local/` 是本地报告；依赖环境可重装。materials 被 .gitignore 忽略以减少误提交，但仍需独立备份。不要把历史压缩包、部署快照或 `.backups/` 一概删除。

代码和仓库自制的虚构演示素材使用 [MIT License](LICENSE)。自己的照片、音乐、字体等素材需另行确认使用权限。Python/Node 依赖及 FFmpeg 各自遵循上游许可证；本工程没有内置分发其程序文件。
