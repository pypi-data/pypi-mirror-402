# 文档索引

Amazon 商品监控系统文档中心

---

## 快速导航

| 文档 | 说明 |
|------|------|
| [配置指南](CONFIGURATION.md) | 环境变量和系统配置详解 |
| [钉钉集成](DINGTALK.md) | 钉钉文档读取和通知配置 |
| [邮编功能](ZIP_CODE.md) | 多站点邮编自动设置指南 |
| [通知格式](NOTIFICATION.md) | 钉钉通知消息格式说明 |
| [优化说明](OPTIMIZATION.md) | DrissionPage 爬虫优化总结 |

---

## 文档概览

### [配置指南](CONFIGURATION.md)
- 运行模式配置（web/cli/scheduler）
- 店铺配置（SP-API 凭证）
- 钉钉机器人配置
- 钉钉文档配置
- 代理配置
- Chrome 浏览器配置
- 终端UI配置
- 配置验证方法

### [钉钉集成](DINGTALK.md)
- 创建钉钉应用
- 获取应用凭证和权限
- 配置钉钉文档
- API 使用方式
- 故障排除

### [邮编功能](ZIP_CODE.md)
- 支持的 Amazon 站点列表
- 自动邮编设置流程
- 加拿大站点特殊处理
- 故障排除和调试

### [通知格式](NOTIFICATION.md)
- 5 种通知类型示例
- @所有人触发条件
- Markdown 格式说明

### [优化说明](OPTIMIZATION.md)
- 浏览器初始化优化
- 选择器语法优化
- 多层次检测策略
- 智能异常分类系统
- 性能提升数据

---

## 快速开始

1. **安装依赖**
   ```bash
   pip install -r requirements.txt
   ```

2. **配置环境**
   ```bash
   copy .env-example .env
   # 编辑 .env 文件填入配置
   ```

3. **启动服务**
   ```bash
   # 推荐：使用统一入口
   python run.py

   # 或指定运行模式
   RUN_MODE=cli python run.py          # 单次执行
   RUN_MODE=scheduler python run.py    # 定时任务
   RUN_MODE=web python run.py          # Web服务
   ```

4. **访问 API 文档**
   ```
   http://localhost:8000/docs
   ```

---

## API 接口

| 接口 | 方法 | 说明 |
|------|------|------|
| `/get-all-product-urls` | POST | 从 SP-API 获取商品链接 |
| `/test-dingtalk` | GET | 测试钉钉文档连接 |
| `/process` | POST | 执行监控任务 |
| `/task/progress` | GET | 获取任务进度 |
| `/health` | GET | 健康检查 |

---

## 返回主文档

[返回项目 README](../README.md)
