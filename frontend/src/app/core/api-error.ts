// ---------------------------------------------------------------
// Turns an HTTP error from the API into a short message for users.
// FastAPI puts its message in { "detail": ... }.
// ---------------------------------------------------------------
import { HttpErrorResponse } from '@angular/common/http';

export function apiErrorMessage(error: unknown): string {
  if (!(error instanceof HttpErrorResponse)) {
    return 'Something went wrong.';
  }
  if (error.status === 0) {
    return 'Cannot reach the API.';
  }
  if (error.status === 401) {
    return 'Please log in.';
  }
  if (error.status === 403) {
    return "You don't have access to this.";
  }

  const detail = error.error?.detail;
  // Plain text message, e.g. "Code 'WHEAT' already exists".
  if (typeof detail === 'string') {
    return detail;
  }
  // Validation errors (422) come as a list; show the first one.
  if (Array.isArray(detail) && detail[0]?.msg) {
    const field = detail[0].loc?.at(-1);
    return field ? `${field}: ${detail[0].msg}` : detail[0].msg;
  }
  return `Request failed (${error.status}).`;
}
