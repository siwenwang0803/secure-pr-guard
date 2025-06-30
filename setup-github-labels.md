# GitHub Repository Labels 设置

## 🏷️ 自动标签配置

为了让auto-label workflow正常工作，需要在GitHub repository中预先创建这些labels。

## 📋 必需的Labels

### 1. bot/github-app-tested
- **颜色**: `#0e8a16` (绿色)
- **描述**: `Automatically tested by GitHub App workflow`
- **用途**: 标识PR已通过GitHub App自动化测试

### 2. security/analyzed  
- **颜色**: `#b60205` (红色)
- **描述**: `Security analysis completed by AI agents`
- **用途**: 标识PR已完成安全分析

### 3. automated
- **颜色**: `#1d76db` (蓝色) 
- **描述**: `Automated processing completed`
- **用途**: 通用自动化处理标记

## 🔧 设置步骤

### 方法1: GitHub Web UI
1. 进入你的repository
2. 点击 **Issues** 或 **Pull requests** tab
3. 点击 **Labels** 按钮
4. 点击 **New label** 
5. 逐个创建上述labels

### 方法2: GitHub CLI (推荐)
```bash
# 安装GitHub CLI (如果未安装)
brew install gh  # macOS
# or
sudo apt install gh  # Ubuntu

# 认证
gh auth login

# 创建labels
gh label create "bot/github-app-tested" --color "0e8a16" --description "Automatically tested by GitHub App workflow"

gh label create "security/analyzed" --color "b60205" --description "Security analysis completed by AI agents"  

gh label create "automated" --color "1d76db" --description "Automated processing completed"
```

### 方法3: API方式
```bash
# 设置变量
REPO="owner/repo"  # 替换为你的repository
TOKEN="your_github_token"

# 创建labels
curl -X POST \
  -H "Authorization: token $TOKEN" \
  -H "Accept: application/vnd.github.v3+json" \
  https://api.github.com/repos/$REPO/labels \
  -d '{
    "name": "bot/github-app-tested",
    "color": "0e8a16", 
    "description": "Automatically tested by GitHub App workflow"
  }'

curl -X POST \
  -H "Authorization: token $TOKEN" \
  -H "Accept: application/vnd.github.v3+json" \
  https://api.github.com/repos/$REPO/labels \
  -d '{
    "name": "security/analyzed",
    "color": "b60205",
    "description": "Security analysis completed by AI agents"  
  }'

curl -X POST \
  -H "Authorization: token $TOKEN" \
  -H "Accept: application/vnd.github.v3+json" \
  https://api.github.com/repos/$REPO/labels \
  -d '{
    "name": "automated", 
    "color": "1d76db",
    "description": "Automated processing completed"
  }'
```

## 📊 Label 颜色参考

### GitHub Label Colors
- 🟢 **绿色** (`0e8a16`): 成功、通过、完成
- 🔴 **红色** (`b60205`): 安全、重要、需要注意  
- 🔵 **蓝色** (`1d76db`): 自动化、工具、系统
- 🟡 **黄色** (`fbca04`): 警告、待处理
- 🟣 **紫色** (`5319e7`): 功能、增强
- 🟠 **橙色** (`ff9500`): 优先级、修复

## ✅ 验证Labels

创建labels后，可以通过以下方式验证:

```bash
# 列出所有labels
gh label list

# 或者API方式
curl -H "Authorization: token $TOKEN" \
     https://api.github.com/repos/$REPO/labels
```

## 🔄 Auto-label工作流测试

Labels创建后，可以测试workflow:

1. 创建一个test PR
2. 检查 **Actions** tab中的workflow运行状态
3. 确认PR被自动添加了3个labels
4. 检查labels的颜色和描述是否正确

## 🎨 视觉效果预览

创建后的labels在PR中会显示为:
- 🟢 `bot/github-app-tested` - 绿色背景
- 🔴 `security/analyzed` - 红色背景  
- 🔵 `automated` - 蓝色背景

## 📝 注意事项

1. **Label名称大小写敏感**: 确保与workflow中的名称完全匹配
2. **颜色格式**: 使用6位十六进制代码，不包含#符号
3. **权限要求**: 需要repository的admin权限才能创建labels
4. **批量创建**: 对于多个repositories，建议使用脚本批量创建

---

**完成后，你的GitHub App workflow就能自动为PRs添加这些彩色标签了！** 🎉 