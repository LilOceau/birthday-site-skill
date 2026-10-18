# 内容与媒体流水线

## 项目布局和依赖

项目通常位于 `网站及发布更新/birthday-site/`。上级工作区保留 `随机日期照片/`、`拼贴照片/确认上传成片/`、`趣味问答/`、开场参考与原始素材。不要依赖某台机器的盘符或用户名。

- `dist/content.js`：`window.BIRTHDAY_CONTENT`，包含 memories、collage、quiz 和提示配置。
- `dist/app.js`：日期、拼贴、问答与进度；`viewer.js`：原图、缩放、触摸及媒体提交。
- `dist/opening.css` / `opening.js`：信封开场；`chapters.css`：正文信笺样式；`live-cache.js`：缓存调度。
- `import-options.json`：`live_dates` 与按日期/原文件名的 `sequence_overrides`。
- `originals-manifest.json`、`collage-import-manifest.json`、`live-video-manifest.json`：来源与完整性证据。

需要 Python、Node 和 `imageio_ffmpeg`。现有脚本向 Python 搜索路径加入工作区 `.tools/`；先确认该目录可读以及 FFmpeg 可执行，访问失败不能被解释为空缓存。无可用模块时，在获得相应安装权限后使用可发现的 Python 环境安装，而不删除现有模块。浏览器测试另需 Playwright 和浏览器，静态站运行本身无需 node_modules。

## 日期照片与 Live

1. 保存修改前 `content.js` 与文件清单，检查本次日期顶层媒体和 `import-options.json`。
2. 只处理日期文件夹顶层文件，保留编号间隔，拒绝重复编号。导入器支持数字开头或末尾 `-数字` / `_数字`；时间戳文件尤其容易被错误识别，需显式配置 `sequence_overrides`，不重命名原件。
3. 增量执行 `python import-materials.py --date MM.DD`。无 `--date` 会重建 memories，可能覆盖相册的自定义元数据；仅在明确全量任务时使用。`--live-only` 也会重写相册内容，不能当成无副作用的校验命令。
4. Live 使用源视频 `-map 0:v:0 -c:v copy -an -movflags +faststart`，保留分辨率、帧率与压缩视频流。普通长视频仍使用独立播放器。对不明确的 MP4 分类，根据已配置的 live_dates 与用户意图决定，不猜测。
5. 对新 Live 比较源文件前后 SHA256，并用 FFmpeg `-c:v copy -f hash -hash sha256 -` 核对源和输出的视频流。导入器本身不产生完整的流哈希审计，不能把导入成功等同于此项已验证。
6. 静态原图复制到 `assets/originals` 并核对 SHA256；Live 原尺寸首帧使用无损 WebP，网页仍保留独立预览与缩略图。
7. 比较内容对象：指定日期之外的相册、collage、quiz 以及自定义字段应保持。检查所有 src、poster、thumb、preview、original 的文件存在性。

`prepare-originals.py` 会补原图并重新生成问答预览、写入内容与清单；`prepare-live-video.py` 会全量转换当前 Live 并写清单。仅在需要对应全量工作时执行，不能作为例行只读检查。`optimize-live-previews.py` 是转调原画视频流程的兼容入口，名称不代表当前实际行为。

每次替换或重新导入视频，要更新 `live-cache.js` 内的视频资源 version 和 `index.html` 对该脚本的版本参数，避免长缓存继续使用旧字节。

## 拼贴

`python import-collages.py` 从 `拼贴照片/确认上传成片/` 读取顶层 PNG，按文件名前导数字排序，拒绝重复编号，原样复制 PNG，生成最长边 1400px 的 preview 和 240px 的 thumb，并验证源与副本 SHA256。脚本重建整个 collage 数组，因此必须保留先前确认的全部成片，并检查自定义 caption 等元数据是否需保留。不要从草稿目录递归收图。

## 问答

保持题目、选项名称与顺序，答案用 0–3 索引；未定答案为 null、不计分。图片选项使用当前数据结构的 `{label, src, preview, alt}`；原 JPG/PNG 与网页预览分开，选项完整等比显示，图片题保持 2×2，放大控件与作答分离。说明使用 explanation / explanationImages，并检查换题、重玩和恢复后的清理。补图和说明不应改变原题的进度签名，只有实际题目/答案变化才作对应失效处理。
