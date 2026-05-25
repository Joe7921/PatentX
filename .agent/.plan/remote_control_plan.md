# 宏观方向计划：iPhone 远程控制免安装 Web 控制台（方向二）

## 计划目标
在 Windows 宿主机上部署轻量化 RDP 网页代理 (Apache Guacamole) 与网页终端 (ttyd)，以便在 iPhone (iOS) 端利用 Safari 浏览器直接监控并安全操作运行在宿主机上的 Antigravity 2.0 Agent 服务与调试看板。

---

## 阶段一：Windows 本机环境准备与 ttyd 终端配置
1. **下载 ttyd**：
   - 编写 PowerShell 脚本自动从 `tsl0922/ttyd` GitHub Release 下载 Windows `ttyd.exe`。
   - 存放路径推荐：项目目录下的 `.agent/remote_config/bin/ttyd.exe`。
2. **编写启动脚本 `start_ttyd.ps1`**：
   - 使用 `-p 8080` 指定端口。
   - 使用 `-b <Tailscale_IP>` 绑定 Tailscale 的局域网网卡，防范公网未授权访问。
   - 使用 `-c username:password` 强制启用网页基本身份验证。
   - 默认命令设为 `powershell.exe`。

---

## 阶段二：使用 Docker 部署轻量化无数据库 Apache Guacamole
1. **目录结构设计**：
   在 `.agent/remote_config/` 下创建 `guacamole/` 文件夹。
2. **编写连接配置文件 `user-mapping.xml`**：
   - 定义用户认证：包含登录 Web 控制台的账号密码。
   - 配置 RDP 协议连接到 Windows 宿主机的 Tailscale IP、3389 端口、以及 Windows 登录凭证（可使用临时占位符让用户后续替换，防止敏感密码直接硬编码）。
3. **编写 `docker-compose.yml`**：
   - 包含 `guacd` 和 `guacamole` 服务。
   - 将宿主机上的 `user-mapping.xml` 映射进容器 `/etc/guacamole/user-mapping.xml`。
   - 端口映射：将主机的 `8082` 映射到容器的 `8080`。

---

## 阶段三：调试看板的外网绑定与联调
1. **修改 Vite 启动配置**：
   - 修改 `vite.config.js` 允许所有网卡监听，或者修改 `package.json` 中的启动命令加上 `--host`。
2. **联调验证**：
   - 在 iPhone Safari 上分别访问：
     - Web 终端：`http://<Tailscale_IP>:8080`
     - 网页远程桌面：`http://<Tailscale_IP>:8082/guacamole/`
     - Vite 调试看板：`http://<Tailscale_IP>:5173`

---

## 阶段四：高价值优化扩展（根据反馈按需部署）
1. **Caddy 统一入口与 TLS（首选）**：
   - 部署 Caddy 容器，自动申请 Tailscale TLS 证书。
   - 使用反向代理实现统一域名和子路径访问（`/terminal` -> `ttyd:8080`, `/desktop` -> `guacamole:8080/guacamole/`）。
2. **NSSM 系统服务注册**：
   - 使用 NSSM 自动将 ttyd 和 Docker Compose 服务注册为 Windows 启动项。
