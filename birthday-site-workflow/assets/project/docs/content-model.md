# 数据格式规范 v1

适用于随 skill 提供、含 `site.json` / `content.json` / `build.py` 的完整工程。旧版直接维护 `dist/content.js` 的网站不适用，不应直接覆盖或自动迁移。

## 文件与检查入口

| 文件 | Schema | 用途 |
| --- | --- | --- |
| [site.json](../site.json) | [site.schema.json](../schemas/site.schema.json) | 身份、文案、年份、迎宾相册 |
| [content.json](../content.json) | [content.schema.json](../schemas/content.schema.json) | 日期相册、拼贴、问答；完整虚构示例 |
| [import-options.json](../import-options.json) | [import-options.schema.json](../schemas/import-options.schema.json) | Live 日期与素材编号覆盖 |

三个文件均为 UTF-8 JSON 对象，可读取 UTF-8 BOM；不接受注释、尾逗号、重复键、NaN 或 Infinity。字段区分大小写。数字不使用引号；布尔值用 `true` / `false`。JSON Schema 的整数允许 `1.0` 这种数值等于整数的写法，但不允许 `true`、`"1"` 或 `1.5`。

Schema 使用 JSON Schema Draft 2020-12，可由支持该版本的编辑器读取。每份 Schema 自包含，不依赖远程 `$ref`。模板文件开头如下，文件类型不同只需替换文件名：

```json
{
  "$schema": "./schemas/content.schema.json",
  "schemaVersion": 1,
  "memories": [],
  "collage": [],
  "quiz": []
}
```

`$schema` 和 `schemaVersion` 均可省略。已有 0.2.0 工程的 JSON 视为 v1，无需补字段或改变媒体路径；显式版本目前只接受整数 `1`。`$schema` 是编辑器提示地址，本地校验不会下载或执行它，不能用它绕过内置校验。这两个元数据字段不写入生成的 `dist/content.js`。

未知字段允许作为扩展元数据，不代表前端会使用它们。以 `customMetadata` 这类独立命名保存扩展，避免冒用已有字段名。导入保留顶层、未替换内容及已存在相册对象的扩展字段；**目标日期的 photos 和整个 collage 列表会重建，其条目内自定义字段不会自动合并**。不要把私人信息或密钥放在内容扩展字段中：除上述两个格式元数据外，content 顶层数据会进入网站。

在工程目录执行：

```text
python validate_data.py
python build.py --check
```

第一条只读检查三份 JSON、相册关系及资源是否存在，不创建备份或生成文件，也不需要安装依赖。成功退出码为 0，失败为 1，错误定位到如 `content.memories[0].photos[2].poster`。第二条还检查生成网页是否最新，过期时执行 `python build.py`。

Schema 能验证结构、类型、长度、日期格式和取值范围；文件存在性、符号链接越界、重复相册日期、迎宾相册引用由 Python 校验器检查。素材编号冲突还需要读取实际源目录，因此在导入时检查。文件后缀不证明格式、编码或图片尺寸真实正确；视频编码和来源哈希由导入器核验，播放效果仍需浏览器验收。

## 通用路径与文本

所有媒体引用都相对 `dist/`，必须写成 `assets/子目录/文件名`，例如 `assets/demo/choice-1.png`，对应 `dist/assets/demo/choice-1.png`。只允许本地文件，禁止 URL、绝对路径、反斜杠、空路径段、`.` / `..` 路径段、冒号、`?`、`#`、`%` 和控制字符。中文、空格允许；应按真实大小写书写，以兼容 Linux 部署。可选路径存在时也必须有效，不能用空字符串或 null 占位；没有资源时省略字段。

标为“非空文本”的字段必须包含非空白字符；最大长度按 Unicode 字符数计算。文案按纯文本处理，不提供 HTML 标记功能。`caption`、`alt`、`explanation` 是可选字符串，可以为空；未规定字符上限，使用者仍需预览长文案的排版。

## site.json

| 字段 | 必填 | 类型 / 限制 | 含义 |
| --- | --- | --- | --- |
| id | 是 | 1–64 字符；首字符小写字母或数字，其余可含 `-` | 浏览器进度命名空间；改变会启用新进度，旧存储仍保留 |
| recipient | 是 | 非空文本，最多 32 字符 | 收件人 |
| title | 是 | 非空文本，最多 48 字符 | 网页标题 |
| year | 是 | 整数，1900–2200 | 展示及日期提示年份，不决定相册排序 |
| description | 是 | 非空文本，最多 160 字符 | 页面描述 |
| letterLine | 是 | 非空文本，最多 48 字符 | 信封主文案 |
| letterDescription | 是 | 非空文本，最多 100 字符 | 信封辅助文案 |
| welcomeDate | 否 | `MM/DD`、null 或省略 | 非空时必须精确对应一个相册日期；null / 省略时隐藏迎宾入口，仍可手动解锁日期 |

日期是无年份的月日，必须补零，允许 `02/29`，不允许 `02/30`、`04/31`；闰日按可存在的年历日期校验，不与 site.year 绑定。

## content.json

`memories`、`collage`、`quiz` 三个数组均必填，允许空数组。顺序有意义：手动编辑按数组顺序呈现；照片导入后，相册按 `MM/DD` 升序，照片按来源编号升序。问答始终保持现有数组顺序。

### memories：日期相册

每个相册必须包含 `date`（唯一的 `MM/DD`）、`title`（非空文本，最多 200 字符）和 `photos`（至少一个媒体对象）。同一天只能有一个相册。

| 媒体字段 | image | live | video | 说明 |
| --- | --- | --- | --- | --- |
| type | `"image"` | `"live"` | `"video"` | 必填 |
| src | 必填 | 必填，结尾 `.live.mp4` | 必填 | 图片预览或视频文件 |
| thumb | 必填 | 必填 | 必填 | 缩略图 |
| poster | 可选 | 必填 | 必填 | 加载或播放前的静帧 |
| preview | 可选 | 可选 | 可选 | 图片查看器使用的预览资源 |
| original | 可选 | 可选 | 可选 | 原图查看入口；Live 导入器生成视频首帧静图 |
| caption / alt | 可选字符串 | 可选字符串 | 可选字符串 | 说明和替代文字；具体显示方式依现有组件 |

Live 的导入输出为保留 H.264 视频流的静音 MP4；普通视频保留原音轨。不要把普通图片改个后缀冒充 Live。完整三种媒体示例见 `content.json`。

### collage：拼贴

每个对象必填 `src`（原图）、`preview`、`thumb`、`width` 和 `height`。宽高为正整数，单位像素；填写原图实际尺寸。`caption`、`alt` 及通用可选路径字段可省略。拼贴按数组顺序显示；导入按文件编号生成，保留与相同 src 对应的非空旧 caption。

### quiz：问答

| 字段 | 必填 | 约束 |
| --- | --- | --- |
| question | 是 | 非空文本，最多 1000 字符 |
| options | 是 | 恰好 4 项，按 A–D 顺序；每项可以是文字或图片对象，可混合 |
| answer | 否 | 0、1、2、3；null 或省略表示待揭晓，不计分 |
| explanation | 否 | 字符串，默认没有解析文字 |
| explanationImages | 否 | 图片对象数组，默认空；每项 src 必填，alt / caption 和通用可选路径字段可省略 |
| pendingImages | 否 | 布尔值，默认 false；true 时选项禁用，该题跳过且不计分；已有图片路径仍须有效 |

文字选项必须非空，最多 500 字符。图片选项必须包含 `label`（非空、最多 500 字符）、`src` 和 `preview`；可选 `alt`、`caption`、`thumb`、`poster`、`original`。答案是**零起始索引**，`0` 对应第一个选项，`3` 对应第四个，不能填写字母或数字字符串。

```json
{
  "question": "哪张图是海边？",
  "options": [
    {"label": "海边", "src": "assets/demo/choice-1.png", "preview": "assets/demo/choice-1.png", "alt": "青蓝色海面"},
    "森林",
    "山间",
    "城市"
  ],
  "answer": 0,
  "explanation": "这是虚构示例。",
  "explanationImages": [{"src": "assets/demo/choice-1.png", "alt": "海边插画"}]
}
```

## import-options.json

两项业务字段均可省略，空对象 `{}` 有效。其默认值只是校验约定，不会自动回写文件。

| 字段 | 类型 / 默认值 | 规则 |
| --- | --- | --- |
| live_dates | 字符串数组 / `[]` | 唯一的合法 `MM.DD`，注意使用点号；日期可先配置，不要求已有相册或源目录 |
| sequence_overrides | 对象 / `{}` | 来源目录名称 → 完整文件名 → 正整数编号 |

```json
{
  "$schema": "./schemas/import-options.schema.json",
  "schemaVersion": 1,
  "live_dates": ["06.15"],
  "sequence_overrides": {
    "06.15": {"20260615120000.png": 4},
    "collages": {"my-journal.png": 3}
  }
}
```

覆盖键必须是单个非空目录名 / 文件名，不允许斜杠、反斜杠、控制字符或单独的 `.` / `..`。目录键采用**实际源目录的 basename**：照片通常为 `06.15`；自定义 `--source D:/my-art` 的拼贴输入应使用 `my-art`，不是固定写 `collages`。编号不要求连续；实际参与同次导入的文件编号不可重复。尚未出现的文件配置可以保留。

编号优先使用覆盖值；否则优先匹配文件名结尾的 `-数字` / `_数字`，再匹配开头数字。自动解析只接受 1–6 位正数，长时间戳需要覆盖配置。MP4 文件名包含 `live`（忽略大小写），或日期在 live_dates 中时，作为 Live；否则作为普通视频。该配置不会把 PNG/JPEG/WebP 转成 Live。

## 兼容与维护规范

从 0.2.0 升级时，不改变已有字段名、数组顺序和答案索引；旧 JSON 可直接通过 v1 校验。此前未约束的可选字段现在会检查类型，未知版本会明确报错。可选字段应省略而非填 null（仅 welcomeDate、answer 支持 null）；如旧数据使用 `assets/./...`、查询参数或百分号编码，应先将路径改为真实文件对应的规范路径，再验证。不会自动改写用户数据。

维护校验器或 Schema 时，安装开发依赖并运行一致性和工作流测试：

```text
python -m pip install -r requirements-dev.txt
python -m unittest discover -s tests -v
```

测试用 Draft 2020-12 校验器核对结构接受 / 拒绝结果，并覆盖旧数据、字段边界、资源关系、只读校验、导入前失败保护和元数据保留。构建与预览继续只用 Python 标准库；jsonschema 仅用于开发测试。破坏兼容的未来改动应提升 schemaVersion，提供明确的迁移说明与备份步骤，不能静默按新版解释旧数据。
