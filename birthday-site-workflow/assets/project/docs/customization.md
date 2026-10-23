# 网站配置指南

在 `site.json` 中修改文案、主题、装饰素材、栏目与行为，然后执行 `python validate_data.py`、`python build.py`，用 `python serve.py` 预览。无需改动 HTML / CSS / JavaScript，也不需要安装额外插件。

完整默认值见 [site.json](../site.json)，暖色主题和简化浏览行为见 [site.custom.example.json](../site.custom.example.json)。后者使用虚构内容和已有演示素材；可以将需要的配置组复制到自己的 site.json，保留已有 id、姓名和内容字段。不要覆盖自己的 content.json 或素材。

## 兼容与配置合并

新增的 `theme`、`assets`、`sections`、`behavior`、`labels` 均可省略；配置组内也可只填需要覆盖的字段。省略字段使用内置默认值，旧版 site.json 仍能构建。配置不会自动回写；删除某个覆盖字段即可恢复默认。

这是数据格式 v1 的可选扩展，`schemaVersion` 仍为 1。顶层扩展元数据继续允许；**这五个配置组内只接受明确列出的字段**，拼写错误会报出具体路径。布尔值必须是 JSON 的 true / false，不能写成字符串。不使用 null 表示“默认”，应省略该字段。

例如，只关闭拼贴、关闭自动播放并修改一句页脚文案，将这些字段合并到现有 site.json：

```json
{
  "sections": {"collage": false},
  "behavior": {"liveAutoplay": false},
  "labels": {"footerMessage": "愿新的一年，也有很多小小的快乐。"}
}
```

以上是局部配置片段，不是包含全部必填字段的完整 site.json。

## theme：主要配色

颜色只接受六位十六进制 `#RRGGBB`，不能填任意 CSS。修改后在桌面和手机预览文字对比与排版。

| 字段 | 默认值 | 生效范围 |
| --- | --- | --- |
| background | `#e7eeed` | 页面、章节背景 |
| ink | `#315f69` | 主文字、信笺文字、主要按钮 |
| accent | `#7295a7` | 强调色变量与浏览器 theme-color |
| paper | `#f4f3ef` | 信纸、章节纸面与导航 |
| envelope | `#cbd6dc` | 信封和章节衬底 |

保留既有纸张纹理、阴影、局部渐变和答案对错颜色；这些不是全套任意视觉主题。图片中的颜色不会因 CSS 配色变化而自动重绘。字体、版式、布局顺序和动效关键帧仍由原有样式与脚本维护。

## assets：装饰资源

| 字段 | 默认值 | 用途 |
| --- | --- | --- |
| background | `assets/demo/sea.png` | 信封开场背景；空拼贴的占位引用 |
| motif | `assets/demo/botanical.svg` | 信笺图案和日期栏目装饰 |
| texture | `assets/demo/paper.png` | 信封、信纸纹理与加载准备 |
| motifAlt | `青绿色枝叶图案` | 信笺图案替代文字；纯装饰可填空字符串 |

资源文件必须位于 `dist/assets/`，路径写成相对 dist 的 `assets/...`，遵循 [通用路径规范](content-model.md#通用路径与文本)。路径存在性会在构建前检查，但文件的视觉质量、透明通道和素材权限需要使用者确认。使用浏览器支持的图像格式；不支持在这里填写外链或直接嵌入 HTML / SVG 代码。

## sections：栏目显示

`dates`、`collage`、`quiz` 都是布尔值，默认 true。false 会同时隐藏栏目和导航项，并从后台预加载清单中排除对应栏目。数据为空时，即使配置为 true，也会隐藏该栏目及导航。三项全关时保留信封与页脚，不会出现指向空栏目的导航。

开关不会删除 content.json 中的数据、dist 内的媒体或浏览器保存的进度。关闭栏目是展示设置，不是隐私控制；生成数据和部署目录仍可包含该栏目内容，公开部署后仍可被访问。重新开启时继续使用原有内容。

## behavior：浏览行为

| 字段 | 默认值 | 规则 |
| --- | --- | --- |
| persistProgress | true | false 时不读取或写入 localStorage；本次访问内仍可使用进度，刷新后重新开始，不删除旧记录 |
| liveAutoplay | true | false 时 Live 初始显示静帧，可手动播放；不改变普通视频控件或源媒体 |
| backgroundPreload | true | false 停止队列中的后台预加载；当前打开的图片、Live 和原图仍可按需加载 |
| openingMotion | `"auto"` | auto 遵循系统减少动态效果偏好；reduced 直接使用静态到达 / 展开状态，无强制等待，保留点击打开和进入按钮 |
| hintAfterAttempts | 2 | 0–10 的整数；达到失败次数后出现日期提示，0 表示关闭提示入口 |

系统“减少动态效果”仍优先于自动播放。关闭后台预加载并不意味着浏览器完全停止请求图片：开场资源、可见栏目图片、已打开的相册和浏览器自身的缓存请求仍属于正常浏览。日期提示仍采用年份与日历线索，不直接揭晓所有日期。

## labels：页面文案

`labels` 为部分覆盖对象。字段名和默认值见下表，也可直接在 site.json 或编辑器 Schema 提示中查找。空字符串表示保留元素但不显示文案；隐藏整个栏目应使用 sections。文字以纯文本处理，不执行 HTML、JavaScript 或 CSS。

`datesTitle`、`collageTitle`、`collageDescription`、`collageHelp`、`quizTitle` 支持用 JSON 的 `\n` 换行。其余字段以普通文本呈现，信笺行内文字建议保持简短。每项最多 500 字符，但上限不代表任何长度都有良好排版。

下列占位符会由页面或构建器替换。仅支持对应字段列出的名称，未知或未闭合花括号会在校验时报错；不支持任意表达式或 HTML：

| 字段 | 可用占位符 |
| --- | --- |
| datesSummary | `{dateCount}`、`{photoCount}` |
| dateCalendarLead | `{year}` |
| overviewOpen / quizSummary | `{count}` |
| quizWelcome / quizThanks | `{recipient}` |
| quizWrong / quizPendingAnswer | `{answer}`（A–D） |
| quizScore | `{score}`、`{total}` |

例如 `"quizThanks": "愿{recipient}的下一年更加精彩。"`。替换是一次性的纯文本插值，姓名中的特殊字符不会被当作模板再次解析。题干、选项、解析和照片说明继续在 content.json 中编辑。

这是一组常用展示文案配置，尚不是完整国际化系统：日历中文月份 / 星期、查看器加载错误、部分无障碍说明和工具提示仍使用现有中文。

| 字段 | 默认文案 |
| --- | --- |
| pageSuffix | 生日邀请函 |
| headerRight | WITH LOVE, ALWAYS |
| envelopeTop | Happy |
| envelopeBottom | birthday |
| letterLeftTop | A SEAT |
| letterLeftBottom | IN OUR |
| letterRightTop | SUMMER |
| letterRightBottom | STORY |
| birthdayLabel | 生日 |
| invitationLabel | 邀请函 |
| invitationEnglish | INVITATION |
| openingLoading | 海风捎来了一封信 |
| openingReady | 轻触信封，打开这份生日邀请 |
| openingOpened | 生日邀请函已展开 |
| enterButton | 走进这一年 |
| replayButton | 重读这封信 |
| navDates | 日期照片 |
| navCollage | 拼贴照片 |
| navQuiz | 趣味问答 |
| datesEyebrow | Remember the day? |
| datesTitle | 把日子拼起来，\n让回忆显影。 |
| datesDescription | 选取四个数字组成正确日期即可解锁当日回忆 |
| welcomeButton | 带我看一段回忆 |
| unlockedLabel | 段回忆已解锁 |
| datesSummary | {dateCount}个日期，{photoCount}个瞬间，等你逐一开启。 |
| hintButton | 给我提示 |
| unlockButton | 解锁这一天 |
| dateSelected | 选好日期后，试着解锁这一天。 |
| dateInvalid | 这个日期好像不成立，检查一下月份和天数吧。 |
| dateMissing | 这一天还没有照片，再想一个日子吧。 |
| dateUnlocked | 日期猜对了！这一天的照片，已经为你打开。 |
| dateWelcome | 先从这段回忆开始。其他日子，等你逐个解锁。 |
| dateReset | 重新选一个，值得被记住的日子。 |
| dateAllUnlocked | 所有日期都已解锁，点开下面的相册，再看一遍吧。 |
| dateCalendarLead | 按 {year} 年的日历想一想： |
| collageEyebrow | Pieces of you |
| collageTitle | 关于你的，\n每一小片。 |
| collageDescription | 把喜欢的瞬间，\n拼成一张独一无二的你。 |
| collageHelp | 左右滑动，或点击左右键翻看。\n轻触照片，放大看细节。 |
| overviewOpen | 查看全部 {count} 张 |
| overviewClose | 收起拼贴总览 |
| overviewNote | 按原有编号排列，轻触任意一张放大查看。 |
| progressSaved | 浏览进度保存在当前浏览器 |
| progressSession | 浏览进度仅在本次访问中保留 |
| progressUnavailable | 当前浏览器暂无法保存进度，本次浏览不受影响 |
| quizEyebrow | How well do you remember? |
| quizTitle | 这道题，\n你一定知道。 |
| quizLabel | 默契小测验 |
| quizWelcome | 关于{recipient}，你了解多少？ |
| quizSummary | 共 {count} 道题，来试试我们的默契。 |
| quizStart | 开始答题 |
| quizNext | 下一题 |
| quizSkip | 跳过，下一题 |
| quizResultButton | 看看结果 |
| quizRetry | 再玩一次 |
| quizCorrect | 答对啦！ |
| quizWrong | 这次的答案是 {answer}。 |
| quizPendingAnswer | 你选择了 {answer}，答案待揭晓。 |
| quizPendingImages | 头像图片待补充，这题先跳过。 |
| quizScore | 答对了 {score} / {total} 题 |
| quizComplete | 本轮问答已完成 |
| quizPartial | 图片或答案待补充的题目暂不计分。 |
| quizThanks | 谢谢你，陪我把这些瞬间再记了一遍。生日快乐，{recipient}！ |
| quizSavedSummary | 已保留这台设备上的答题进度。 |
| quizSavedResult | 查看上次结果 |
| quizContinue | 继续上次答题 |
| footerMessage | Happy birthday. |
| backToLetter | 回到这封信 |

## 验证与维护

```text
python validate_data.py
python build.py --check
python sync_config_schema.py --check
python -m pip install -r requirements-dev.txt
python -m unittest discover -s tests -v
npm ci
npx playwright install chromium
npm run test:browser
npm run test:configuration
```

配置测试在临时工程中验证自定义配色 / 素材 / 文案、栏目组合、静态开场、提示阈值、关闭存储、关闭预加载及手动 Live；不会把测试配置写回工作工程。输出截图保存在 `.local/`。

维护者在 configuration.py 修改默认值或配置约束后，运行 `python sync_config_schema.py` 更新 site.schema.json，并同步默认示例与本文。CI 会检查 Schema 与配置定义是否一致。运行时 config 由构建器生成；不要在 content.json 顶层用 `config`、`siteId`、`recipient`、`hintYear`、`welcomeDate` 或 `mediaVersion` 保存自定义数据，这些名称会被生成值覆盖。
