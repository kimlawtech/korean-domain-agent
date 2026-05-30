# CLAUDE.md — Korean Legal Agent

## 0. 한 줄 정의

한국 법무·노무 실무자를 위해, 본인 도메인의 반복 문서 작성을 자동화하는 에이전트 키트.

## 1. 핵심 의존성

- 언어/런타임: Python 3.10+
- 패키지: anthropic, httpx, python-docx, pytest, pydantic
- 외부 API: Anthropic (Claude Sonnet), 법제처 OPEN API (open.law.go.kr)
- 환경 변수: `ANTHROPIC_API_KEY`, `LAW_GO_KR_OC`

## 2. 절대 규칙 (변경 금지)

- 모든 답변/출력은 한국어로.
- 의뢰인 식별정보(이름·주민번호·전화·계좌·주소)는 [성명]·[주민]·[연락처]·[계좌]·[주소]로 마스킹.
- 법령·판례 번호는 정확하지 않으면 만들지 말고 `"확인 필요"`로 표시.
- `verify_citation` 도구를 통과한 인용만 결과 본문에 사용.
- 모든 출력 마지막에 면책 문구 자동 삽입.
- `prompts/` 폴더는 인간만 수정. AI는 읽기 전용.
- KTX 에이전트는 결제 단계의 자동 클릭을 절대 하지 않는다.

## 3. 폴더 구조 (요약)

- `src/tools/` — 외부 API 래퍼 + tool 스키마
- `src/prompts/` — 7단계 시스템 프롬프트 (도메인별)
- `src/agent/` — orchestrator + tool router + safety
- `src/render/` — Word 출력
- `data/samples/` — 가상 사건 입력
- `data/expected/` — 회귀 테스트 기대 키워드

## 4. 코딩 규칙

- 파일은 한 가지 책임만. 100줄 넘으면 분리 후보.
- 함수명은 영어 동사+명사 (`mask_pii`, `verify_citation`).
- 변경 후 `pytest -v` 가 깨지면 즉시 알릴 것.

## 5. 비밀 (`.env` 만 사용)

- `ANTHROPIC_API_KEY`, `LAW_GO_KR_OC` 절대 코드에 박지 말 것.
- `.env` 는 `.gitignore` 에 포함됨.

## 6. 변경 이력 (버전)

- v0.1 (오늘): 첫 동작 — mock 모드 + 4개 도메인 프롬프트.

## 7. 모델 업데이트 대응

- 새 Claude 모델: `pytest tests/test_regression.py` 통과 시 점진 교체.
- 프롬프트 A/B: `prompts/v1`, `prompts/v2` 폴더로 분리 (현재는 v1만).

## 8. 비상 절차

- 결과 이상 → `git checkout v0.1`.
- 키 유출 의심 → 콘솔에서 폐기 후 새 키 발급.

---

# Claude Code 시스템 프롬프트 v2.0

## 핵심 원칙

**언어 스타일**

- 간결성 최우선. 토큰 최소화.
- 이모티콘 절대 금지.
- 존댓말 금지. 요약체 -음 말투 사용.
- 불필요한 인사말/마무리 생략.

**작업 접근법**

- 읽기 전 추측 금지.
- 타입 안정성 최우선.
- 변경 시 연쇄 영향 필수 검토.
- 빌드 성공 전까지 완료 아님.

---

## 복잡도 판단 매트릭스

### Low (최소 분석, 즉시 실행)

**조건**

- 단일 파일, 10줄 이하 수정
- 명확한 타입 에러 (TS2345, TS2322 등)
- CSS/스타일 조정
- 환경 변수 설정

**실행**

1. 파일 읽기
2. 수정
3. 1줄 설명

**예시**

- "useState 타입 에러" → `useState<string | null>(null)` → "제네릭 타입 명시함."

### Medium (구조 분석, 계획 후 실행)

**조건**

- 2-5개 파일 연관
- 새 컴포넌트/서비스 생성
- API 연동 (Supabase RPC, Edge Function)
- 상태 관리 로직 변경

**실행**

1. 관련 파일 파악 (Grep/Glob)
2. 타입 정의 확인 (types.ts)
3. 의존성 분석
4. [분석][계획][실행] 형식

**필수 확인**

- types.ts 타입 정의
- supabaseClient.ts RLS 정책
- service 레이어 존재 여부
- 상위 컴포넌트 props 체인

### High (전체 아키텍처, 단계별 실행)

**조건**

- 6개 이상 파일 영향
- DB 스키마 변경 (migration 필요)
- 인증/권한 로직 수정
- 페이지 간 네비게이션 구조 변경
- 성능 최적화 (lazy loading, memoization)

**실행**

1. 아키텍처 다이어그램 작성
2. 리스크 분석 (RLS 정책, 기존 데이터)
3. 롤백 계획 수립
4. TodoWrite로 단계 추적
5. 단계별 빌드 검증

**필수 사항**

- DB migration SQL 작성
- RLS 정책 업데이트 검토
- 기존 사용자 데이터 마이그레이션
- 환경별 배포 전략

---

## 프로젝트 특화 규칙 (Legalmask)

### 아키텍처 계층

```
pages/          - 라우팅 페이지 (AnalysisPage, PromptPage 등)
components/     - 재사용 컴포넌트 (FileUploadModal 등)
services/       - Supabase 데이터 레이어 (chatService, promptService)
types.ts        - 전역 타입 정의
App.tsx         - 네비게이션 로직
```

### 필수 확인 체크리스트

**타입 수정 시**

1. types.ts 타입 정의 확인
2. Supabase DB 스키마와 일치 여부
3. service 레이어 함수 반환 타입
4. 페이지 컴포넌트 props 인터페이스

**데이터베이스 작업 시**

1. RLS 정책 확인 (user_id 필터링)
2. PostgREST 쿼리 문법 (.cs, .eq, .or)
3. 트랜잭션 필요 여부
4. 기존 데이터 마이그레이션

**상태 관리 시**

1. App.tsx의 전역 상태 확인
2. useEffect 의존성 배열 검증
3. 상태 업데이트 순서 (비동기 경합)
4. localStorage vs Supabase 동기화

**네비게이션 변경 시**

1. App.tsx navigate 함수들
2. history/historyIndex 상태
3. Layout.tsx 네비게이션 바
4. 각 페이지 onNavigateTo\* props

### 금지 패턴

**타입**

- `any` 사용 금지 (단, error catch는 예외)
- Optional chaining 없이 nested property 접근
- 타입 단언(as) 남발 (정확한 타입 정의 우선)

**데이터**

- Supabase 쿼리에서 select('\*') 남발
- RLS 우회 시도 (service_role key 사용 금지)
- localStorage와 DB 동기화 누락

**UI**

- 컴포넌트 내 하드코딩된 문자열 (상수 분리)
- 인라인 스타일 대신 Tailwind 사용
- document 직접 접근 (window.document로 명시)

---

## 오류 해결 프로토콜 (고도화)

### 타입 에러 (TS2xxx)

```
[진단]
1. 에러 코드 확인 (TS2345: 인자 타입, TS2322: 할당 타입 등)
2. types.ts에서 관련 타입 정의 찾기
3. service 레이어 반환 타입 확인

[해결]
- Generic 타입 명시
- 유니온 타입 좁히기 (타입 가드)
- Optional property 처리 (?. 또는 || 기본값)

[검증]
npm run build
```

### Supabase 쿼리 에러

```
[진단]
1. 브라우저 Network 탭에서 실제 쿼리 확인
2. PostgREST 문법 검증 (.cs는 배열 contains)
3. RLS 정책 확인 (SELECT/INSERT/UPDATE 권한)

[해결]
- 쿼리 빌더 순서 조정 (.select().eq().order())
- 배열 검색 시 .cs.{"값"} 큰따옴표 사용
- RLS: user_id = auth.uid() 확인

[검증]
Supabase Studio SQL Editor에서 직접 쿼리
```

### 빌드 에러

```
[진단]
1. npm run build 출력 전문 확인
2. 에러 파일:라인 번호 추적
3. 의존성 버전 충돌 확인 (package.json)

[해결]
- TypeScript strict 모드 준수
- import 순환 참조 제거
- 타입 정의 파일 누락 확인

[검증]
1. npm run build 성공
2. dist/ 폴더 생성 확인
3. 로컬 미리보기: npx vite preview
```

### 런타임 에러

```
[진단]
1. 브라우저 Console 에러 메시지
2. React DevTools로 컴포넌트 상태 확인
3. Network 탭에서 API 응답 확인

[해결]
- null/undefined 체크 강화
- try-catch로 비동기 에러 핸들링
- useEffect cleanup 함수 작성

[검증]
각 사용자 시나리오별 수동 테스트
```

---

## 출력 형식 (템플릿)

### 코드 변경

```
[변경] src/pages/AnalysisPage.tsx (L1285-1293)
- document.execCommand → window.document.execCommand (타입 충돌 해결)

[영향]
- 없음 (로컬 함수 변경)

[검증]
npm run build
```

### 신규 생성

```
[생성] src/services/templateService.ts
- 목적: 문서 템플릿 CRUD
- 함수: getTemplates, createTemplate, updateTemplate

[연동]
import { templateService } from '@/services/templateService';

[타입]
types.ts에 Template 인터페이스 추가 필요
```

### DB 스키마 변경

```
[마이그레이션] supabase/migrations/20260217_add_templates.sql

CREATE TABLE templates (
  id uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id uuid REFERENCES auth.users NOT NULL,
  name text NOT NULL,
  content text,
  created_at timestamptz DEFAULT now()
);

ALTER TABLE templates ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can only access own templates"
  ON templates FOR ALL
  USING (auth.uid() = user_id);

[적용]
npx supabase db reset (로컬)
npx supabase db push (프로덕션)

[연동]
src/services/templateService.ts 생성
types.ts에 Template 타입 추가
```

---

## 작업 플로우

### 파일 수정 흐름

```
1. 관련 파일 식별 (Grep/Glob)
2. types.ts 타입 확인
3. 의존성 체크 (import 추적)
4. 수정 실행
5. 연쇄 영향 파일 수정
6. npm run build 검증
7. git commit (빌드 성공 시만)
```

### 새 기능 개발 흐름

```
1. 요구사항 분석 → TodoWrite
2. DB 스키마 설계 (필요 시)
3. types.ts 타입 정의
4. service 레이어 구현
5. UI 컴포넌트 구현
6. 페이지 통합
7. 네비게이션 연결 (App.tsx)
8. 빌드 검증 → commit
```

### 버그 수정 흐름

```
1. 에러 재현 조건 파악
2. 관련 파일 디버깅 (console.log/breakpoint)
3. 근본 원인 식별
4. 최소 변경으로 수정
5. 사이드 이펙트 검증
6. 빌드 → commit
```

---

## 응답 예시 (고도화)

### Low - 타입 에러

```
Q: AnalysisPage.tsx(1606): Property 'file_type' does not exist on type 'Document'

A:
doc.file_type → doc.type

types.ts Document 인터페이스에는 type 필드만 존재함.
```

### Medium - 필터링 버그

```
Q: 프롬프트 갤러리에서 "기타" 필터가 안 됨

A:
[분석]
- 파일: promptService.ts (L164)
- 원인: PostgREST 배열 검색 문법 오류
- categories.cs.{기타} → categories.cs.{"기타"} (따옴표 필요)

[수정]
query = query.or(`domain.eq.${filters.domain},categories.cs.{"${filters.domain}"}`);

[검증]
프롬프트 생성 → "기타" 태그 → 필터 클릭 → 표시 확인
```

### High - 에디터 기능 구현

```
Q: AnalysisPage 편집기 버튼들 전부 구현

A:
[복잡도] High - 14개 함수 구현 필요

[분석]
- 영향: AnalysisPage.tsx (1200줄 이상)
- 기능: 클립보드, 서식, 정렬, 리스트, 다운로드, 공유
- 위험: document 객체 타입 충돌

[계획]
1. 클립보드 (cut/copy/paste) - execCommand
2. 서식 (bold/italic/underline) - 마크다운 래핑
3. 정렬 (left/center/right) - CSS 적용
4. 리스트 (bullet/numbered) - 접두사 추가
5. 다운로드 (txt/docx/pdf/hwp) - Blob API
6. 공유 - navigator.clipboard

[실행]
TodoWrite로 진행 상황 추적
각 기능 구현 → 빌드 검증 → 다음 단계

[주의]
- document → window.document (타입 충돌 방지)
- 선택 영역 없을 때 예외 처리
- 비동기 API (clipboard, file download) 에러 핸들링
```

---

## 컨텍스트 최적화

### 파일 읽기 전략

- 큰 파일(>1000줄): offset/limit 사용
- 특정 코드 검색: Grep으로 먼저 위치 파악
- 타입 확인: types.ts만 선택적 읽기

### 토큰 절약

- Low 복잡도: 설명 1줄로 제한
- Medium: [분석][계획][실행] 각 3줄 이내
- High: TodoWrite로 진행 상황만 업데이트, 장황한 설명 지양

### 세션 관리

- 10회 이상 대화: /compact 권장
- 주제 변경: /clear 후 재시작
- 빌드 실패 반복: 전체 에러 로그 재검토
