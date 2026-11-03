// ---------------------------------------------------------------
// Tests for the temporary admin key: it is attached ONLY to
// non-GET requests to /api/master, and only when a key is set.
// ---------------------------------------------------------------
import { HttpClient, provideHttpClient, withInterceptors } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { TestBed } from '@angular/core/testing';

import { AdminKeyStore, adminKeyInterceptor } from './admin-key';

describe('adminKeyInterceptor', () => {
  let http: HttpClient;
  let httpMock: HttpTestingController;
  let store: AdminKeyStore;

  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [
        provideHttpClient(withInterceptors([adminKeyInterceptor])),
        provideHttpClientTesting(),
      ],
    });
    http = TestBed.inject(HttpClient);
    httpMock = TestBed.inject(HttpTestingController);
    store = TestBed.inject(AdminKeyStore);
    store.set('');
  });

  afterEach(() => {
    store.set('');
    httpMock.verify();
  });

  it('adds X-Admin-Key to master-data writes when a key is set', () => {
    store.set('secret');

    http.post('/api/master/units', {}).subscribe();

    const request = httpMock.expectOne('/api/master/units');
    expect(request.request.headers.get('X-Admin-Key')).toBe('secret');
    request.flush({});
  });

  it('does not add the key to reads', () => {
    store.set('secret');

    http.get('/api/master/units').subscribe();

    const request = httpMock.expectOne('/api/master/units');
    expect(request.request.headers.has('X-Admin-Key')).toBe(false);
    request.flush([]);
  });

  it('does not add the key to other APIs', () => {
    store.set('secret');

    http.post('/api/other', {}).subscribe();

    const request = httpMock.expectOne('/api/other');
    expect(request.request.headers.has('X-Admin-Key')).toBe(false);
    request.flush({});
  });

  it('sends no header when no key is set', () => {
    http.post('/api/master/units', {}).subscribe();

    const request = httpMock.expectOne('/api/master/units');
    expect(request.request.headers.has('X-Admin-Key')).toBe(false);
    request.flush({});
  });
});
