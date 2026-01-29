# Markdown to Blogger

마크다운 파일을 HTML로 변환하여 Blogger에 게시하는 Python CLI 도구입니다.  
Google Blogger API와 다양한 이미지 업로드 서비스를 지원합니다.

---

## 설치 방법

**Python 3.8 이상**이 필요합니다.

### 1. 저장소 클론

```bash
git clone [YOUR_REPO_URL]
cd markdown_to_blog
```

---

### 2. 의존성 설치

#### **uv 사용 시 (권장)**

```bash
# uv가 없다면 먼저 설치 (Windows)
pip install uv

# 또는 macOS/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# 프로젝트 디렉토리에서 의존성 설치 및 실행
uv sync            # 런타임/개발 의존성 자동 관리 (pyproject.toml 기반)
uv sync --dev      # 개발 의존성 그룹 포함 설치

# 가상환경 자동 활성화(uv가 자동 관리). 명령 실행 예시:
uv run mdb --help
uv run mdb publish -t "제목" post.md
```

#### **pip로 직접 설치**

```bash
pip install -e .
```

#### **Docker 실행**

```bash
docker compose up --build
```

---

## 사용법

모든 명령어는 `mdb`로 시작합니다.

| 명령어                | 설명                                              |
|----------------------|---------------------------------------------------|
| set_blogid           | 블로그 ID를 설정합니다.                           |
| get_blogid           | 현재 설정된 블로그 ID를 확인합니다.                |
| set_client_secret    | Google API 클라이언트 시크릿 파일을 설정합니다.    |
| refresh_auth         | Google API 인증 정보를 갱신합니다.                |
| convert              | 마크다운 파일을 HTML로 변환합니다.                 |
| publish              | 마크다운 파일을 블로거에 발행합니다.              |
| publish_html         | HTML 파일을 블로거에 직접 발행합니다.             |
| upload_image         | 이미지를 선택한 서비스에 업로드합니다.             |
| upload_images        | 마크다운 파일 내의 모든 이미지를 업로드합니다.     |
| publish_folder       | 폴더 내의 모든 마크다운 파일을 순차적으로 발행합니다.|
| list_my_blogs        | 내 계정의 블로그 id와 url(도메인)을 출력합니다.    |
| run_server           | Django 기반 관리 서버를 실행합니다.                |
| install_server       | 서버 파일을 지정한 위치에 설치합니다.              |
| daemon               | Daemon 서버 관리 (시작/중지/상태 확인)           |

---

### 주요 명령어 예시

- **블로그 ID 설정:**  
  `mdb set_blogid [블로그ID]`

- **현재 블로그 ID 확인:**  
  `mdb get_blogid`

- **Google API 클라이언트 시크릿 파일 설정:**  
  `mdb set_client_secret [client_secret.json 경로]`

- **인증 정보 갱신:**  
  `mdb refresh_auth`

- **마크다운 → HTML 변환:**  
  `mdb convert --input [마크다운파일.md] --output [저장할.html]`

- **마크다운 파일을 블로거에 발행:**  
  `mdb publish [옵션] [마크다운파일.md]`

- **HTML 파일을 블로거에 발행:**  
  `mdb publish_html --title "[제목]" [HTML파일명]`

- **이미지 업로드:**  
  `mdb upload_image [이미지파일] --service [서비스명]`

- **마크다운 내 모든 이미지 업로드:**  
  `mdb upload_images --input [마크다운파일] --service [서비스명] --tui`

- **폴더 내 모든 마크다운 파일 발행:**  
  `mdb publish_folder [폴더경로] --interval [시간] --service [이미지서비스] --tui`

- **내 블로그 목록(id, url) 확인:**
  `mdb list_my_blogs`
- **관리 서버 실행:**
  `mdb run_server --host 0.0.0.0 --port 8000`
- **관리 서버 설치:**
  `mdb install_server ./server`

---

## Daemon 기능 (ZeroMQ 기반)

Daemon 모드를 사용하면 모든 CLI 명령어를 원격에서 실행할 수 있습니다.

### Daemon 서버 시작

```bash
# 백그라운드에서 시작
mdb daemon start

# 포그라운드에서 시작 (디버깅용)
mdb daemon start --foreground

# 다른 주소로 바인드
mdb daemon start --bind tcp://0.0.0.0:5555
```

### Daemon 서버 상태 확인

```bash
mdb daemon status
```

### Daemon 서버 중지

```bash
# 정상 종료 (권장)
mdb daemon stop

# 강제 종료 (프로세스 직접 종료)
mdb daemon stop --force
```

Daemon 로그는 `~/.markdown_to_blog/daemon.log` 파일에 저장됩니다.

### Daemon에서 명령어 실행

```bash
# Daemon을 통해 블로그 ID 확인
mdb daemon execute get_blogid

# Daemon을 통해 마크다운 파일 발행
mdb daemon execute publish -p '{"filename": "post.md", "blogid": "your_blog_id"}'
```

### 지원하는 모든 명령어

다음 명령어들을 Daemon을 통해 실행할 수 있습니다:
- set_blogid
- get_blogid
- list_my_blogs
- convert
- refresh_auth
- set_client_secret
- encode_secret
- decode_secret
- backup_posting
- sync_posting
- update_posting
- delete_posting
- save_as_markdown
- publish
- publish_html
- upload_image
- upload_images
- publish_folder

### Message Protocol

Daemon 통신 프로토콜은 JSON 기반이며, `markdown_to_blog/libs/protocol.json`에 정의되어 있습니다.  
이 프로토콜을 다른 프로그래밍 언어에서도 사용할 수 있습니다.

**요청 예시:**
```json
{
  "id": "request-uuid",
  "command": "get_blogid",
  "params": {}
}
```

**응답 예시:**
```json
{
  "id": "request-uuid",
  "status": "success",
  "data": {
    "blogid": "your_blog_id"
  }
}
```

---

## 이미지 업로드 지원 서비스

- anhmoe, beeimg, fastpic, imagebin, pixhost, sxcu 등  
  (자세한 목록은 `mdb upload_image --help` 참고)

---

## 개발 및 기여

- PR, 이슈 환영합니다!
- 코드 스타일: black, isort, autopep8 등 지원

---

## 라이선스

MIT
