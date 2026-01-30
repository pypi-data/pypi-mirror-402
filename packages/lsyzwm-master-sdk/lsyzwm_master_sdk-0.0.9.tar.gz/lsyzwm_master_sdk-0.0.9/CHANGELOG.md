# Changelog

All notable changes to this project will be documented in this file.

## [0.0.9] - 2026-01-22

### Changed
- `_get_node_value` 方法返回值从 `Optional[str]` 改为 `tuple (value, stat)`，支持获取节点元数据
- `get_worker_instance_task`、`get_worker_cache_value`、`get_worker_instance_cache_value` 方法在返回 JSON 时自动注入 `_ctime` 字段（节点创建时间，毫秒级时间戳）

## [0.0.5] - 2026-01-05

### Added
- `create_cron_job_node` 方法：创建 cron 定时任务节点
- `create_interval_job_node` 方法：创建间隔任务节点
- `create_remove_job_node` 方法：创建移除作业节点
- 新增路径常量：`INTERVAL_JOBS_PATH`、`CRON_JOBS_PATH`、`REMOVE_JOBS_PATH`

### Changed
- `create_delay_job_node`、`create_cron_job_node`、`create_interval_job_node` 的节点路径简化，移除 worker_name 路径段

## [0.0.4] - 2025-12-26

### Added
- `get_worker_instances(worker_name)` 方法：获取指定 worker 的所有在线实例

### Changed
- `add_task_node` 方法：当 `worker_sid` 为空时，自动从已注册的 worker 实例中随机选择一个
  - 如果没有在线实例，默认使用 `{worker_name}-1`

### Removed
- 移除冗余的 `get_workers()` 方法（与 `get_registered_workers()` 功能重复）

## [0.0.3] - 2025-12-25

### Added
- 初始发布
- `MasterZooClient` ZooKeeper 客户端
- `MasterRpcClient` RPC 客户端
- Worker 注册与任务管理功能
- 缓存节点管理功能
- 延时任务节点支持
