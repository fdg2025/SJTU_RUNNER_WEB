# Cookie获取完全指南

## 🎯 三种获取方式

### 方式一：智能检测（推荐）⭐

**最简单的方式，无需任何技术知识**

1. **点击"一键获取"按钮**
2. **选择"智能检测"**
3. **按照提示操作**：
   - 打开交我跑网站并登录
   - 按F12打开开发者工具
   - 找到Cookie并复制
   - 系统自动检测并提取

**优点**：全自动，无需手动输入

### 方式二：一键脚本（高效）🚀

**适合熟悉浏览器控制台的用户**

1. **点击"复制脚本"按钮**
2. **打开交我跑网站并登录**
3. **按F12打开控制台**
4. **粘贴脚本并回车**
5. **Cookie自动复制到剪贴板**

**优点**：一步到位，自动复制

### 方式三：手动输入（传统）📝

**最传统的方式，适合所有情况**

1. **打开交我跑网站并登录**
2. **按F12 → 应用程序 → Cookie**
3. **手动复制keepalive和JSESSIONID**
4. **粘贴到输入框中**

**优点**：兼容性最好，适用所有浏览器

## 📋 详细步骤说明

### 第一步：登录交我跑网站

1. **访问网站**：https://pe.sjtu.edu.cn/phone/#/indexPortrait
2. **使用JAccount登录**
3. **确保登录成功**（看到个人信息页面）

### 第二步：打开开发者工具

**Chrome/Edge浏览器**：
- 按 `F12` 键
- 或右键页面 → "检查"
- 或菜单 → 更多工具 → 开发者工具

**Firefox浏览器**：
- 按 `F12` 键
- 或右键页面 → "检查元素"

**Safari浏览器**：
- 先启用开发菜单：偏好设置 → 高级 → 显示开发菜单
- 然后：开发 → 显示Web检查器

### 第三步：找到Cookie

1. **切换到"应用程序"标签**（Chrome）或"存储"标签（Firefox）
2. **在左侧找到"Cookie"**
3. **点击展开 → 选择"https://pe.sjtu.edu.cn"**
4. **找到以下两个Cookie**：
   - `keepalive`
   - `JSESSIONID`

### 第四步：复制Cookie值

**方法A：逐个复制**
1. 点击`keepalive`，复制其"值"
2. 点击`JSESSIONID`，复制其"值"
3. 按格式组合：`keepalive=值1; JSESSIONID=值2`

**方法B：使用脚本（推荐）**
1. 切换到"控制台"标签
2. 粘贴以下脚本并回车：
```javascript
const keepalive = document.cookie.match(/keepalive=([^;]+)/)?.[1];
const jsessionid = document.cookie.match(/JSESSIONID=([^;]+)/)?.[1];
if (keepalive && jsessionid) {
  const cookie = `keepalive=${keepalive}; JSESSIONID=${jsessionid}`;
  console.log('Cookie:', cookie);
  navigator.clipboard.writeText(cookie).then(() => {
    alert('Cookie已复制到剪贴板！');
  });
} else {
  alert('未找到所需的Cookie，请确保已登录');
}
```

## 🔍 Cookie格式说明

### 正确格式
```
keepalive=ukjSa2ugfYYVbLgRl6ilvcBHc8AhWs27L5NKLaSyuhY=; JSESSIONID=708c40a4-3441-4443-a543-92f968e1df44
```

### 格式要求
- 必须包含 `keepalive=` 和 `JSESSIONID=`
- 两个值之间用 `; ` 分隔（分号+空格）
- 不要包含其他Cookie值
- 不要有多余的空格或换行

### 常见错误格式
```
❌ keepalive=xxx JSESSIONID=xxx          # 缺少分号
❌ keepalive=xxx;JSESSIONID=xxx          # 分号后缺少空格
❌ keepalive=xxx; JSESSIONID=xxx; other=xxx  # 包含多余Cookie
```

## 🛠️ 故障排除

### 问题1：找不到Cookie
**原因**：未正确登录或Cookie已过期
**解决**：
1. 确认已成功登录交我跑网站
2. 刷新页面重新登录
3. 检查是否在正确的域名下查看Cookie

### 问题2：Cookie格式错误
**原因**：复制时包含了多余内容或格式不正确
**解决**：
1. 使用提供的脚本自动提取
2. 检查格式是否符合要求
3. 确保只包含keepalive和JSESSIONID

### 问题3：智能检测失败
**原因**：浏览器不支持剪贴板API或权限被拒绝
**解决**：
1. 允许网站访问剪贴板权限
2. 使用手动输入方式
3. 尝试使用一键脚本方式

### 问题4：Cookie很快失效
**原因**：SJTU网站的Cookie有时效性
**解决**：
1. 获取Cookie后尽快使用
2. 如果失效，重新获取新的Cookie
3. 保持交我跑网站标签页打开状态

## 💡 使用技巧

### 技巧1：保持登录状态
- 获取Cookie期间不要关闭交我跑网站标签页
- 不要在其他设备上登录同一账号

### 技巧2：快速获取
- 使用"一键脚本"方式最快
- 将脚本保存为书签，下次直接点击

### 技巧3：验证Cookie
- 获取后立即在工具中测试
- 如果提示Cookie无效，重新获取

### 技巧4：批量处理
- 如果需要为多个账号获取Cookie
- 可以使用无痕模式分别登录获取

## 🔒 安全提醒

1. **不要分享Cookie**：Cookie相当于登录凭证
2. **定期更新**：Cookie会过期，需要定期重新获取
3. **安全环境**：在可信的设备和网络环境下操作
4. **及时使用**：获取后尽快使用，避免长时间存储

## 📞 获取帮助

如果按照指南仍然无法获取Cookie：

1. **检查浏览器版本**：确保使用最新版本
2. **尝试不同方式**：三种方式任选其一
3. **查看错误信息**：注意工具给出的具体错误提示
4. **联系技术支持**：提供详细的错误截图和描述
