# 安全政策

## 报告漏洞

发现安全问题请通过 GitHub 仓库的 Security 标签页提交私密报告（Security Advisories），
或直接联系维护者。不要在公开 Issue 中贴出漏洞细节、复现步骤或凭据。

报告里请包含：

- 受影响的文件与行号
- 问题成因与影响范围
- 复现步骤或最小验证代码

确认后会尽快发布修复版本。

## 配置与凭据

本插件的真实配置 `config.toml` 已在 `.gitignore` 中排除，不会被提交。
如果 fork 或部署时修改了忽略规则，请确认密钥类字段不进入版本库：

```
git status --short
git log -S "sk-" --oneline
```

`.gitignore` 只对未跟踪文件生效。已经提交过的配置需要 `git rm --cached` 才能真正移除。
