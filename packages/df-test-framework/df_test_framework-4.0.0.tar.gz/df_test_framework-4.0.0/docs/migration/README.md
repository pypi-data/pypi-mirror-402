# 迁移指南

本文档提供 DF Test Framework 版本迁移的快速导航。

---

## 📖 可用的迁移指南

### 最新版本迁移

**[从 v3.x 迁移到 v4.0](v3-to-v4.md)** ⭐ 推荐

v4.0.0 是一个重大版本更新，引入了全面异步化特性：

- **异步 API**：AsyncHttpClient、AsyncDatabase、AsyncRedis、AsyncAppActions
- **性能提升**：2-30 倍性能提升
- **向后兼容**：同步 API 完全保留
- **平滑升级**：渐进式迁移路径

---

### 次版本迁移

**[从 v3.15 迁移到 v3.16](v3.15-to-v3.16.md)**

v3.16 版本的主要变更：
- 中间件系统重构
- 异步中间件支持
- 拦截器统一为中间件

---

## 🚀 快速开始

### 1. 确定当前版本

```bash
# 查看当前安装的版本
pip show df-test-framework | grep Version
```

### 2. 选择迁移路径

- **v3.15+ → v4.0**：查看 [v3-to-v4.md](v3-to-v4.md)
- **v3.15 → v3.16**：查看 [v3.15-to-v3.16.md](v3.15-to-v3.16.md)
- **更早版本**：建议先升级到 v3.15+，再迁移到 v4.0

### 3. 执行迁移

按照对应迁移指南的步骤逐步执行：
1. 备份当前代码
2. 更新依赖版本
3. 修改代码适配新 API
4. 运行测试验证
5. 逐步部署

---

## 🔗 相关资源

- [v4.0.0 发布说明](../releases/v4.0.0.md)
- [更新日志](../../CHANGELOG.md)
- [架构文档](../architecture/ARCHITECTURE_V4.0.md)
- [快速开始](../user-guide/QUICK_START.md)

---

## 🆘 获取帮助

如果在迁移过程中遇到问题：

1. 查看对应迁移指南的"常见问题"部分
2. 查看[故障排查指南](../troubleshooting/common-errors.md)
3. 查看[示例代码](../user-guide/examples.md)了解正确用法
4. 提交 [GitHub Issue](https://github.com/yourorg/test-framework/issues)

---

## 📝 历史版本迁移

如果你需要更早版本的迁移指南（v1.x、v2.x、v3.0-v3.14），这些文档已归档。
建议直接升级到最新版本，而不是逐个小版本迁移。

---

**返回**: [文档首页](../README.md)
