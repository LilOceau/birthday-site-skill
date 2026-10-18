---
name: birthday-site-workflow
description: 从附带完整模板创建生日静态网站，或维护现有生日网站。支持信封开场、日期相册、Live、拼贴、图片问答、增量导入、验证发布和可恢复清理。
---

# 生日网站构建与维护

新建工程时阅读 [references/build-project.md](references/build-project.md)，运行 `scripts/create_project.py <新目录>`。完整模板、虚构素材、导入器与测试都在 `assets/project/`，安装整个 skill 后即可使用，无需原站目录、额外插件或账号。

维护已有工程时先识别其版本。含 `site.json`、`content.json`、`build.py` 的附带模板按 build-project.md 操作；旧项目按以下流程核查，不用模板覆盖现有工程。仓库 examples/minimal-site 仍是只读检查器的小型演示，不是新建入口。

## 定位与当前事实

从用户工作区运行 `rg --files -g import-materials.py` 定位项目，阅读当前代码、配置与 Git 状态。**dist 含手工维护的源码与发布媒体，不能当作可再生缓存删除**。新模板仅生成其中 index.html/content.js，旧项目可能直接维护这两个文件。不要执行 clean/reset 覆盖尚未提交的修改。

先运行本 skill 的只读检查：

```powershell
python <skill目录>/scripts/inspect_site.py --site <生日网站目录> --output <项目外的报告路径.json>
```

检查当前内容计数、引用文件与发布文件哈希；计数由现有内容推导，不将历史数量写死。检查不替代浏览器测试，也不证明线上与本地相同。

## 选择工作流程

- 增加日期照片、Live、拼贴、原图或问答：阅读 [references/content-workflow.md](references/content-workflow.md)。使用项目原有脚本与配置，不复制另一份导入器导致分叉。
- 修改交互、验证或发布：阅读 [references/validation-release.md](references/validation-release.md)。发布到当前用户指定的目标，不把 Sites 私有备份与 Netlify 正式站混为一谈。
- 整理缓存、中间文件或回滚：阅读 [references/retention.md](references/retention.md)。先证明依赖关系和副本完整性，再清理。

## 持续保留的行为

- 保留日期分组与数字顺序、白框叠放相册、逐日解锁、间接日历提示和已有拼贴/问答。原素材及其名称不变。
- Live 是保留 H.264 视频流的静音 MP4；若旧工程 README 提到 WebP，先核对实际代码。保持静帧先显示、playing 后切视频、ended 后回静帧，暂停/失败/后台时仍可看照片。
- 翻页等待下载与解码时保留当前画面；仅在新画面提交时同时更新编号、说明、选中项与进度；废弃过期异步结果。
- 原图仅在用户打开对应图片时加载。后台队列只准备预览、缩略图和 Live，前台优先，最多两个任务；隐藏、离线、省流量时暂停，不能额外解锁日期。
- 拼贴保留数字排序、左右按钮、键盘、触摸滑动和放大查看；问答保留用户文字、A–D 顺序及零起始答案索引，缺少答案时不猜测。
- 浏览器 localStorage 是独立的用户进度存储，不能纳入磁盘缓存清理；域名变化也不会自动迁移进度。

视觉修改先提供本地预览；用户确认并要求发布后上传同一份验收字节。已有明确发布授权时直接执行，不重复确认。交付说明实际改动、验证结果、部署目标与仍未验证的部分。
