# 验证与发布

## 本地验证

在生日网站目录运行 `node --check` 检查实际改动的 JS，然后运行：

```powershell
node validate.cjs
node validate.cjs --reduced-motion
node validate-opening.cjs
```

使用单独终端运行 `python -m http.server 8765 --bind 127.0.0.1 --directory dist`。确认端口属于此网站；测试可用 `PREVIEW_URL` 更换地址。若 Playwright 默认路径不存在，设置 `PLAYWRIGHT_MODULE` 指向实际可用模块。不要把环境故障记为测试通过。

根据变化选择现有真实浏览器回归：

| 变化 | 脚本 |
| --- | --- |
| 看图、缩放、触摸、慢加载与高清切换 | `node validate-viewer.cjs` |
| 拼贴布局、进度、问答恢复 | `node validate-progress.cjs` |
| Live 原画播放、自动播放限制、旧路径进度迁移 | `node validate-live-video.cjs` |
| Live 静帧优先、迟到响应、重播、重试 | `node validate-live-loading.cjs` |
| 后台缓存、前台优先、暂停恢复与去重 | `node validate-continuous-cache.cjs` |

验证脚本中可能存在历史固定数量、旧路径或环境假设。先判断失败是否来自本次实现，再按实际内容更新有意义的断言，不能为了“通过”弱化行为检查。现有脚本会把报告写到 `.tools/` 中固定日期目录；需要保留旧证据时先备份报告，或在隔离的测试副本中改输出目录。

开场视觉修改检查关键帧、重播、后台暂停、减少动态效果、手机与桌面，并给用户查看真实连续播放。受限浏览器的低频 rAF 采样不能证明真实流畅度。Windows WebKit 的 H.264 解码不支持结果不能等同于真实 iPhone Safari 验证。

## 发布

先读取 `netlify.toml`、`.netlify/state.json`、README 的最近发布记录和 `.openai/hosting.json`，区分：Netlify 正式网站、Sites 私有备份、本地未发布修改。目标 ID 和网址从现有项目读取，不从本 skill 推断。

Netlify 已获发布授权且本地验证完成时：

```powershell
netlify deploy --prod --no-build --dir dist --site <已核对的站点ID>
```

保留所用 CLI 的依赖，或在环境可安装时使用已授权工具；不要从日志或账号文件提取凭据写进报告/skill。只上传 dist，不上传原始工作区、Git、备份、测试输出或本地身份信息。

Sites 仅在用户选择该目标时使用当前可用 Sites skill/连接器的打包发布流程。若 Bash 打包不可用，Windows `tar.exe` 可打包已准备好的静态目录；保持其实际源版本一致，不为打包故障重做内容导入。

发布后记录部署状态、版本/ID、地址和本地摘要。从目标站读取 index.html、改动的 JS/CSS/content.js 及本次新增资源，核对 SHA256 和 HTTP 状态。必要时在匿名浏览器验证。连接器 succeeded 与 HTTP 探测受限分别记录，不能将 403/超时解释为字节相同。仅本地修改任务不自动触发生产发布。
