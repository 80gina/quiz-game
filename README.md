# 숲해설·환경교육 퀴즈 게임

터미널에서 동작하는 퀴즈 게임입니다. 퀴즈를 풀고, 새 퀴즈를 추가하고, 목록과 최고 점수를 확인할 수 있고, 프로그램을 끄고 다시 켜도 **퀴즈와 최고 점수가 `state.json`에 남습니다.**

## 1. 프로젝트 개요
| 항목 | 내용 |
|---|---|
| 목표 | Python 기본 문법, 클래스(객체 지향), 파일 입출력(JSON), Git(브랜치·병합·clone·pull) 연습 |
| 언어 | Python 3.10 이상 (표준 라이브러리만 사용, 외부 라이브러리 없음) |
| 구조 | `Quiz`(퀴즈 한 문제), `QuizGame`(게임 전체) 클래스 2개 |
| 저장 | 프로젝트 루트의 `state.json` (UTF-8) |

## 2. 퀴즈 주제와 선정 이유
- **주제:** 숲, 생태, 수질, 환경영향평가
- **선정 이유:** 숲해설·환경교육·환경영향평가 업무와 직접 연결되어 문제를 만들기 쉽고, 교육 현장에서 바로 쓸 수 있는 주제이기 때문입니다.
- **기본 퀴즈:** 5문제 (식물층, BOD, 법정보호종, 부영양화, 광합성)

## 3. 실행 방법
```bash
python main.py
```
Windows에서 `python`이 안 되면 `py main.py`를 사용합니다. 메뉴에서 번호를 입력해 기능을 선택합니다. (`5`로 종료)

## 4. 기능 목록
| 메뉴 | 기능 | 설명 |
|---|---|---|
| 1 | 퀴즈 풀기 | 저장된 퀴즈를 차례로 출제하고 정답/오답을 알려 주며, 끝나면 점수를 보여 줍니다. 퀴즈가 없으면 안내합니다. |
| 2 | 퀴즈 추가 | 문제, 선택지 4개, 정답 번호(1~4)를 입력받아 새 퀴즈를 등록하고 저장합니다. |
| 3 | 퀴즈 목록 | 등록된 퀴즈의 문제를 번호와 함께 보여 줍니다. 퀴즈가 없으면 안내합니다. |
| 4 | 점수 확인 | 최고 점수를 보여 줍니다. 퀴즈를 풀 때마다 최고 점수와 비교해 갱신합니다. 안 풀었으면 안내합니다. |
| 5 | 종료 | 저장하고 종료합니다. |

### 입력과 오류 처리
| 상황 | 처리 |
|---|---|
| 앞뒤 공백 (` 5 `) | 공백을 지우고 처리합니다. |
| 숫자가 아닌 입력 (`abc`) | `숫자만 입력하세요.` 후 다시 입력받습니다. |
| 범위 밖 숫자 (메뉴 `9`, 정답 `0`) | 범위를 안내하고 다시 입력받습니다. |
| 빈 입력 (그냥 Enter) | 안내하고 다시 입력받습니다. |
| `Ctrl+C`, 입력 스트림 종료(EOF) | 비정상 종료하지 않고 안내 후 **저장하고 안전하게 종료**합니다. |
| `state.json`이 없음 (첫 실행) | 기본 퀴즈 5개로 시작합니다. |
| `state.json`이 손상됨 | 안내 후 기본 퀴즈로 복구합니다. |

## 5. 파일 구조
```
quiz-game/
├── main.py        # Quiz, QuizGame 클래스와 실행 코드
├── state.json     # 퀴즈와 최고 점수 (프로그램이 자동 생성·갱신, 저장소에는 올리지 않음)
├── .gitignore     # 파이썬 임시 파일 무시
├── README.md      # 이 문서
└── docs/
    └── screenshots/   # 실행 화면과 Git 작업 증거
```

### 코드 구성 (`main.py`)
| 이름 | 종류 | 역할 |
|---|---|---|
| `Quiz` | 클래스 | 속성 `question`, `choices`, `answer`. 메서드 `show()`, `is_correct()`, `to_dict()`, `from_dict()` |
| `default_quizzes()` | 함수 | 기본 퀴즈 5개를 `Quiz` 인스턴스로 만들어 돌려줍니다. |
| `QuizGame` | 클래스 | 속성 `quizzes`, `best_score`. 메서드 `show_menu`, `play`, `add_quiz`, `list_quizzes`, `show_score`, `load`, `save`, `run`, 입력 도우미 `read_line`, `read_int` |

## 6. 데이터 파일 설명 (`state.json`)
| 항목 | 내용 |
|---|---|
| 경로 | 프로젝트 루트 (`main.py`와 같은 폴더) |
| 인코딩 | UTF-8 (한글이 깨지지 않도록 `ensure_ascii=False`) |
| 역할 | 프로그램을 끄고 다시 켜도 추가한 퀴즈와 최고 점수를 유지 |
| 생성 시점 | 퀴즈를 풀거나 추가할 때, 종료할 때 자동 저장 |

### 스키마
```json
{
  "quizzes": [
    {
      "question": "문제 문장",
      "choices": ["선택지 1", "선택지 2", "선택지 3", "선택지 4"],
      "answer": 1
    }
  ],
  "best_score": 5
}
```
| 키 | 타입 | 설명 |
|---|---|---|
| `quizzes` | 리스트 | 퀴즈 목록 |
| `quizzes[].question` | 문자열 | 문제 |
| `quizzes[].choices` | 문자열 4개 리스트 | 선택지 |
| `quizzes[].answer` | 정수 (1~4) | 정답 번호 |
| `best_score` | 정수 또는 `null` | 최고 정답 수 (아직 안 풀었으면 `null`) |

`state.json`은 실행할 때마다 바뀌는 기록 파일이라 저장소에는 포함하지 않았습니다. 구조와 실제 내용은 아래 스크린샷에서 확인할 수 있습니다.

## 7. 실행 결과 스크린샷
| 기능 | 화면 |
|---|---|
| 메뉴, 입력 검증 (`abc`, 빈 입력, `9`) | ![메뉴](docs/screenshots/S4_menu_run.png) |
| 퀴즈 풀기 | ![퀴즈 풀기](docs/screenshots/S9_play_quiz.png) |
| 결과 점수 | ![결과](docs/screenshots/S11_play_result.png) |
| 퀴즈 추가 | ![퀴즈 추가](docs/screenshots/S19_add_quiz.png) |
| 퀴즈 목록 | ![퀴즈 목록](docs/screenshots/S21_list_quiz.png) |
| 점수 확인 | ![점수 확인](docs/screenshots/S23_score.png) |
| `state.json` 저장 내용 | ![state.json](docs/screenshots/S28_state_json.png) |
| 껐다 켜도 유지됨 | ![유지](docs/screenshots/S29_state_persist.png) |
| 손상된 파일 복구 | ![복구](docs/screenshots/S30_state_corrupt.png) |

## 8. Git 작업 기록
### 커밋 (의미 단위로 나눠서 기록)
| # | 커밋 | 내용 |
|---|---|---|
| 1 | `29e3b37` Chore: 저장소 초기 설정 | `.gitignore`, `README.md` |
| 2 | `fbb6e05` Feat: 메뉴 기능과 입력 검증 구현 | 메뉴, 입력 검증 |
| 3 | `1b3ccfa` Feat: Quiz 클래스 구현 | `Quiz` 클래스 |
| 4 | `6f6ca04` Feat: 기본 퀴즈 데이터 5개 작성 | 기본 퀴즈 |
| 5 | `4899875` Feat: 퀴즈 풀기 기능 구현 | (브랜치 `feature/play-quiz`) |
| 6 | `b165a01` Feat: 퀴즈 결과 표시와 퀴즈 없음 처리 | (브랜치 `feature/play-quiz`) |
| 7 | `ad654b1` Merge: 퀴즈 풀기 기능 병합 | `main`에 병합 |
| 8 | `1ab5db8` Feat: 퀴즈 추가 기능 구현 | 퀴즈 추가 |
| 9 | `5c21bb9` Feat: 퀴즈 목록 기능 구현 | 퀴즈 목록 |
| 10 | `7a428f1` Feat: 점수 확인과 최고 점수 갱신 구현 | 점수 |
| 11 | `cc89c38` Refactor: QuizGame 클래스로 구조 정리 | 클래스 구조 정리 |
| 12 | `6fba925` Feat: state.json 저장·불러오기와 예외 처리 구현 | 파일 입출력 |
| 13 | Docs: README 작성 | 이 문서 |

### 브랜치와 병합
`main`에서 `feature/play-quiz` 브랜치를 만들어 퀴즈 풀기 기능을 개발한 뒤 `git merge --no-ff`로 `main`에 병합했습니다.

![병합 그래프](docs/screenshots/S14_merge.png)

### 사용한 Git 명령 7종
| 명령 | 사용한 곳 |
|---|---|
| `init` | 저장소 시작 |
| `add` | 커밋 전 파일 담기 |
| `commit` | 기능 단위 저장 |
| `push` | GitHub로 올리기 |
| `pull` | (clone 실습 후 변경 가져오기, 아래 9장) |
| `checkout` | 브랜치 생성과 이동 (`checkout -b feature/play-quiz`, `checkout main`) |
| `clone` | (복제 실습, 아래 9장) |

## 9. clone / pull 실습
(실습 후 이 장을 채웁니다.)
- clone 실습: 복제 저장소(quiz-game-clone)에서 이 줄을 추가하고 push했습니다.
