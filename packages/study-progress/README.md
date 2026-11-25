# @e-chang0/study-progress

학습 진도 계산과 Semantic Version 비교를 제공하는 9주차 실습 패키지입니다.

```js
import { summarizeProgress, isNewerVersion } from '@e-chang0/study-progress';
summarizeProgress(3, 9); // { completed: 3, total: 9, remaining: 6, percent: 33 }
isNewerVersion('1.0.1', '1.0.0'); // true
```

Node.js 24 이상. GitHub Packages 설치 인증과 Docker 실행 절차는 저장소의
[`docs/WEEK9.md`](https://github.com/e-chang0/donga/blob/main/docs/WEEK9.md)를 참고하세요.
