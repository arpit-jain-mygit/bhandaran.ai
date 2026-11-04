// ---------------------------------------------------------------
// Tests for Admin > Delete test data: a preview comes first, and
// delete stays locked until DELETE is typed exactly.
// ---------------------------------------------------------------
import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { TestBed } from '@angular/core/testing';
import { provideRouter } from '@angular/router';

import { CleanupPlan } from '../../core/cleanup.service';
import { TestDataAdmin } from './test-data-admin';

const PLAN: CleanupPlan = {
  accounts: ['ow***@example.test'],
  missing_emails: [],
  warehouses: 1,
  missing_warehouse_ids: [],
  bookings: 0,
  photos: 0,
  login_codes: 0,
  owner_settings: 0,
  suppressed_emails: 0,
  invitees_released: 0,
  deleted: false,
  photo_files_left: 0,
};

describe('TestDataAdmin', () => {
  let httpMock: HttpTestingController;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [TestDataAdmin],
      providers: [provideRouter([]), provideHttpClient(), provideHttpClientTesting()],
    }).compileComponents();
    httpMock = TestBed.inject(HttpTestingController);
  });

  // Reach protected members the way the template does.
  type Page = {
    emailsText: string;
    confirmText: string;
    check(): void;
    remove(): void;
    canDelete(): boolean;
  };

  it('asks for a check before anything can be deleted', () => {
    const fixture = TestBed.createComponent(TestDataAdmin);
    const page = fixture.componentInstance as unknown as Page;
    page.emailsText = 'owner@example.test';
    page.confirmText = 'DELETE';

    expect(page.canDelete()).toBe(false);
  });

  it('lists the preview, then deletes only after DELETE is typed', () => {
    const fixture = TestBed.createComponent(TestDataAdmin);
    const page = fixture.componentInstance as unknown as Page;
    page.emailsText = 'owner@example.test';

    page.check();
    httpMock.expectOne('/api/admin/test-data/preview').flush(PLAN);
    expect(page.canDelete()).toBe(false);

    page.confirmText = 'delete';
    expect(page.canDelete()).toBe(false);

    page.confirmText = 'DELETE';
    expect(page.canDelete()).toBe(true);

    page.remove();
    const request = httpMock.expectOne('/api/admin/test-data/delete');
    expect(request.request.body).toEqual({
      emails: ['owner@example.test'],
      warehouse_ids: [],
      confirm: 'DELETE',
    });
    request.flush({ ...PLAN, deleted: true });
  });

  it('refuses to check with nothing entered', () => {
    const fixture = TestBed.createComponent(TestDataAdmin);
    const page = fixture.componentInstance as unknown as Page;

    page.check();

    httpMock.expectNone('/api/admin/test-data/preview');
  });

  it('explains when a godown name is typed instead of its ID', () => {
    const fixture = TestBed.createComponent(TestDataAdmin);
    const page = fixture.componentInstance as unknown as Page & {
      godownsText: string;
      error(): string;
    };
    page.godownsText = 'Kesar-Big';

    page.check();

    httpMock.expectNone('/api/admin/test-data/preview');
    expect(fixture.componentInstance['error']()).toContain('not a godown ID');
  });
});
