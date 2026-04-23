# SelfMathAgent 🧮🤖

> **An AI-powered, hallucination-free tutor for absolute beginners in Mathematical Analysis & Higher Algebra.**
> 让零基础玩家告别低效的“刷视频”自学，通过“测试驱动”与“苏格拉底式启发”真正掌握数学分析与高等代数。

## ✨ 核心特性 (Core Features)

* 🗺️ **动态学习路径 (Dynamic To-Do List):** 基于预设的数学分析/高代知识图谱，通过摸底测验评估个人基础，自动生成闯关式的学习进度 To-Do List。
* 🗣️ **苏格拉底式辅导 (Socratic Tutoring Loop):** 基于 `LangGraph` 状态机构建。当用户做错题目时，Agent 不直接提供完整解析，而是提供分步提示（Scaffolding），引导用户主动思考。
* 🛡️ **告别数学幻觉 (Hallucination-Free with SymPy):** 内置基于 Python `SymPy` 的符号计算工具。对于用户提交的不等式放缩或代数变形，Agent 通过调用代码进行严格验证，而非依赖大模型的“语言直觉”，确保逻辑的绝对严谨。
* 🏗️ **专属新手训练营 (Scaffolding for Beginners):** 针对新手最头疼的 $\epsilon-N$ 语言、不等式构造等模块，设计专门的“拆解填空式”互动训练。
* 👁️ **自动化题库构建 (Vision OCR Pipeline):** 集成多模态大模型的批量离线 OCR 工具，能将海量 PDF 习题集自动清洗、结构化并存入本地数据库。

## 🛠️ 技术栈 (Tech Stack)

* **AI 编排框架:** `LangChain` & `LangGraph` (实现复杂的 Agent 状态机与流程控制)
* **后端服务:** `FastAPI` (提供高性能的异步 API 接口)
* **数学大脑:** Python `SymPy` (负责底层的符号计算与真值验证)
* **模型接入:** 云端多模态大模型 API (如 GPT-4o / Claude 3.5 Sonnet)
* **数据结构化:** `Pydantic` (强制约束 OCR 与大模型输出的标准 JSON 格式)

## 🗺️ 开发 TODOLIST

- [ ] **阶段一：MVP 核心闭环**
  - [ ] 手动构建包含 20 道基础题的结构化 JSON 测试题库。
  - [ ] 使用 `LangGraph` 编写核心循环图（出题节点 -> 校验节点 -> 提示节点）。
  - [ ] 基于 `FastAPI` 跑通基础的问答 API，验证对话上下文管理（Thread ID）。

- [ ] **阶段二：Agent 工具库扩充**
  - [ ] 封装 `sympy_calc` 验证工具，并将其注册为 Agent 可调用的 Tool。
  - [ ] 编写基于云端多模态 API 的离线 OCR 批处理脚本，打通题库录入流水线。
  - [ ] 引入轻量级向量数据库，实现基于知识点的相似题检索工具。

- [ ] **阶段三：前端交互与流式体验**
  - [ ] 开发本地 Web 界面，实现基础的用户交互逻辑。
  - [ ] 后端接入 WebSocket / SSE，向前端实时推送 Agent 调用工具的“思考状态”。
  - [ ] 前端集成 `MathJax` 或 `KaTeX`，完美渲染 Agent 输出的 LaTeX 数学公式。
