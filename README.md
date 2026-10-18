# Birthday Site Workflow

一个用于 Codex 的生日静态网站维护 skill，整理日期相册、原画 Live、编号拼贴、图片问答、验证发布和可恢复清理的工作流程。

**首版定位：维护已有工程。** 本仓库提供 AI 操作说明、只读资产检查脚本和虚构的最小示例。完整网站、媒体导入器、交互实现和浏览器回归脚本仍由目标工程提供；目前不支持仅安装此 skill 就从零生成同款网站。

## 包含什么

```text
README.md
LICENSE
.gitignore
birthday-site-workflow/
  SKILL.md
  agents/openai.yaml
  references/
    content-workflow.md
    validation-release.md
    retention.md
  scripts/inspect_site.py
examples/minimal-site/
  README.md
  import-materials.py       # 仅作工程识别标记，拒绝执行真实导入
  import-options.json
  dist/
    index.html
    content.js
    assets/card-a.svg
    assets/card-b.svg
```

- **媒体流程**：沿用目标工程导入器，保留源文件、日期分组、数字顺序和 Live 原画视频流。
- **交互约束**：保持日期解锁、拼贴翻页、问答顺序、原图按需加载和浏览进度。
- **验证与发布**：选择目标工程已有检查，按明确授权发布并核对线上资源。
- **可恢复清理**：先盘点、备份和比对，再清理经过确认的缓存或重复副本。
- **只读检查器**：统计内容、检查静态文件引用、输出发布文件 SHA256；不会导入媒体、清理文件或发布网站。

## 安装到 Codex

在 Codex 中使用内置安装技能：

```text
$skill-installer 安装 https://github.com/LilOceau/birthday-site-skill/tree/main/birthday-site-workflow 中的 skill。
```

仓库为私有时，需要当前账号拥有读取权限；公开后可直接下载。安装后在下一轮对话中调用 `$birthday-site-workflow`。如果已有同名 skill，先检查原版本与本地修改，再执行更新。

也可以克隆仓库，将 **`birthday-site-workflow/` 整个目录**复制到 `$CODEX_HOME/skills/`；未设置 `CODEX_HOME` 时使用 `~/.codex/skills/`。README 与 examples 用于阅读和体验，使用安装器仅安装 skill 子目录时不会一并复制它们。

## 快速体验

以下命令在仓库根目录执行，适用于 PowerShell 或常见终端：

```text
git clone https://github.com/LilOceau/birthday-site-skill.git
cd birthday-site-skill
python birthday-site-workflow/scripts/inspect_site.py --site examples/minimal-site
```

预期统计：**1 个日期、2 张静态图片、0 段 Live、0 个普通视频、1 张拼贴、1 道问答**；缺失引用和越界引用均为空。示例只使用本仓库编写的 SVG 几何图形，不含人物照片、真实问答或部署账号。

需要保存详细哈希报告时：

```text
python birthday-site-workflow/scripts/inspect_site.py --site examples/minimal-site --output .local/minimal-inspection.json
```

报告必须在被检查工程之外；若输出文件已存在，请选用新文件名。详细步骤与预期结果见 [最小示例说明](examples/minimal-site/README.md)。

## 环境依赖

| 操作 | 所需环境 |
| --- | --- |
| 让 Codex 阅读和执行流程 | 支持本地 skills 的 Codex 环境，以及目标工程文件访问权限 |
| 运行附带检查器与最小示例 | Python 3.11+、可在 PATH 中调用的 Node.js；检查器使用 Python/Node 标准库，无需 pip/npm 安装包 |
| 执行真实媒体导入 | 目标工程的导入脚本、原始素材，以及脚本使用的 FFmpeg / `imageio_ffmpeg` |
| 执行浏览器回归 | 目标工程的 `validate*.cjs`、Playwright 及匹配的浏览器运行时 |
| 发布网站 | 目标工程配置；选择 Netlify 时需要其 CLI 和授权，选择 Sites 时需要可用的相应工具与授权 |

本次示例验证环境为 Windows PowerShell、Python 3.13、Node.js 24；其他环境请先运行上面的只读示例。基础流程无需额外 MCP 服务或插件清单。Sites 是可选发布路径，不是安装本 skill 的前置条件。

## 接入自己的工程

skill 会查找 `import-materials.py` 与 `dist/content.js`。请先让 Codex 阅读工程，再判断是否兼容；同名文件并不证明实现相同。

| 约定 | 目标工程需要提供的内容 |
| --- | --- |
| `dist/` | 手工维护的网页源码和发布资源；不能直接视为可删除的构建缓存 |
| `dist/content.js` | 定义 `window.BIRTHDAY_CONTENT`，含 `memories`、`collage`、`quiz` |
| 日期相册 | `memories[].photos[]` 中的 `src`、`thumb`、`type`，按需使用 `poster` / `original` |
| 拼贴 | `collage[]` 中的原图、预览、缩略图及编号顺序 |
| 问答 | `quiz[]` 中的题目、四个选项、0–3 的答案索引；未确定答案可为 null |
| 导入配置 | `import-options.json` 中的 `live_dates` 与 `sequence_overrides` |
| 导入与回归 | 工程自己的 `import-materials.py`、`import-collages.py`、`prepare-*.py` 和相关 `validate*.cjs` |

完整流程还涉及 `app.js`、`viewer.js`、`opening.js`、`live-cache.js` 等工程实现。目录名称、媒体分类与验证命令应按实际项目适配。缺少某项脚本时，先说明缺口；不要把示例识别标记当成可用导入器。

调用示例：

```text
$birthday-site-workflow 检查当前生日网站的媒体引用和构建依赖，报告缺失项。

$birthday-site-workflow 将指定日期文件夹增量导入现有工程，保留其他相册、拼贴和问答，完成本地验证。

$birthday-site-workflow 盘点当前工程的缓存、历史发布包和中间目录，先列出可验证的保留与清理依据。
```

## 检查范围与限制

检查器覆盖内容对象中的常见资源字段，以及 HTML/CSS 中的静态链接；不会发现所有动态拼接 URL，不验证图片解码、视频流、浏览器交互或线上部署。退出码 0 表示这些检查未发现问题，1 表示缺失或越界引用；参数错误及执行错误也会返回非零值。

`content.js` 会由 Node.js 执行以读取内容对象。仅对可信的本地工程运行；`node:vm` 不应被当作执行不可信 JavaScript 的安全边界。

流程说明中的媒体导入、清理和发布会影响文件或外部服务，须按实际用户任务范围执行；只读检查通过不代表已获发布或删除授权。浏览器 localStorage 中的个人进度不属于构建缓存。

## 发布范围与后续方向

首版提供维护流程与检查示例。后续构建版计划补充去除个人内容的网站模板、可复用导入器与独立验证流程；这些能力尚未包含在本版本中。

当前仓库不分发个人照片、真实视频、原站问答内容、部署标识或凭据。`.gitignore` 用于减少误提交，提交前仍应检查实际文件清单。

## 许可证

仓库内的说明、检查脚本和虚构示例采用 [MIT License](LICENSE)。接入项目自有代码、素材和第三方工具的授权由对应项目另行提供。
