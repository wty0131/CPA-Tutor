# CPA Tutor — 注册会计师考试助手

基于 **FastAPI + React + DeepSeek AI** 的 CPA 考试智能备考系统，覆盖注册会计师全部六科。

## 功能特性

| 功能 | 说明 |
|------|------|
| **六科全覆盖** | 会计、审计、财务成本管理、税法、经济法、公司战略与风险管理 |
| **AI 智能出题** | DeepSeek 自动生成高质量 CPA 考题，涵盖单选/多选/计算三种题型 |
| **AI 深度解析** | 每道题附带详细解析，自动标注关联知识点 |
| **模拟考试** | 定时计分考试模式（单选15+多选5+计算5），成绩报告 + 薄弱点分析 |
| **错题本** | SM-2 间隔复习算法，按记忆曲线安排复习时间 |
| **知识点归纳** | AI 生成知识点总结，包含核心概念、常见错误、备考建议 |
| **题库爬取** | 可扩展的爬虫框架，支持从公开题库网站抓取题目 |

## 技术栈

| 层 | 技术 |
|---|------|
| 后端 | Python FastAPI + SQLAlchemy + SQLite |
| 前端 | React + TypeScript + Vite + Ant Design |
| AI | DeepSeek API（OpenAI 兼容） |
| 爬虫 | httpx + BeautifulSoup |


```

├── backend/
│   ├── main.py                 # FastAPI 入口
│   ├── config.yaml             # 配置文件
│   ├── core/                   # AI客户端、数据库、ORM模型
│   ├── api/                    # REST API 路由（7个模块）
│   ├── scraper/                # 爬虫框架（基类 + 注册表）
│   └── services/               # AI解析、知识点、调度服务
├── frontend/
│   └── src/
│       ├── api/                # API 请求封装
│       └── pages/              # 页面组件（7个）
├── start.bat                   # Windows 一键启动脚本
└── README.md
```

## 快速开始

### 1. 环境要求

- Python 3.10+
- Node.js 18+
- DeepSeek API Key（[获取地址](https://platform.deepseek.com)）

### 2. 安装依赖

```bash
# 后端
cd backend
pip install fastapi uvicorn sqlalchemy pyyaml httpx beautifulsoup4 lxml openai

# 前端
cd frontend
npm install
```

### 3. 配置 API Key

```bash
# Windows
set DEEPSEEK_API_KEY=sk-your-key-here

# macOS / Linux
export DEEPSEEK_API_KEY=sk-your-key-here
```

或直接编辑 `backend/config.yaml` 中的 `api_key` 字段。

### 4. 启动

**方式一：一键启动（Windows）**
双击 `start.bat`

**方式二：手动启动**
```bash
# 终端1：后端
cd backend
python -m uvicorn main:app --host 127.0.0.1 --port 8000

# 终端2：前端
cd frontend
npm run dev
```

浏览器访问 `http://localhost:5173`

### 5. 生成题目

```bash
cd backend
PYTHONPATH=. python generate_questions.py
```

## API 文档

启动后端后访问 `http://localhost:8000/docs` 查看 Swagger 文档。

| 端点 | 说明 |
|------|------|
| `GET /api/subjects` | 六科列表及统计 |
| `GET /api/questions` | 题目查询（支持科目/知识点/难度/题型过滤） |
| `POST /api/practice/submit` | 提交答案 → 判断正误 + AI 解析 |
| `GET /api/wrongbook` | 错题本列表 |
| `POST /api/wrongbook/:id/review` | SM-2 复习打分 |
| `GET /api/knowledge-points` | 知识点树 |
| `POST /api/knowledge-points/:id/summarize` | AI 知识点归纳 |
| `POST /api/exam/generate` | 生成模拟试卷 |
| `POST /api/exam/submit` | 交卷 → 成绩报告 + 薄弱分析 |
| `POST /api/scraper/trigger` | 手动触发爬取 |

## 扩展爬虫

在 `backend/scraper/sites/` 下创建新爬虫，继承 `BaseScraper`：

```python
from scraper.base import BaseScraper, ScrapedQuestion

class MyScraper(BaseScraper):
    site_name = "example_cpa_bank"

    def scrape(self, subject_code: str | None = None) -> list[ScrapedQuestion]:
        # 解析网站，返回题目列表
        soup = self.fetch_page("https://example.com/questions")
        # ...
        return questions
```

## License

MIT
