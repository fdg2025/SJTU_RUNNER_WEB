# Cookie测试用例

## 用户提供的Cookie数据

根据你提供的Cookie表格数据，正确的Cookie应该是：

```
keepalive=ukjSa2ugfYYVbLgRl6ilvcBHc8AhWs27L5NKLaSyuhY=; JSESSIONID=5609c8d3-369f-4b29-9add-9ce40a064c69
```

## 问题分析

1. **keepalive值的问题**：
   - 原始值：`'ukjSa2ugfYYVbLgRl6ilvcBHc8AhWs27L5NKLaSyuhY=`
   - 问题：开头有一个单引号 `'`
   - 修复后：`ukjSa2ugfYYVbLgRl6ilvcBHc8AhWs27L5NKLaSyuhY=`

2. **JSESSIONID正常**：
   - 值：`5609c8d3-369f-4b29-9add-9ce40a064c69`

## 测试方法

### 方法1：直接使用修复后的Cookie
```
keepalive=ukjSa2ugfYYVbLgRl6ilvcBHc8AhWs27L5NKLaSyuhY=; JSESSIONID=5609c8d3-369f-4b29-9add-9ce40a064c69
```

### 方法2：使用表格数据测试智能解析
将以下内容粘贴到手动输入框中：
```
JSESSIONID	5609c8d3-369f-4b29-9add-9ce40a064c69	pe.sjtu.edu.cn	/	会话	46	✓	✓	Lax			Medium
keepalive	'ukjSa2ugfYYVbLgRl6ilvcBHc8AhWs27L5NKLaSyuhY=	pe.sjtu.edu.cn	/	会话	54	✓					Medium
```

### 方法3：使用改进的脚本
在交我跑网站控制台运行：
```javascript
// 在交我跑网站的控制台中运行此脚本
const keepalive = document.cookie.match(/keepalive=([^;]+)/)?.[1];
const jsessionid = document.cookie.match(/JSESSIONID=([^;]+)/)?.[1];
if (keepalive && jsessionid) {
  // 清理可能的引号
  const cleanKeepalive = keepalive.replace(/^['"]|['"]$/g, '');
  const cleanJsessionid = jsessionid.replace(/^['"]|['"]$/g, '');
  const cookie = `keepalive=${cleanKeepalive}; JSESSIONID=${cleanJsessionid}`;
  console.log('Cookie:', cookie);
  navigator.clipboard.writeText(cookie).then(() => {
    alert('Cookie已复制到剪贴板！\n格式: keepalive=' + cleanKeepalive.substring(0,20) + '...; JSESSIONID=' + cleanJsessionid);
  });
} else {
  alert('未找到所需的Cookie，请确保已登录\n当前Cookie: ' + document.cookie);
}
```

## 预期结果

所有方法都应该产生相同的最终Cookie：
```
keepalive=ukjSa2ugfYYVbLgRl6ilvcBHc8AhWs27L5NKLaSyuhY=; JSESSIONID=5609c8d3-369f-4b29-9add-9ce40a064c69
```

## 验证步骤

1. 使用任一方法获取Cookie
2. 检查格式是否正确
3. 确认keepalive值没有开头的单引号
4. 确认JSESSIONID值正确
5. 在工具中测试Cookie是否有效

