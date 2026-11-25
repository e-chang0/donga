# 9주차: GitHub Packages와 의존성 보안 자동화

## 구현과 흐름

| 과제 | 구현 | 확인할 증빙 |
|---|---|---|
| npm 최초 배포·패치 업데이트 | `@e-chang0/study-progress`, `v1.0.0`과 `v1.0.1` 태그 | Packages의 두 버전과 Publish Packages 성공 로그 |
| Docker 자동 빌드·푸시 | `ghcr.io/e-chang0/donga/study-progress:<버전>` | 빌드·실행·push·다시 pull 후 검증 로그 |
| 로컬 컨테이너 실행 | `scripts/verify-container.mjs` | 실제 PC에서 실행한 명령·출력 |
| Dependabot | npm·Docker·Actions 주간 업데이트와 npm 그룹 | `.github/dependabot.yml`과 실제 업데이트 PR |
| 자동머지 조건 | npm patch만, 필수 검사와 보호 규칙 적용 | 워크플로·저장소 설정·해당 시 자동머지 로그 |
| 보안 결과 자동화 | npm audit JSON·Markdown·Actions Summary·90일 artifact | Package CI 또는 정기 보안 워크플로 artifact |

이번 실습은 과제의 `npm audit/Snyk` 중 **npm audit**를 사용한다.
Snyk 스캔이나 SNYK_TOKEN 설정을 수행했다고 표시하지 않는다.

### 1. 로컬 npm 검증

Node.js 24 이상, 저장소 루트에서 실행한다.

```powershell
cd packages/study-progress
npm ci --ignore-scripts
npm test
npm pack --dry-run
cd ../..
node --test scripts/audit-policy.test.mjs
node scripts/security-audit.mjs
```

패키지는 학습 진도 계산과 semver 비교를 제공한다. HTTP 서버는 같은 계산 함수를
사용하며 `GET /health`, `GET /progress?completed=3&total=9`를 제공한다.

### 2. 저장소 설정

관리자는 다음 설정을 확인한다. 기존 보호 규칙을 완화하거나 우회하지 않는다.

1. Settings → General → Pull Requests → **Allow auto-merge**를 켠다.
2. `main` 브랜치 보호에서 PR 필수, 최신 base 반영, 대화 해결, 관리자 우회 금지를 유지한다.
3. 필수 상태 검사에 `collaboration-checks`, `npm-tests`, `security-audit`, `docker-smoke`를 모두 등록한다.
4. Dependency graph·Dependabot alerts·Dependabot security updates를 켠다.
5. Actions에서 패키지 발행 워크플로의 `packages: write` 권한을 허용한다.

자동머지 워크플로는 실제 `dependabot[bot]`이 동일 저장소에서 만든 PR의 검증된
메타데이터를 사용한다. npm patch 업데이트만 대상이며 npm minor·major,
Docker·Actions 업데이트는 사람이 검토한다. 업데이트 PR 코드를
`pull_request_target` 워크플로에서 checkout하거나 실행하지 않는다.

브랜치 보호에 네 필수 검사가 없거나 관리자에게도 적용되지 않으면 자동머지
요청을 거부한다. GitHub의 auto-merge가 필수 검사·리뷰·대화 해결 규칙을 기다린다.
저장소 설정까지 확인하기 전에는 자동머지가 활성화됐다고 기록하지 않는다.

### 3. 1.0.0 발행

코드 PR을 검사 후 `main`에 병합한 다음, 그 커밋에 태그를 붙인다.

```powershell
git switch main
git pull --ff-only
git tag v1.0.0
git push origin v1.0.0
```

`Publish Packages`는 태그와 package.json 버전 일치, main 이력 포함 여부,
npm 테스트·보안 검사·Docker 실행을 검증한 뒤 발행한다.
Actions가 자동으로 제공하는 `GITHUB_TOKEN`을 사용하므로 수동 PAT를
저장소에 커밋할 필요가 없다. npm 패키지 설치와 GHCR에서 다시 pull한 이미지의
실행까지 확인한다. 발행된 버전은 재사용하지 않는다.

### 4. 1.0.1 업데이트

```powershell
git switch -c feature/week9-patch-release
cd packages/study-progress
npm version patch --no-git-tag-version
npm test
cd ../..
git add packages/study-progress/package.json packages/study-progress/package-lock.json
git commit -m "chore(release): bump study-progress to 1.0.1"
git push -u origin feature/week9-patch-release
# PR 생성 → 검사 통과 → main에 병합
git switch main
git pull --ff-only
git tag v1.0.1
git push origin v1.0.1
```

Packages에서 1.0.0과 1.0.1이 모두 존재하는지 확인한다. 단순히 package.json의
숫자를 바꾸는 것과 실제 레지스트리에 새 버전을 발행하는 것을 구분한다.

### 5. Docker 로컬 검증

Docker Desktop의 Linux 컨테이너 엔진이 실행 중이어야 한다.

```powershell
docker version
docker build -t study-progress:local packages/study-progress
node scripts/verify-container.mjs study-progress:local
```

검증 스크립트는 임시 localhost 포트로 컨테이너를 실행하고 health·진도 응답·잘못된
입력의 HTTP 400·비 root 사용자를 검사한 뒤 자신이 만든 컨테이너를 정리한다.

발행된 GHCR 이미지를 검증하려면 다음을 실행한다. 패키지가 비공개이면
본인 계정으로 `docker login ghcr.io`가 먼저 필요하다.

```powershell
docker pull ghcr.io/e-chang0/donga/study-progress:1.0.1
node scripts/verify-container.mjs ghcr.io/e-chang0/donga/study-progress:1.0.1
```

GitHub-hosted runner의 Docker 성공을 본인 PC의 로컬 실행 성공으로 대신 적지 않는다.
현재 PC에 Docker가 없으면 로컬 검증은 미완료로 남긴다.

### 6. Dependabot·보안 정책

- 매주 월요일 Asia/Seoul 기준 npm 09:00, Docker 09:10, Actions 09:20 업데이트 확인.
- npm patch·minor·보안 업데이트를 각각 그룹화. major는 수동 검토.
- npm version PR 동시 최대 2개, Docker와 Actions는 각각 1개.
- 매주 월요일 09:23에 정기 npm audit. PR·main·배포 시에도 검사.
- 모든 npm 의존성을 검사하고 high·critical 취약점 또는 스캐너 오류가 있으면 CI 실패.
- 낮은 심각도의 취약점도 JSON·Markdown에 기록한다.
- 보안 검사 실패 시에도 결과 artifact를 업로드하며 보관 기간은 90일이다.

리포트에는 검사 시각(UTC), 커밋, 실행 링크, 심각도별 건수를 넣는다.
취약점이 없는 결과도 리포트로 보관하므로 의도적으로 취약한 의존성을 넣지 않는다.

## 제출 증빙 체크리스트

- [ ] 구현 PR과 실제 성공한 Package CI 링크
- [ ] npm 1.0.0 및 1.0.1 Packages 화면과 각각의 배포 로그
- [ ] GHCR 이미지 버전·digest와 push/pull·실행 검증 로그
- [ ] 본인 PC의 Docker 로컬 실행 출력
- [ ] Dependabot 스케줄·그룹 설정
- [ ] 자동머지 허용 및 필수 검사 설정 확인
- [ ] npm audit 결과 JSON·Markdown 또는 artifact 링크

## 공식 문서

- [GitHub Packages npm 배포](https://docs.github.com/en/actions/tutorials/publish-packages/publish-nodejs-packages)
- [GitHub Actions Docker 이미지 배포](https://docs.github.com/en/actions/tutorials/publish-packages/publish-docker-images)
- [Dependabot 설정](https://docs.github.com/en/code-security/reference/supply-chain-security/dependabot-options-reference)
- [Dependabot 자동머지](https://docs.github.com/en/code-security/tutorials/secure-your-dependencies/automate-dependabot-with-actions)
