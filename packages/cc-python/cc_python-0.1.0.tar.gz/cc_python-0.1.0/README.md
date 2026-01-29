# CC Python

Claude Code 스타일의 터미널 기반 AI 코딩 어시스턴트 (Python/Textual 구현)

## 기능

### 핵심 기능
- **AI 대화**: Claude API를 통한 실시간 스트리밍 응답
- **도구 시스템**: 파일 읽기/쓰기, 셸 명령 실행, Git 작업 지원
- **권한 관리**: 도구 실행 전 사용자 승인 요청
- **세션 관리**: 대화 저장/복원 기능

### 도구 (Tools)
- **파일 도구**: `read_file`, `write_file`, `edit_file`, `list_directory`, `search_files`, `glob`
- **셸 도구**: `bash`, `python`
- **Git 도구**: `git_status`, `git_diff`, `git_log`, `git_commit`, `git_branch`, `git_checkout`

### 명령어 (Commands)
- `/help` - 사용 가능한 명령어 표시
- `/clear` - 대화 내용 삭제
- `/exit` - 종료
- `/model [name]` - 모델 변경/표시
- `/config [key] [value]` - 설정 변경/표시
- `/sessions` - 저장된 세션 목록
- `/resume <id>` - 세션 복원
- `/save [name]` - 현재 세션 저장
- `/context` - 현재 컨텍스트 정보
- `/compact` - 대화 히스토리 압축
- `/init` - CLAUDE.md 파일 생성

## 설치

```bash
# uv 사용 (권장)
uv sync

# pip 사용
pip install -e .
```

## 사용법

```bash
# 실행
cc-python

# 또는 uv로 실행
uv run cc-python
```

### 환경 변수

```bash
# API 키 설정 (필수)
export ANTHROPIC_API_KEY="your-api-key"
```

### 프로젝트 컨텍스트

프로젝트 루트에 `CLAUDE.md` 파일을 생성하면 AI가 프로젝트 컨텍스트를 자동으로 로드합니다:

```bash
/init  # CLAUDE.md 템플릿 생성
```

## 키보드 단축키

- `Tab` - Thinking 모드 토글
- `Ctrl+C` - 종료
- `Ctrl+L` - 화면 지우기

## 설정

설정 파일 위치: `~/.cc-python/config.toml`

```toml
[api]
model = "claude-sonnet-4-20250514"
max_tokens = 8192

[thinking]
enabled = false
budget = 10000

[tools]
auto_approve_read = false
auto_approve_write = false
auto_approve_shell = false
```

## 지원 모델

- `claude-sonnet-4-20250514` (기본)
- `claude-opus-4-20250514`
- `claude-3-5-sonnet-20241022`
- `claude-3-5-haiku-20241022`

## 개발

```bash
# 개발 모드로 실행
uv run textual run --dev cc_python:main

# 콘솔 열기
uv run textual console
```

## 라이선스

MIT
