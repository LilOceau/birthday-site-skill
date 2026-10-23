# 从零创建完整工程

本 skill 的 `assets/project/` 是可独立运行的工程模板，自带虚构内容和完整交互。新建时优先运行附带初始化器，不从用户私人站点复制媒体、身份信息或部署设置。

```text
python <skill目录>/scripts/create_project.py <新目录> --recipient 小夏 --title "A day for you"
```

目录必须不存在；初始化器不会覆盖。它复制完整工程、分配独立进度 ID 并执行构建。进入新目录后执行 `python serve.py`。具体配置、导入、测试、恢复和部署步骤读取工程 [README](../assets/project/README.md)。素材都是可替换的示例，不能描述为用户真实回忆。

## 与已有旧版工程的区别

新工程以 site.json/content.json 为内容来源，build.py 生成 dist/index.html 和 dist/content.js。不要直接修改生成文件后期待下一次构建保留。dist 中其余源码和媒体仍需保留。

主题、装饰素材、栏目开关、常用文案及浏览行为按 [网站配置指南](../assets/project/docs/customization.md) 在 site.json 配置；使用部分覆盖，不改动 content.json 的素材和问答。配置变更要运行 `npm run test:configuration`，并预览实际文案、配色与栏目组合。

新工程照片导入必须带 --date，不存在全量重建或 --live-only 选项；输出到 assets/imported/，证据保存在 manifests/，修改前副本在 .backups/。原有项目可能使用不同脚本、目录和清单：不要将新模板覆盖到旧工程上。旧工程遵循 content-workflow.md，并先核对实际实现。

## 完成交付的证据

1. 按 [数据格式规范 v1](../assets/project/docs/content-model.md) 修改配置，运行 `python validate_data.py` 和 `python build.py --check`，检查格式、资源、相册关系和生成文件。
2. 安装 `requirements-dev.txt` 并执行 unittest；它验证 Schema 与运行时约束一致、非法配置不触发写入、增量导入不会改变其他内容、来源文件不变、编号冲突不会写入内容、备份存在、导出范围和视频 Range。
3. 执行 npm run test:browser，审阅桌面/手机尺寸截图；重大交互修改再补针对性检查。真实移动设备另行注明是否验证。
4. 说明预览地址和停止方式。用户有发布意图时按指定目标上传验收版本，不预置共享站点或声称日期解锁能保护隐私。

工程可在没有 Codex、MCP 或站点插件的情况下独立使用。用户只需构建和本地预览时，不要求登录任何服务。
