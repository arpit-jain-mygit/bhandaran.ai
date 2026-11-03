// ---------------------------------------------------------------
// Tests for the Home page: it shows the right text for each
// API outcome (healthy, API down).
// ---------------------------------------------------------------
import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { TestBed } from '@angular/core/testing';

import { Home } from './home';

describe('Home', () => {
  let httpMock: HttpTestingController;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [Home],
      providers: [provideHttpClient(), provideHttpClientTesting()],
    }).compileComponents();
    httpMock = TestBed.inject(HttpTestingController);
  });

  // Helper: read the text of the main status element.
  function statusText(element: HTMLElement): string {
    return element.querySelector('[data-testid="status"]')?.textContent?.trim() ?? '';
  }

  it('shows "ok" when the API and database are healthy', async () => {
    const fixture = TestBed.createComponent(Home);
    httpMock
      .expectOne('/api/health')
      .flush({ status: 'ok', version: '0.1.0', db_mode: 'local', database: 'ok' });
    await fixture.whenStable();

    expect(statusText(fixture.nativeElement)).toBe('ok');
  });

  it('shows an error message when the API is unreachable', async () => {
    const fixture = TestBed.createComponent(Home);
    httpMock.expectOne('/api/health').flush('down', { status: 502, statusText: 'Bad Gateway' });
    await fixture.whenStable();

    expect(statusText(fixture.nativeElement)).toContain('API unreachable');
  });
});
