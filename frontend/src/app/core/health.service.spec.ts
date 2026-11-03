// ---------------------------------------------------------------
// Tests for HealthService. HttpTestingController intercepts HTTP
// calls, so no real backend is needed.
// ---------------------------------------------------------------
import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { TestBed } from '@angular/core/testing';

import { Health, HealthService } from './health.service';

describe('HealthService', () => {
  let service: HealthService;
  let httpMock: HttpTestingController;

  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [provideHttpClient(), provideHttpClientTesting()],
    });
    service = TestBed.inject(HealthService);
    httpMock = TestBed.inject(HttpTestingController);
  });

  // Fail the test if any expected request was never made.
  afterEach(() => httpMock.verify());

  it('calls GET /api/health and returns the response', () => {
    const fake: Health = { status: 'ok', version: '0.1.0', db_mode: 'local', database: 'ok' };
    let result: Health | undefined;

    service.getHealth().subscribe((health) => (result = health));

    const request = httpMock.expectOne('/api/health');
    expect(request.request.method).toBe('GET');
    request.flush(fake);

    expect(result).toEqual(fake);
  });
});
