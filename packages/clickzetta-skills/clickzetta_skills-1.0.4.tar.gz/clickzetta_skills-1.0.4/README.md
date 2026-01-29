# Clickzetta Skills

Clickzetta 系统技能工具集 - 包含性能分析、诊断等专业工具的 Python 包。

## 包含的技能

### 1. Job Performance Analyzer (作业性能分析器)

自动诊断 Clickzetta Job 性能问题的工具，分析执行计划(plan.json)和运行概况(job_profile.json)，识别瓶颈并给出参数优化建议。

**命令**: `cz-analyze-job`

**支持场景**:
- 增量计算(REFRESH)
- AP模式
- GP模式
- Compaction
- 各类SQL场景

**已实现规则**:
- Stage/Operator 级别优化 (7条规则)
- 状态表优化 (6条规则)

### 2. SQL History Expert (SQL历史专家)

分析 SQL 执行历史，识别性能趋势和异常。

**命令**: `cz-sql-history`

### 3. Table Stats Expert (表统计专家)

分析表统计信息，提供优化建议。

**命令**: `cz-table-stats`

## 安装

### 使用 Makefile（推荐）

```bash
# 进入项目目录
cd cz_skills

# 安装
make install

# 开发模式安装（可编辑）
make install-dev

# 卸载
make uninstall
```

### 手动安装

```bash
# 构建
python3 -m build

# 安装
pip3 install dist/clickzetta_skills-*.whl
```

## 使用

### Job Performance Analyzer

```bash
# 分析性能问题
cz-analyze-job plan.json job_profile.json ./output

# 查看帮助
cz-analyze-job
```

### SQL History Expert

```bash
# 分析 SQL 历史
cz-sql-history <options>
```

### Table Stats Expert

```bash
# 分析表统计
cz-table-stats <options>
```

### 列出所有技能

```bash
make list-skills
```

## 开发

### 添加新技能

1. 在根目录下创建新的技能目录（使用连字符命名）
2. 实现技能逻辑
3. 在 `pyproject.toml` 的 `[project.scripts]` 中添加命令入口
4. 在 `[tool.hatch.build.targets.wheel]` 中添加包名和映射

示例结构：
```
cz_skills/
├── pyproject.toml
├── Makefile
├── README.md
├── job-performance-analyzer/      # 目录名用连字符
│   ├── __init__.py
│   ├── __main__.py               # 包含 main() 函数
│   └── ...
├── sql-history-expert/
│   ├── __init__.py
│   ├── __main__.py
│   └── ...
└── your-new-skill/               # 新技能
    ├── __init__.py
    ├── __main__.py
    └── ...
```

在 `pyproject.toml` 中添加：
```toml
[project.scripts]
cz-your-skill = "your_skill.__main__:main"

# Map the directory name (with hyphens) to the package name (with underscores)
[tool.hatch.build.targets.wheel.force-include]
"job-performance-analyzer" = "job_performance_analyzer"
"sql-history-expert" = "sql_history_expert"
"table-stats-expert" = "table_stats_expert"
"your-new-skill" = "your_skill"
```

**重要**:
- 目录名使用连字符 (`your-new-skill/`)
- Python 包名使用下划线 (`your_skill`)
- 通过 `force-include` 映射目录名到包名

### 运行测试

```bash
make test
```

### 构建发布

```bash
# 构建
make build

# 上传到 PyPI（需要配置 twine）
make upload
```

