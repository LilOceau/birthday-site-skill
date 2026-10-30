# 图标与分享预览

模板附带原创的灰蓝信封图标和分享卡片，无人物照片或第三方字体文件。

| 文件 | 用途 |
| --- | --- |
| `dist/assets/branding/favicon.svg` | 浏览器标签页 SVG 图标 |
| `dist/assets/branding/favicon-32.png` | 32×32 PNG 备用图标 |
| `dist/assets/branding/apple-touch-icon.png` | 180×180 Apple 主屏幕图标 |
| `dist/assets/branding/social-card.png` | 1200×630 PNG 分享卡片 |

![默认分享封面](../dist/assets/branding/social-card.png)

## 配置正式网址与分享内容

将以下两组加入或合并到 site.json。`icons` 和 `sharing` 均可省略，缺失字段使用默认值。原有 id、姓名、日期相册和问答保持各自用途。

```json
{
  "icons": {
    "favicon": "assets/branding/favicon.svg",
    "fallback": "assets/branding/favicon-32.png",
    "appleTouch": "assets/branding/apple-touch-icon.png"
  },
  "sharing": {
    "url": "https://your-name.github.io/your-site/",
    "title": "写给你的生日来信",
    "description": "把值得记住的日子，慢慢翻给你看。",
    "image": "assets/branding/social-card.png",
    "imageAlt": "灰蓝色信封、信纸与生日祝福"
  }
}
```

这是局部片段，示例域名必须换成自己的正式地址。`sharing.url` 是**网站所在目录的完整 HTTPS 网址，末尾必须有 `/`**。GitHub Pages 项目站应保留仓库子目录；独立域名可以是 `https://example.com/`。不接受查询参数、片段、账号密码、端口、`index.html` 或 `..` 路径。当前规范只接受 ASCII 域名和由字母、数字、点、下划线、横线、波浪号组成的目录名；国际化域名需使用其 ASCII/Punycode 表示，部署目录也应使用支持的名称。

尚未上线时把 url 留为 `""`。这时会生成本地图标引用，但不生成 canonical、Open Graph 或 Twitter 分享标签，避免新项目误用作者演示站的网址。初始化器也不会替你填写正式域名。

title / description 默认空字符串，分别回退到 site.title / site.description；imageAlt 是图片内容的替代说明。标题、摘要和替代说明最多 500 字符，均按纯文本转义，不支持 HTML 和文案占位符。

image 必须是本地 PNG 文件，建议 1200×630，最大 5 MiB、单边不超过 8192 像素。宽高由图片头读取，不需要手填。两份 PNG 图标必须分别为 32×32 和 180×180；favicon 必须是带 SVG 命名空间的 SVG 文件。构建会检查路径、文件类型和尺寸，但不等同于完整图像解码或视觉验收。

## 替换自己的图标或封面

最简单的方法是制作好图片，放进 `dist/assets/branding/` 或自己的 assets 子目录，再更新对应路径。保留一份原文件备份。路径相对 dist，不能填写 C 盘路径或外链。

也可以使用附带的生成器。以下命令在工程目录的 PowerShell 执行，使用现有 site.json 配色、sharing.title（空则用 title）与 letterDescription 生成信封图标和封面：

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe make_branding.py --replace
python build.py
```

不需要激活虚拟环境。生成器默认使用 Pillow 内置拉丁字体；标题或副标题含中文时，需要指定本机支持中文的字体。例如 Windows 的微软雅黑（先确认路径存在）：

```powershell
Test-Path "C:\Windows\Fonts\msyh.ttc"
.\.venv\Scripts\python.exe make_branding.py --replace --font "C:\Windows\Fonts\msyh.ttc" --subtitle "愿每个小小瞬间，都值得收藏。"
python build.py
```

字体仅用于本机生成位图，不会被复制进网站；使用自己的字体时仍需确认用途许可。其他系统请替换为自己的字体路径。生成器不会把不支持的文字悄悄画成方框；未指定字体且文本含非 ASCII 字符时会明确报错。传入的字体仍须由使用者确认字符覆盖。

`--replace` 只覆盖这四个输出文件，并先备份到 `.backups/`；省略此选项时遇到已有文件会拒绝写入。`--output assets/my-brand` 可写入新目录，之后须在 site.json 更新四个路径。改变配色或标题不会自动重画既有 PNG，应运行生成器或自行替换图片后重新构建。封面中的固定小字和信封构图是示例样式；要完全不同的设计可直接换自己的 PNG。

## 如何验证

```powershell
python validate_data.py
python build.py --check
python serve.py
```

在浏览器查看标签页图标，并直接打开本地 `/assets/branding/social-card.png` 检查文字和构图。正式部署后，页面原始 HTML 中应有 canonical、og:title、og:description、og:url、og:image、图片尺寸与 alt，以及 twitter:card 等标签；它们无需执行 JavaScript 即可读取。图片地址必须能够匿名访问，使用登录保护的站点可能无法产生公开分享卡片。

资源链接带内容哈希：替换图片后重新构建会改变参数，帮助平台识别更新。不同聊天应用可能缓存旧卡片、裁切图片或不显示预览，本项目不能强制刷新第三方缓存，也不承诺所有平台的实际展示一致。这里提供的是标准网页元数据，不包含微信 JS-SDK 自定义分享接入。

字段依据：[Open Graph protocol](https://ogp.me/)。发布示例依据：[GitHub Pages 自定义工作流](https://docs.github.com/en/pages/getting-started-with-github-pages/using-custom-workflows-with-github-pages)。
