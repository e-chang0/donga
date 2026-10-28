# main 브랜치 보호 운영

GitHub Settings → Branches → Classic branch protection rule에서 `main`을 대상으로 설정합니다. 이 문서는 목표 설정과 검증 절차이며 실제 적용 결과는 과제 제출 기록과 GitHub 설정 화면을 기준으로 확인합니다.

| 항목 | 개인 과제 설정 | 이유 |
|---|---|---|
| Require a pull request before merging | 켜기 | 변경을 Feature 브랜치·PR로 기록 |
| Require approvals | 끄기 (0명) | 작성자는 자신의 PR을 승인할 수 없으며 현재 팀원이 없음 |
| Require review from Code Owners | 끄기 | 현재 유일한 소유자가 PR 작성자이므로 자기 승인 교착 방지 |
| Require status checks | `collaboration-checks` | PR 규칙 및 DORA·정책 회귀 테스트 |
| Require branches to be up to date | 켜기 | 최신 main과 통합한 결과 확인 |
| Require conversation resolution | 켜기 | 인라인 리뷰 논의 해결 |
| Do not allow bypassing the above settings | 켜기 | 관리자도 PR과 검증 절차 준수 |
| Allow force pushes / deletions | 모두 끄기 | main 이력과 브랜치 보존 |

설정하기 전에 `Collaboration Checks`가 실제 PR에서 성공하여 `collaboration-checks` 상태가 등록되어야 합니다. 팀원이 참여하면 실제 Code Owner를 추가하고 타인 승인 1건 이상 및 Code Owner 승인을 별도 PR/설정으로 활성화합니다.

## DORA 자동화와의 호환

기존 DORA workflow는 보고서를 생성하고 `main`에 직접 push했습니다. PR 필수 보호와 함께 사용할 수 없어 아래 흐름으로 조정했습니다.

1. 매주 또는 수동 실행으로 최신 main을 checkout합니다.
2. 기존 DORA 단위 테스트 → 지표 수집 → 실행 요약 → 90일 artifact 업로드를 수행합니다.
3. 변경된 보고서만 고유한 `feature/dora-report-<run_id>-<run_attempt>` 브랜치에 push합니다.
4. 사용자가 실행 요약의 비교 링크에서 PR을 엽니다. 제목은 `chore(metrics): update weekly DORA report`로 입력합니다.
5. CI와 리뷰를 거쳐 병합하면 기본 브랜치의 대시보드가 갱신됩니다.

기본 GITHUB_TOKEN으로 만든 변경은 다른 workflow를 자동 연쇄 실행하지 않으므로, bot이 자동으로 PR을 생성하지 않고 사용자가 직접 여는 흐름을 사용합니다. 추가 PAT·새 secret·자동 승인·보호 예외는 사용하지 않습니다. 보고서가 바뀌지 않으면 새 브랜치를 만들지 않습니다.

## 검증과 복구

- 설정 화면에서 main 규칙과 필수 상태 이름을 확인합니다.
- DORA 수동 실행 결과에서 지표 artifact와 feature 브랜치 생성 성공을 확인합니다.
- 보호 이후에도 main 직접 push를 시도하는 옛 workflow를 사용하지 않습니다.
- 기능을 되돌려야 한다면 revert PR로 수정합니다. DORA workflow를 예전 직접 push 방식으로만 되돌리면 보호 규칙 때문에 실패하므로 두 설정의 호환성을 함께 검토합니다.

참고: [GitHub 보호 브랜치 문서](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-protected-branches/about-protected-branches), [GITHUB_TOKEN의 workflow 재실행 제한](https://docs.github.com/en/actions/how-tos/writing-workflows/choosing-when-your-workflow-runs/triggering-a-workflow).
