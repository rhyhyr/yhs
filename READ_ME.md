# 생성형 AI로 작성하였습니다.

# 🎓 AI 기반 유학생 행정 절차 안내 서비스

## 📌 Overview
본 프로젝트는 유학생이 겪는 행정 및 생활 문제를 해결하기 위해  
RAG 기반 AI를 활용하여 **개인 상황에 맞는 절차 중심 가이드**를 제공하는 서비스입니다.

---

## 🎯 Key Features

### 1. Context-aware Query Processing
사용자의 국적, 학교, 비자 정보를 기반으로 질의를 해석

### 2. Adaptive Multi-Path RAG
질문 난이도 및 신뢰도에 따라  
Fast / Deep / Crawling 경로를 선택하는 다단계 탐색 구조

### 3. Action Guide Generation
단순 정보 제공이 아닌  
실제 행동으로 이어지는 절차형 가이드 제공

### 4. Channel-based Knowledge Structuring
질문을 자동 분류하여 채널 단위로 지식 축적

---

## 🧠 System Architecture
User Query
↓
Context Processing
↓
RAG Pipeline
(Fast → Deep → Crawling)
↓
Answer + Action Guide


---

## 👤 Target Users

- 한국 거주 유학생
- 행정 절차에 어려움을 겪는 사용자
- 한국어 정보 이해가 어려운 사용자

---

## 🚀 Tech Stack

- Frontend: (예: React)
- Backend: (예: Node.js / FastAPI)
- Database: Neo4j, Vector DB
- AI: OpenAI API (LLM), Embedding
- Crawling: Playwright

---

## 📊 Project Goal

- 정보 제공 → 행동 유도 구조 설계
- 유학생 문제 해결 중심 서비스 구축
- 실제 사용자 기반 반복 개선 (Agile)

---

## 🛠 Installation

```bash
git clone https://github.com/your-repo.git
cd project
npm install
npm run dev
