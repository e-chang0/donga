# 기여 가이드

이 저장소는 동아대학교 학습·과제를 GitHub Flow로 관리합니다. 기존 2·3주차 기록과 DORA 자동화를 유지하면서 변경을 작은 PR로 제안합니다.

## 작업 순서

1. 이슈 또는 PR 본문에 변경 목적과 완료 조건을 적습니다.
2. 최신 `main`에서 `feature/<작업명>` 브랜치를 만듭니다. `main`에 직접 push하지 않습니다.
3. 한 PR에는 하나의 목적만 담고, 아래 커밋 규칙을 지킵니다.
4. PR 템플릿을 작성하고 테스트 명령과 실제 결과를 남깁니다.
5. 변경 diff를 검토하고 `[MUST]`·`[SHOULD]` 피드백을 기록합니다.
6. `[MUST]`를 해결하고 CI 성공을 확인한 뒤 squash merge합니다. squash 제목도 Conventional Commits를 따릅니다.
7. 병합된 원격 브랜치는 제출 증빙을 확인한 후 정리합니다.

```bash
git switch main
git pull --ff-only origin main
git switch -c feature/<작업명>
# 변경 및 테스트
git add <변경한-파일>
git commit -m "docs(collaboration): add contribution guide"
git push -u origin feature/<작업명>
```

## Conventional Commits

형식은 `<type>(<선택적 scope>)!: <설명>`입니다. 호환성 파괴가 없으면 `!`를 생략합니다.

| type | 사용 예 |
|---|---|
| `feat` | 기능 추가 |
| `fix` | 오류 수정 |
| `docs` | 문서 변경 |
| `test` | 테스트 추가·수정 |
| `refactor` | 동작을 유지하는 구조 개선 |
| `ci` | GitHub Actions·검증 변경 |
| `chore` | 보고서 갱신·유지보수 |
| `perf`, `style`, `build`, `revert` | 성능·서식·빌드·되돌림 |

예: `ci(review): validate pull request conventions`, `chore(metrics): update weekly DORA report`.
PR 제목과 이번 PR에서 추가한 일반 커밋의 제목에 이 규칙을 적용합니다. 과거 커밋은 다시 쓰지 않습니다.

## 검증

Python 3.12 이상에서 저장소 루트에서 실행합니다. Windows에서는 `python` 대신 `py`를 사용할 수 있습니다.

```bash
python -m unittest discover -s tests -v
git diff --check
```

문서 변경은 상대 링크·경로·예시 명령을 확인합니다. 코드 변경은 정상 입력뿐 아니라 오류·경계 조건도 검증합니다. 실행하지 않은 테스트를 성공으로 표시하지 않습니다.

## 리뷰와 개인 실습

- 리뷰 요청 전에 작성자가 먼저 diff를 점검합니다.
- `[MUST]`: 병합 전에 해결할 오류·검증 누락. 근거와 수정 방향을 함께 적습니다.
- `[SHOULD]`: 개선 권고. 수용하거나 보류 이유를 답변합니다.
- 자기 리뷰는 `COMMENT`로 제출하고 **자기 리뷰**라고 명시합니다. 타인의 승인으로 계산하지 않습니다.
- 팀 협업 시 작성자 외 리뷰어의 승인을 받고, CODEOWNERS에 실제 쓰기 권한이 있는 팀원을 등록합니다.
- 개인 실습의 자기 리뷰 3건이 강의의 리뷰 3건 요건으로 인정되는지는 담당자에게 확인해야 합니다.

동시 리뷰 대기 PR은 기존 `PROJECT_RULES.md`의 한도인 2개를 지킵니다. PR 본문과 리뷰 기록은 수행한 작업의 증빙이며, 다른 사람의 리뷰나 승인을 대신 만들어 기록하지 않습니다.
