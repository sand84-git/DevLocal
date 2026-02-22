/** Google Sheets URL 정규식 패턴 */
export const SHEETS_URL_REGEX =
  /^https:\/\/docs\.google\.com\/spreadsheets\/d\/[a-zA-Z0-9_-]+/;

/**
 * Google Sheets URL 유효성 검증
 * @returns null if valid, error message string if invalid
 */
export function validateSheetUrl(url: string): string | null {
  if (!url.trim()) return "Google Sheet URL을 입력해주세요";
  if (!SHEETS_URL_REGEX.test(url))
    return "올바른 Google Sheets URL을 입력해주세요";
  return null;
}

/**
 * Row Range 유효성 검증
 * @returns null if valid, error message string if invalid
 */
export function validateRowRange(start: number, end: number): string | null {
  if (start < 0) return "Row 시작값은 1 이상이어야 합니다";
  if (end < 0) return "Row 끝값은 1 이상이어야 합니다";
  if (end > 0 && start > 0 && end < start)
    return "Row 끝값은 시작값 이상이어야 합니다";
  return null;
}
