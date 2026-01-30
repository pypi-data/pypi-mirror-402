# iOS Unit Test Generator

智能 MCP 服务器，自动生成、编译、运行和修复 iOS 单元测试。

## 🚀 快速开始（推荐使用 uvx）

**无需拉取代码，直接在 VS Code 中配置即可使用！**

### 方式一：VS Code MCP 配置（推荐）

在 VS Code 设置中添加 MCP 服务器配置：

**macOS/Linux** - 编辑 `~/.vscode/mcp.json`:
```json
{
  "servers": {
    "ios-unittest-generator": {
      "command": "uvx",
      "args": ["ios-unittest-generator"],
      "env": {
        "CHROMIUM_SRC": "/path/to/chromium/src"
      }
    }
  }
}
```

**Windows** - 编辑 `%APPDATA%\Code\User\mcp.json`:
```json
{
  "servers": {
    "ios-unittest-generator": {
      "command": "uvx",
      "args": ["ios-unittest-generator"],
      "env": {
        "CHROMIUM_SRC": "C:\\path\\to\\chromium\\src"
      }
    }
  }
}
```

### 方式二：命令行运行

```bash
# 直接运行（无需安装）
uvx ios-unittest-generator

# 或者先安装再运行
pip install ios-unittest-generator
ios-unittest-generator
```

## 📋 核心功能

- ✅ 自动分析源文件，识别可测试元素
- ✅ 生成完整的测试文件（包含 fixture、SetUp、测试用例）
- ✅ 智能检测测试目标（支持 `ios/chrome/*`、`components/*/ios/*` 等所有路径）
- ✅ 自动更新 BUILD.gn 文件（按字母顺序）
- ✅ 自动编译测试，智能分析编译错误
- ✅ 自动运行测试，智能分析运行时错误

## 📖 11 个 MCP 工具

| 工具 | 功能 |
|------|------|
| `full_test_workflow` | 完整工作流（分析→生成→增强→编译→运行） |
| `analyze_ios_code_for_testing` | 分析源文件，提取可测试元素 |
| `generate_ios_unittest_file` | 生成测试文件 |
| `check_ios_test_coverage` | 检查测试覆盖率 |
| `verify_test_enhancement_complete` | 验证测试增强完成（质量门控） |
| `compile_ios_unittest` | 编译测试（自动错误分析） |
| `run_ios_unittest` | 运行测试（自动错误分析） |
| `analyze_runtime_errors` | 分析运行时错误 |
| `analyze_compilation_errors` | 分析编译错误 |
| `update_existing_tests` | 增量更新测试 |
| `update_build_file_for_test` | 自动更新 BUILD 文件 |

## 💡 使用示例

```bash
# 一键生成完整测试
Use full_test_workflow for ios/chrome/browser/ui/foo.mm

# 单独编译
Use compile_ios_unittest for ios/chrome/browser/ui/foo.mm

# 单独运行
Use run_ios_unittest with filter FooTest.*
```

## 🔧 环境变量

| 变量 | 描述 | 示例 |
|------|------|------|
| `CHROMIUM_SRC` | Chromium 源码根目录 | `/Users/user/chromium/src` |

## 📦 发布到 PyPI

```bash
# 构建
python -m build

# 上传到 PyPI
twine upload dist/*

# 上传到 TestPyPI（测试）
twine upload --repository testpypi dist/*
```

---

**版本**: v4.19.0  
**更新日期**: 2026-01-22
