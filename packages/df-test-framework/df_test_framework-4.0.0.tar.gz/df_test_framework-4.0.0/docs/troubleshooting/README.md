# 故障排查指南

> **最后更新**: 2026-01-16
> **适用版本**: v3.0.0+（基础功能），v4.0.0+（包含异步支持）

本目录提供 DF Test Framework 的故障排查和调试资源。

---

## 📚 可用文档

### [常见错误与解决方案](common-errors.md)

列出使用框架时的常见错误及其解决方案，包括：

- **启动与配置错误**：Settings 配置、Bootstrap 初始化问题
- **连接与网络错误**：HTTP 请求、超时、连接池问题
- **数据库错误**：连接、事务、查询问题
- **Redis 错误**：连接、序列化问题
- **测试执行错误**：Fixture、依赖注入问题
- **扩展与插件错误**：插件加载、Hook 执行问题

**适用场景**：快速查找特定错误的解决方案

---

### [调试指南](debugging-guide.md)

详细的调试技巧和工具使用指南，包括：

- **日志调试**：配置日志级别、查看详细日志
- **断点调试**：使用 IDE 调试器、远程调试
- **性能分析**：识别性能瓶颈、优化建议
- **网络抓包**：查看 HTTP 请求/响应详情
- **数据库调试**：SQL 日志、查询分析
- **UI 测试调试**：截图、视频录制、Playwright Inspector

**适用场景**：深入分析和解决复杂问题

---

## 🔍 快速查找

### 按错误类型查找

| 错误类型 | 查看文档 |
|---------|---------|
| 配置错误 | [common-errors.md](common-errors.md#启动与配置错误) |
| HTTP 错误 | [common-errors.md](common-errors.md#连接与网络错误) |
| 数据库错误 | [common-errors.md](common-errors.md#数据库错误) |
| 测试执行错误 | [common-errors.md](common-errors.md#测试执行错误) |

### 按调试场景查找

| 调试场景 | 查看文档 |
|---------|---------|
| 查看详细日志 | [debugging-guide.md](debugging-guide.md) - 日志调试 |
| 性能问题 | [debugging-guide.md](debugging-guide.md) - 性能分析 |
| HTTP 请求问题 | [debugging-guide.md](debugging-guide.md) - 网络抓包 |
| UI 测试问题 | [debugging-guide.md](debugging-guide.md) - UI 测试调试 |

---

## 🆘 获取更多帮助

如果以上文档无法解决你的问题：

1. **查看示例代码**：[用户指南示例](../user-guide/examples.md)
2. **查看 API 文档**：[API 参考](../api-reference/README.md)
3. **提交 Issue**：[GitHub Issues](https://github.com/yourorg/test-framework/issues)
4. **查看更新日志**：[CHANGELOG.md](../../CHANGELOG.md) - 了解已知问题和修复

---

## 💡 最佳实践

- **启用详细日志**：在开发环境设置 `LOG_LEVEL=DEBUG`
- **使用断点调试**：IDE 调试器比 print 更高效
- **保留错误现场**：截图、日志、堆栈跟踪
- **隔离问题**：创建最小可复现示例
- **查看文档**：很多问题在文档中已有说明

---

**返回**：[文档首页](../README.md)
