import type { ReactNode } from "react";

/**
 * 원본과 수정본을 단어 단위로 비교하여
 * 변경된 부분에 하이라이트 마킹을 적용합니다.
 */
export function highlightDiff(
  original: string,
  revised: string,
): ReactNode {
  if (!original || !revised || original === revised) {
    return revised;
  }

  const origWords = original.split(/(\s+)/);
  const revWords = revised.split(/(\s+)/);

  // LCS(Longest Common Subsequence) 기반 diff
  const lcs = buildLCS(origWords, revWords);
  const result: ReactNode[] = [];
  let oi = 0;
  let ri = 0;
  let li = 0;

  while (ri < revWords.length) {
    if (li < lcs.length && oi < origWords.length && origWords[oi] === lcs[li] && revWords[ri] === lcs[li]) {
      // 공통 부분 — 변경 없음
      result.push(<span key={ri}>{revWords[ri]}</span>);
      oi++;
      ri++;
      li++;
    } else if (li < lcs.length && revWords[ri] === lcs[li]) {
      // 원본에서 삭제된 부분 건너뛰기
      oi++;
    } else {
      // 수정본에서 추가/변경된 부분 — 하이라이트
      result.push(
        <span
          key={ri}
          className="bg-emerald-100 text-emerald-700 font-semibold rounded px-0.5"
        >
          {revWords[ri]}
        </span>,
      );
      ri++;
    }
  }

  return result;
}

/** LCS 배열 계산 (단어 단위) */
function buildLCS(a: string[], b: string[]): string[] {
  const m = a.length;
  const n = b.length;
  const dp: number[][] = Array.from({ length: m + 1 }, () =>
    Array(n + 1).fill(0),
  );

  for (let i = 1; i <= m; i++) {
    for (let j = 1; j <= n; j++) {
      if (a[i - 1] === b[j - 1]) {
        dp[i][j] = dp[i - 1][j - 1] + 1;
      } else {
        dp[i][j] = Math.max(dp[i - 1][j], dp[i][j - 1]);
      }
    }
  }

  // Backtrack to build LCS
  const lcs: string[] = [];
  let i = m;
  let j = n;
  while (i > 0 && j > 0) {
    if (a[i - 1] === b[j - 1]) {
      lcs.unshift(a[i - 1]);
      i--;
      j--;
    } else if (dp[i - 1][j] > dp[i][j - 1]) {
      i--;
    } else {
      j--;
    }
  }

  return lcs;
}
