# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.1.3] - 2026-01-18

### Added

- 支持 Nacos 1.x/2.x/3.x 版本，按版本选择客户端实现
- 新增版本配置与端口环境变量说明，补充示例配置

### Changed

- 客户端实现拆分为多文件结构，便于维护扩展
- 默认使用 v3，v1/v2 需显式指定版本

## [0.1.0] - 2025-01-18

### Added

- Initial release
- 工具: `nacos_get_config` - 获取 Nacos 配置内容
- 工具: `nacos_publish_config` - 发布/更新 Nacos 配置
- 支持 Nacos 3.x 版本 (基于 3.1.0 Console API)
- 支持双端口设计 (API 8848 + Console 8080)
- 支持只读模式 (NACOS_READ_ONLY 环境变量)
- 支持 stdio 和 streamable_http 传输模式
- 支持 Markdown 和 JSON 响应格式
