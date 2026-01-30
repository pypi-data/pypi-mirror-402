# PyPI 发布指南

## 前置准备

### 1. 注册 PyPI 账号

- **生产环境**: https://pypi.org/account/register/
- **测试环境**: https://test.pypi.org/account/register/

### 2. 创建 API Token

1. 登录 PyPI: https://pypi.org/manage/account/
2. 进入 "API tokens" 页面
3. 点击 "Add API token"
4. 设置 Token 名称 (如: `aigohotel-mcp-upload`)
5. 选择 Scope: "Entire account" 或指定项目
6. 复制生成的 Token (格式: `pypi-AgEIcHlwaS5vcmc...`)

### 3. 配置 PyPI 凭证

**方式1: 使用 .pypirc 文件 (推荐)**

创建/编辑文件: `~/.pypirc` (Linux/Mac) 或 `%USERPROFILE%\.pypirc` (Windows)

```ini
[distutils]
index-servers =
    pypi
    testpypi

[pypi]
username = __token__
password = pypi-AgEIcHlwaS5vcmc...

[testpypi]
repository = https://test.pypi.org/legacy/
username = __token__
password = pypi-AgEIcHlwaS5vcmc...
```

**方式2: 环境变量**

```bash
# Windows PowerShell
$env:TWINE_USERNAME="__token__"
$env:TWINE_PASSWORD="pypi-AgEIcHlwaS5vcmc..."

# Linux/Mac
export TWINE_USERNAME=__token__
export TWINE_PASSWORD=pypi-AgEIcHlwaS5vcmc...
```

## 发布步骤

### 步骤 1: 更新版本号

编辑 `pyproject.toml`:
```toml
[project]
version = "0.1.0"  # 修改为新版本号
```

版本号规范 (语义化版本):
- **0.1.0**: 初始版本
- **0.1.1**: Bug 修复
- **0.2.0**: 新功能
- **1.0.0**: 稳定版本

### 步骤 2: 更新项目元数据

编辑 `pyproject.toml` 中的作者信息:
```toml
authors = [
    {name = "Your Name", email = "your.email@example.com"}
]

[project.urls]
Homepage = "https://github.com/yourusername/aigohotel-mcp"
Repository = "https://github.com/yourusername/aigohotel-mcp"
```

### 步骤 3: 清理旧构建产物

```bash
# 进入项目目录
cd e:\Cursor\测试脚本File\aigohotel-mcp-uv

# 删除旧的构建文件
Remove-Item -Recurse -Force dist, build, *.egg-info -ErrorAction SilentlyContinue
```

### 步骤 4: 构建分发包

```bash
# 使用 uv 构建
uv build

# 或使用 build 工具
pip install build
python -m build
```

构建完成后会生成:
```
dist/
├── aigohotel_mcp-0.1.0-py3-none-any.whl  # Wheel 包
└── aigohotel_mcp-0.1.0.tar.gz            # 源码包
```

### 步骤 5: 检查包完整性

```bash
# 安装 twine
pip install twine

# 检查包
twine check dist/*
```

输出应该显示:
```
Checking dist/aigohotel_mcp-0.1.0-py3-none-any.whl: PASSED
Checking dist/aigohotel_mcp-0.1.0.tar.gz: PASSED
```

### 步骤 6: 上传到测试环境 (可选但推荐)

```bash
# 上传到 TestPyPI
twine upload --repository testpypi dist/*

# 测试安装
pip install --index-url https://test.pypi.org/simple/ aigohotel-mcp
```

### 步骤 7: 上传到生产环境

```bash
# 上传到 PyPI
twine upload dist/*
```

上传成功后会显示:
```
Uploading distributions to https://upload.pypi.org/legacy/
Uploading aigohotel_mcp-0.1.0-py3-none-any.whl
100% ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 
Uploading aigohotel_mcp-0.1.0.tar.gz
100% ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 

View at:
https://pypi.org/project/aigohotel-mcp/0.1.0/
```

## 验证发布

### 1. 检查 PyPI 页面

访问: https://pypi.org/project/aigohotel-mcp/

### 2. 测试安装

```bash
# 创建新的虚拟环境测试
python -m venv test_env
source test_env/bin/activate  # Windows: test_env\Scripts\activate

# 从 PyPI 安装
pip install aigohotel-mcp

# 验证安装
aigohotel-mcp --help
```

### 3. 测试 uvx 运行

```bash
uvx aigohotel-mcp
```

## 完整发布脚本

### Windows PowerShell

```powershell
# publish.ps1
$ErrorActionPreference = "Stop"

Write-Host "🚀 开始发布 aigohotel-mcp 到 PyPI..." -ForegroundColor Green

# 1. 清理旧构建
Write-Host "`n📦 清理旧构建产物..." -ForegroundColor Yellow
Remove-Item -Recurse -Force dist, build, *.egg-info -ErrorAction SilentlyContinue

# 2. 构建包
Write-Host "`n🔨 构建分发包..." -ForegroundColor Yellow
uv build

# 3. 检查包
Write-Host "`n✅ 检查包完整性..." -ForegroundColor Yellow
twine check dist/*

# 4. 上传到 TestPyPI (可选)
$testUpload = Read-Host "`n是否先上传到 TestPyPI 测试? (y/n)"
if ($testUpload -eq "y") {
    Write-Host "`n📤 上传到 TestPyPI..." -ForegroundColor Yellow
    twine upload --repository testpypi dist/*
    Write-Host "`n✅ TestPyPI 上传完成!" -ForegroundColor Green
    Write-Host "测试安装: pip install --index-url https://test.pypi.org/simple/ aigohotel-mcp" -ForegroundColor Cyan
    
    $continue = Read-Host "`n继续上传到生产环境? (y/n)"
    if ($continue -ne "y") {
        exit 0
    }
}

# 5. 上传到 PyPI
Write-Host "`n📤 上传到 PyPI..." -ForegroundColor Yellow
twine upload dist/*

Write-Host "`n🎉 发布成功!" -ForegroundColor Green
Write-Host "查看项目: https://pypi.org/project/aigohotel-mcp/" -ForegroundColor Cyan
```

### Linux/Mac Bash

```bash
#!/bin/bash
# publish.sh

set -e

echo "🚀 开始发布 aigohotel-mcp 到 PyPI..."

# 1. 清理旧构建
echo -e "\n📦 清理旧构建产物..."
rm -rf dist build *.egg-info

# 2. 构建包
echo -e "\n🔨 构建分发包..."
uv build

# 3. 检查包
echo -e "\n✅ 检查包完整性..."
twine check dist/*

# 4. 上传到 TestPyPI (可选)
read -p "是否先上传到 TestPyPI 测试? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo -e "\n📤 上传到 TestPyPI..."
    twine upload --repository testpypi dist/*
    echo -e "\n✅ TestPyPI 上传完成!"
    echo "测试安装: pip install --index-url https://test.pypi.org/simple/ aigohotel-mcp"
    
    read -p "继续上传到生产环境? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 0
    fi
fi

# 5. 上传到 PyPI
echo -e "\n📤 上传到 PyPI..."
twine upload dist/*

echo -e "\n🎉 发布成功!"
echo "查看项目: https://pypi.org/project/aigohotel-mcp/"
```

## 常见问题

### Q1: 包名已存在
**错误**: `The name 'aigohotel-mcp' is already taken`

**解决方案**:
1. 修改 `pyproject.toml` 中的 `name` 字段
2. 使用更具体的名称,如: `aigohotel-mcp-yourname`

### Q2: 版本号冲突
**错误**: `File already exists`

**解决方案**:
1. 增加版本号: `0.1.0` → `0.1.1`
2. PyPI 不允许覆盖已发布的版本

### Q3: 认证失败
**错误**: `Invalid or non-existent authentication information`

**解决方案**:
1. 检查 Token 是否正确
2. 确认 username 为 `__token__`
3. 重新生成 API Token

### Q4: README 渲染失败
**错误**: `The description failed to render`

**解决方案**:
1. 检查 README.md 语法
2. 确保使用标准 Markdown
3. 避免使用特殊扩展语法

## 更新已发布的包

```bash
# 1. 修改代码
# 2. 更新版本号 (pyproject.toml)
version = "0.1.1"

# 3. 重新构建和发布
rm -rf dist
uv build
twine check dist/*
twine upload dist/*
```

## 撤回发布

PyPI **不支持删除已发布的版本**,但可以:

1. **Yank (隐藏)**: 不推荐用户安装,但已安装的不受影响
   ```bash
   # 需要在 PyPI 网站操作
   # Project → Manage → Options → Yank release
   ```

2. **发布新版本**: 修复问题后发布新版本

## 相关链接

- [PyPI 官网](https://pypi.org/)
- [TestPyPI](https://test.pypi.org/)
- [Packaging Python Projects](https://packaging.python.org/tutorials/packaging-projects/)
- [Twine 文档](https://twine.readthedocs.io/)
- [UV 文档](https://docs.astral.sh/uv/)
