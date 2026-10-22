# Birthday Site Skill

从零创建可运行的生日网站，也可维护已有生日网站。该 Codex skill 内置完整静态工程、虚构示例素材、增量导入器、验证脚本和部署说明；**无需访问作者的私人项目即可独立使用**。

信封开场 → 日期解锁相册 → Live 与视频 → 编号拼贴 → 图片问答。保留灰蓝信笺风格、手机适配、原图按需加载和浏览器进度。

## 五分钟开始

先安装 Python 3.11+。在 PowerShell、macOS 或 Linux 终端运行：

```text
git clone https://github.com/LilOceau/birthday-site-skill.git
cd birthday-site-skill
python birthday-site-workflow/scripts/create_project.py ../my-birthday-site --recipient 小夏 --title "A day for you"
cd ../my-birthday-site
python serve.py
```

打开 http://127.0.0.1:8765 。点击信封和“走进这一年”；迎宾相册是 **06/15**，另一个日期是 **08/22**。Ctrl+C 停止预览。目标目录必须不存在，初始化器不会覆盖已有内容。

预览不需要安装 pip/npm 包，也不需要账号、API key 或插件。下载仓库 ZIP 后也能运行同一初始化命令，无需 Git。新工程的 [README](birthday-site-workflow/assets/project/README.md) 包含完整的配置、媒体导入、测试、恢复和发布步骤。

## 作为 Codex skill 使用

将 `birthday-site-workflow/` **整个目录**复制到 `$CODEX_HOME/skills/`（默认 `~/.codex/skills/`），或让 skill-installer 安装：

```text
$skill-installer 安装 https://github.com/LilOceau/birthday-site-skill/tree/main/birthday-site-workflow 中的 skill。
```

重新加载技能后调用：

```text
$birthday-site-workflow 在新目录创建一个生日网站，收件人为小夏，先用示例素材给我预览。
```

安装器只需安装 skill 子目录，完整工程已包含在里面。有旧版本时先保留本地修改，再更新整个目录。已有私人站点继续走维护流程，不要用模板覆盖旧工程。

## 版本 0.2.1 包含什么

| 能力 | 实现与入口 |
| --- | --- |
| 创建独立工程 | scripts/create_project.py；新目录保护、独立浏览进度 ID |
| 内容配置 | 三份 JSON Schema、数据格式规范 v1、只读校验；build.py 生成网页内容 |
| 完整前端 | 信封动画、日期相册、Live/普通视频、缩放、拼贴翻页与总览、图片问答 |
| 媒体导入 | 按日期增量导入、编号校验、原件哈希、H.264 视频流保留、备份与清单 |
| 本地预览 | Python 标准库服务，支持视频 Range 请求 |
| 导出部署 | 只导出 dist、Netlify 静态站配置、明确选择部署目标 |
| 验证 | Python 集成测试、Playwright 桌面/手机尺寸/存储受限测试、GitHub Actions |
| 旧站维护 | 原有只读检查器与内容/清理/回滚工作流程仍保留 |

默认演示含 **2 个日期、5 个媒体（其中 1 段 Live、1 个普通视频）、2 张拼贴、3 道问答**。全部图片为原创几何插画，短片为程序生成，无人物照片、私人问答、原站部署地址或第三方字体。

## 数据格式规范

三份配置的字段、日期、资源路径、媒体类型、答案索引和导入编号见 [数据格式规范 v1](birthday-site-workflow/assets/project/docs/content-model.md)。[schemas/](birthday-site-workflow/assets/project/schemas/) 提供编辑器可用的 Draft 2020-12 Schema，附带 JSON 即为完整虚构示例。新旧示例均可校验；不声明 schemaVersion 时按 v1 解释。

在工程目录运行 `python validate_data.py`，即可只读检查三份配置及资源引用，不需要额外安装依赖。

## 替换自己的内容

进入初始化后的工程，编辑 site.json 的姓名、标题、年份和迎宾日期，编辑 content.json 的相册标题与问答，然后运行：

```text
python build.py
```

需要导入自己的照片时安装 requirements.txt，把素材按 `materials/photos/MM.DD/` 和 `materials/collages/` 放好，再执行：

```text
python -m pip install -r requirements.txt
python import-materials.py --date 06.15
python import-collages.py
python build.py --check
```

建议使用虚拟环境，激活方法与格式约定见 [工程说明](birthday-site-workflow/assets/project/README.md)。导入器不改动原始输入，旧输出和必要备份不会自动删除。照片导入仅替换指定日期的媒体列表，拼贴与问答保持不变。

**dist 中既有源码，也有生成文件和媒体，不能整目录清理。** 仅 index.html/content.js 由构建生成；改动这两项应修改上游模板和 JSON。

## 环境与验证

| 操作 | 依赖 |
| --- | --- |
| 初始化、改文案、构建、预览、导出 | Python 3.11+ 标准库 |
| 图片与视频导入 | requirements.txt 中的 Pillow、imageio-ffmpeg |
| Python 测试及 Schema 一致性检查 | requirements-dev.txt，含导入依赖和 jsonschema |
| 浏览器回归 | Node.js 22+、锁定版本的 Playwright 和浏览器 |
| 只读 inspect_site.py | Python 3.11+、Node.js；只用于受信任的本地工程 |
| 上线 | 自选静态托管；账号、站点和授权由使用者提供 |

在新工程目录验证和导出：

```text
python validate_data.py
python build.py --check
python -m pip install -r requirements-dev.txt
python -m unittest discover -s tests -v
npm ci
npx playwright install chromium
npm run test:browser
python export.py release/birthday-site.zip
```

浏览器测试覆盖开场、相册、缩放、Live/视频呈现、拼贴、图片问答和进度恢复；手机尺寸模拟不能替代真实 Safari/iPhone 验收。仓库提供 [CI 流程](.github/workflows/validate.yml)，在干净 Linux 环境初始化后执行同样的检查。

inspect_site.py 会读取并执行本地 content.js（Node vm 不是安全沙箱），不要用于不受信任的 JS。旧的 [minimal-site](examples/minimal-site/README.md) 仅用于演示该检查器；完整构建使用本页初始化器。

## 发布与素材边界

完整工程使用相对资源路径，可部署到支持静态文件的服务；Netlify 配置已附带，具体步骤见工程 README。无需安装专门插件，不会自动创建或覆盖线上站点。

**日期解锁是互动效果，不是访问控制。** 公开部署后，内容和媒体都能被访问。用真实素材建站时，请自己决定访问范围；导出包包含 dist 中保留的旧媒体，不能把打包过程当成隐私过滤。仓库公开与网站上线是两个独立操作。

## 目录与许可

```text
birthday-site-workflow/
  SKILL.md
  agents/openai.yaml
  scripts/                  # 初始化器、只读检查器
  references/               # 新建与旧站维护的分支流程
  assets/project/           # 完整可复制工程、示例素材与测试
examples/minimal-site/       # 保留的检查器小示例
.github/workflows/validate.yml
```

代码和自制演示素材使用 [MIT License](LICENSE)，模板也附带同一许可证。第三方依赖遵循各自许可证；用户自己的图片、音乐和字体不因使用本仓库而自动获得授权。
