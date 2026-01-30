# FastANP 模块化设计（第一版）

## 背景与目标
- FastANP 将作为独立可发布的 FastAPI 插件包，负责把 ANP 协议约束（ad.json、OpenRPC、DID-WBA 认证、JSON-RPC 分发）以“插件 + 胶水层”形式对外提供。
- 当前代码来自 `anp` 包内部实现，目录扁平、职责耦合，后续要像 FastMCP 一样支持多场景扩展、可插拔组件与清晰依赖。
- 因此第一步先确定模块化目录骨架，再逐步迁移具体代码，确保每个子包语义清晰。

## 目录结构
```
src/fastanp/
├── app/           # FastAPI 应用装配、运行入口、配置承载
├── interfaces/    # Interface 装饰器、OpenRPC 生成、JSON-RPC 分发、工具
├── context/       # Session / Context 模型、会话存储抽象
├── auth/          # DID-WBA 认证中间件、配置桥接（依赖 anp.authentication）
├── ad/            # Agent Description 生成器、Information 管理
├── utils/         # URL 规范化、类型解析、Docstring 解析等通用工具
├── models/        # Agent Description、OpenRPC 等 Pydantic 数据模型
├── examples/      # fastanp 独立示例与脚手架（后续迁移原 examples）
├── README.md      # fastanp 独立说明
└── DESIGN.md      # 本设计文档
```

## 设计理念与参考
1. **模块解耦**：对齐 FastMCP 的 `client/server/resources` 目录拆分，避免所有逻辑堆叠在单文件。每个子目录聚焦单一职责，便于替换实现或扩展特性。
2. **插件化主线**：`app/` 持有 FastAPI 应用装配逻辑，暴露统一的 Builder 接口，体现“FastAPI 主体 + FastANP 插件”的思想。
3. **协议驱动**：`interfaces/`、`ad/`、`models/` 集中处理 OpenRPC、ad.json、ANP 元数据，确保 fastanp 不持有具体业务协议实现，只提供协议描述和运行时支持。
4. **安全与上下文分层**：`auth/` 专注 DID-WBA 认证，`context/` 管 session/state，既能直接复用 anp.authentication 能力，又方便将来支持替代方案（如第三方身份或分布式 session）。
5. **演进式迁移**：本次仅创建结构与文档，后续将逐步把 `anp/fastanp` 里的文件迁入对应子目录，再补充测试与示例，保持可运行性。

## 下一步建议
- 制定迁移顺序（例如 context → auth → interfaces → ad → app），每次迁移配套单元测试。
- 在 `examples/` 中提供独立于 anp 仓库的演示脚本，验证新包的安装/运行路径。
- 结合 `pyproject.toml` 设计多包构建（fastanp 强依赖 anp），并输出升级指南。
