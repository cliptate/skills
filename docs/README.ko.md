# Cliptate Skills

macOS 명령줄에서 [Cliptate](https://github.com/cliptate/cliptate)를 사용하는 에이전트 스킬입니다.

**언어:** [English](../README.md) · [简体中文](README.zh.md) · [日本語](README.ja.md) · 한국어 · [Deutsch](README.de.md)

## 제공되는 스킬

| 스킬 | 기능 |
| --- | --- |
| [cliptate](../cliptate/SKILL.md) | 로컬 오디오·비디오 전사, 자막 내보내기, 음성 합성, 인식 사전 관리, 기록 및 교정 근거 조회 |
| [cliptate-long2shorts](../cliptate-long2shorts/SKILL.md) | Cliptate 전사, 에이전트의 구간 선택·번역, FFmpeg 렌더링으로 긴 영상을 세로형 하이라이트로 변환 |

명령 예제, JSON 처리, 페이지네이션, 일부 실패 처리 및 버전 확인 안내가 포함되어 있습니다. 스킬 지침은 현재 중국어 간체로 작성되어 있지만, 에이전트는 다른 언어의 요청에도 활용할 수 있습니다. 이 저장소는 에이전트 지침을 제공하며 Cliptate 앱은 별도로 설치해야 합니다.

## 요구 사항

- macOS 15 이상을 실행하는 Apple Silicon Mac.
- GitHub 또는 직접 다운로드 버전의 Cliptate. App Store 버전은 CLI 서비스를 제공하지 않습니다.
- 필요한 명령이 `cliptate --help`에 표시되는 CLI 버전. 이전 버전에는 `tts`나 `history`가 없을 수 있습니다.
- 필요한 모델이 이미 다운로드되어 있어야 합니다. 모델 다운로드가 필요한 작업에는 `--download`를 사용합니다.
- `cliptate-long2shorts`에는 Python 3.9+, ffprobe, libass 지원 FFmpeg, 자막 글꼴도 필요합니다. YouTube 소스에는 yt-dlp를 사용합니다.

## 설치 및 사용

### npx로 설치

Node.js와 npm을 설치한 후 [skills CLI](https://github.com/vercel-labs/skills)에서 스킬과 대상 에이전트를 대화형으로 선택할 수 있습니다.

```sh
npx skills add cliptate/skills
```

Codex용으로 두 스킬을 전역 설치하려면:

```sh
npx skills add cliptate/skills --agent codex --global --skill cliptate --skill cliptate-long2shorts
```

`--global`을 지정하면 모든 프로젝트에서 사용할 수 있으며, 생략하면 현재 프로젝트에 설치합니다. `cliptate`만 필요하면 `--skill cliptate-long2shorts`를 제외하세요. `cliptate-long2shorts`는 전사에 `cliptate`를 사용하므로 두 스킬을 함께 설치해야 합니다. 다른 에이전트는 대화형으로 선택하거나 `--agent`를 해당 에이전트의 지원 식별자로 변경하세요.

### 수동 설치

이 저장소를 복제한 후 필요한 스킬의 `cliptate/` 또는 `cliptate-long2shorts/` 폴더 전체를 Codex의 `~/.codex/skills/`로 복사합니다. 포함된 `references/`, `agents/`, `scripts/` 하위 폴더도 유지하세요. `cliptate`는 단독으로 사용할 수 있습니다. `cliptate-long2shorts`는 전사에 `cliptate` 스킬을 사용하므로 두 폴더를 같은 스킬 디렉터리에 설치하세요. 대상 폴더가 이미 있다면 교체하기 전에 내용을 확인합니다. 다른 에이전트에서는 해당 에이전트가 지원하는 스킬 디렉터리를 사용합니다. Codex에서는 다음 대화 턴부터 사용할 수 있습니다.

Cliptate의 **설정 → 명령줄**에서 제공하는 설치 명령으로 helper를 `~/.local/bin`에 연결합니다. 이 디렉터리가 PATH에 포함되어 있는지 확인하거나 앱 번들 안의 helper를 직접 실행합니다. 실제 명령을 확인하세요.

```sh
cliptate --version
cliptate --help
```

요청 예제:

```text
$cliptate를 사용해 interview.mp4를 전사하고 interview.srt로 저장해 주세요.
$cliptate를 사용해 narration.txt를 narration.wav 음성으로 합성해 주세요.
$cliptate를 사용해 최근 교정 기록을 분석하고 신뢰할 수 있는 새 용어를 사전에 추가해 주세요.
$cliptate-long2shorts를 사용해 interview.mp4에서 30–90초 길이의 세로 영상 3개를 만들고 중국어·영어 자막을 넣어 주세요. 먼저 첫 번째 영상을 미리 보여 주세요.
```

공개 CLI는 SRT/VTT 자막 파일을 내보내며 영상 편집이나 자막 삽입 렌더링은 지원하지 않습니다. 명령은 선택한 앱의 설정을 사용합니다. 전사와 음성 합성은 기록을 새로 만들지 않지만 사전 변경 사항은 저장됩니다.

`cliptate-long2shorts`는 FFmpeg로 영상 구간을 잘라 자막을 렌더링합니다. 기본적으로 원본 화면 전체를 유지하고 여백을 추가하며 MP4, ASS, 두 줄 요약, 표지·미리보기 이미지, 원본 구간 정보를 제공합니다. CLI 시간 정보는 세그먼트 단위이며 단어 단위 정밀도나 플랫폼 게시 기능은 제공하지 않습니다.

## 참고 문서

- [스킬 진입점](../cliptate/SKILL.md): CLI 확인, 작업 선택, 결과 판단.
- [전사 및 자막](../cliptate/references/transcription.md): 입력, 형식, 출력 경로, 배치 JSON.
- [음성 합성](../cliptate/references/tts.md): 텍스트 입력, 모델 종류, 음성 설계·복제, WAV 출력.
- [사전 및 기록](../cliptate/references/dictionary-history.md): 용어 관리, 기록 페이지네이션, 교정 기록에서 학습.
- [짧은 영상 워크플로](../cliptate-long2shorts/SKILL.md), [실행 환경](../cliptate-long2shorts/references/runtime.md), [렌더링 매니페스트](../cliptate-long2shorts/references/manifest.md).

유지보수 시 실제 helper의 도움말을[상위 프로젝트의 CLI 가이드](https://github.com/cliptate/cliptate/blob/main/docs/cli.md) 및 인수 파서와 비교하세요. 현재 소스의 기능이 설치된 앱에는 아직 없을 수 있습니다.
