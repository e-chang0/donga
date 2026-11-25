# 9주차 수행 기록

작성일: 2026-11-25 (Asia/Seoul). 실제로 확인된 결과만 기록한다.

## 구현·검증

| 항목 | 확인된 결과 |
|---|---|
| 저장소 | [e-chang0/donga](https://github.com/e-chang0/donga) |
| 구현 PR | [#7](https://github.com/e-chang0/donga/pull/7) |
| PR 규칙·Python 테스트 | [Collaboration Checks 성공](https://github.com/e-chang0/donga/actions/runs/45539491576), 11개 테스트 |
| npm 테스트·소비자 설치 | [Package CI 성공](https://github.com/e-chang0/donga/actions/runs/45539491611), 패키지 테스트 4개·보안 정책 테스트 3개 |
| Docker 빌드·실행 | 같은 Package CI의 [docker-smoke](https://github.com/e-chang0/donga/actions/runs/45539491611/job/138954214222) 성공 |
| npm audit | 취약점 0개, JSON·Markdown 리포트 생성 |
| 보안 결과 보관 | [npm-audit-45539491611-1](https://github.com/e-chang0/donga/actions/runs/45539491611/artifacts/14987739192), 2027-02-23 UTC까지 보관 예정 |
| YAML 검사 | 신규 워크플로 4개 actionlint 통과 |

GitHub runner에서 확인한 컨테이너 검증 출력:

```json
{"image":"study-progress:ci","health":"ok","progress":"ok","invalidInput":"ok","user":"node"}
```

Docker 검증은 health 응답, 3/9 진도 계산, 불가능한 진도 입력의 HTTP 400,
비 root 실행 사용자를 확인했다.

## 실제 배포

사용자의 main 병합·배포 승인 후 PR #7과 [패치 업데이트 PR #10](https://github.com/e-chang0/donga/pull/10)을
각각 필수 검사 성공 뒤 squash merge했다.

| 버전 | main 커밋 | 발행 및 설치·실행 검증 |
|---|---|---|
| 1.0.0 | `49d93ea95ddd2423b50ac04a5dbe1e2098e2d13e` | [Publish Packages 성공](https://github.com/e-chang0/donga/actions/runs/45543187952) |
| 1.0.1 | `a6d10bc8ae1caa984699c24f3e22c3f1bbe3d663` | [Publish Packages 성공](https://github.com/e-chang0/donga/actions/runs/45543575553) |

- npm: `@e-chang0/study-progress@1.0.0` 및 `@e-chang0/study-progress@1.0.1`.
- 레지스트리: `https://npm.pkg.github.com`.
- 컨테이너: `ghcr.io/e-chang0/donga/study-progress:1.0.0`, `:1.0.1`, `:latest`.
- 각 배포에서 실제 npm 발행·소비자 설치, Docker build·push·pull·실행을 검증했다.
- 두 배포 모두 npm audit 취약점 0개이며 보안 결과를 artifact로 보관했다.
- [1.0.0 증빙 artifact](https://github.com/e-chang0/donga/actions/runs/45543187952/artifacts/14989314412)
  · [1.0.1 증빙 artifact](https://github.com/e-chang0/donga/actions/runs/45543575553/artifacts/14990023952).

### 발행 이미지 digest

```text
1.0.0 sha256:67239ead7cb579bc870d929441503f0732b6bbb70af5c248fc9f6c360688b558
1.0.1 sha256:722f7a679a5c420b9cab5cd4872a0645257d7ce8badb4096ea9b568acf87f22b
```

1.0.1의 registry pull 이후 실행 결과:

```json
{"image":"ghcr.io/e-chang0/donga/study-progress:1.0.1","health":"ok","progress":"ok","invalidInput":"ok","user":"node"}
```

## Dependabot 실제 동작

설정 반영 뒤 Dependabot이 [Docker 업데이트 PR #8](https://github.com/e-chang0/donga/pull/8)과
[Actions 그룹 업데이트 PR #9](https://github.com/e-chang0/donga/pull/9)를 생성했다.
두 PR은 npm 패치 자동머지 대상이 아니므로 수동 검토 대상으로 남겼다.

## 자동머지 설정 확인

GitHub Settings의 Allow auto-merge를 활성화했다. 사용자가 GitHub의 Confirm access를
직접 완료한 뒤 `Branch protection rule settings saved.`를 확인했다.
공개 브랜치 API에서도 다음 네 필수 검사와 관리자 포함 적용(`everyone`)을 확인했다.

- `collaboration-checks`
- `npm-tests`
- `security-audit`
- `docker-smoke`

기존 PR 필수·최신 base 반영·대화 해결·관리자 우회 금지 규칙을 유지했다.
현재 npm 의존성은 최신 버전이므로 실제 npm 패치 Dependabot PR의 자동 병합은 아직
관찰되지 않았다. npm patch PR이 생성되면 자동머지 워크플로가 조건을 검사한다.

## 본인 PC 설치·남은 검증

- Windows 11 Pro x64, 펌웨어 가상화 활성화 확인.
- Docker Desktop 4.100.1: 공식 Docker Inc 서명 확인, 사용자 계정 설치 exit code `0`.
- Docker CLI `29.9.3` 실행 확인.
- WSL 3.0.5.0: 공식 Microsoft Corporation 서명 확인, 설치 exit code `0`.
- Virtual Machine Platform 활성화 exit code `3010`: **PC 재부팅 필요**.
- 로컬 Docker 컨테이너 실행은 재부팅 후 검증할 예정으로, 현재 미완료다.

재부팅 후 Docker Desktop을 실행하고 저장소 루트에서 다음을 수행한다.

```powershell
docker version
docker build -t study-progress:local packages/study-progress
node scripts/verify-container.mjs study-progress:local
```

GitHub runner 실행 성공은 본인 PC의 로컬 Docker 성공으로 표시하지 않는다.
Snyk는 사용하지 않았으며, 이번 실습의 보안 스캐너는 npm audit이다.
