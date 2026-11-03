// ---------------------------------------------------------------
// Tests for Admin > Platform settings: shows settings, saves a
// platform value, and sets an owner's own value.
// ---------------------------------------------------------------
import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { TestBed } from '@angular/core/testing';
import { provideRouter } from '@angular/router';

import { Setting } from '../../core/settings.service';
import { SettingsAdmin } from './settings-admin';

const TIMEOUT: Setting = {
  key: 'renter_confirmation_timeout_days',
  label: 'Days to wait for renter confirmation',
  description: 'How long a renter has to confirm.',
  type: 'int',
  choices: [],
  min: 1,
  max: 30,
  owner_can_override: true,
  default: 3,
  value: 3,
  source: 'default',
};

const OWNER_ID = '3f2b8a1c-1111-4222-8333-944455556666';

describe('SettingsAdmin', () => {
  let httpMock: HttpTestingController;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [SettingsAdmin],
      providers: [provideRouter([]), provideHttpClient(), provideHttpClientTesting()],
    }).compileComponents();
    httpMock = TestBed.inject(HttpTestingController);
  });

  async function setup() {
    const fixture = TestBed.createComponent(SettingsAdmin);
    fixture.detectChanges();
    httpMock.expectOne('/api/settings').flush([TIMEOUT]);
    await fixture.whenStable();
    return fixture;
  }

  // Reach protected members the way the template does.
  type Page = {
    draft: Record<string, unknown>;
    ownerIdInput: string;
    ownerDraft: Record<string, unknown>;
    savePlatform(s: Setting): void;
    loadOwner(): void;
    saveOwner(row: { key: string; label: string }): void;
  };

  it('shows each setting with where its value comes from', async () => {
    const fixture = await setup();
    const text = (fixture.nativeElement as HTMLElement).textContent ?? '';

    expect(text).toContain('Days to wait for renter confirmation');
    expect(text).toContain('Default');
  });

  it('saves a new platform value', async () => {
    const fixture = await setup();
    const page = fixture.componentInstance as unknown as Page;
    page.draft[TIMEOUT.key] = 7;

    page.savePlatform(TIMEOUT);

    const request = httpMock.expectOne(`/api/settings/${TIMEOUT.key}`);
    expect(request.request.method).toBe('PUT');
    expect(request.request.body).toEqual({ value: 7 });
    request.flush([{ ...TIMEOUT, value: 7, source: 'platform' }]);
  });

  it("loads an owner and saves the owner's own value", async () => {
    const fixture = await setup();
    const page = fixture.componentInstance as unknown as Page;

    page.ownerIdInput = OWNER_ID;
    page.loadOwner();
    httpMock
      .expectOne(`/api/settings/owners/${OWNER_ID}`)
      .flush([{ key: TIMEOUT.key, label: TIMEOUT.label, value: 3, source: 'default' }]);

    page.ownerDraft[TIMEOUT.key] = 10;
    page.saveOwner({ key: TIMEOUT.key, label: TIMEOUT.label });

    const request = httpMock.expectOne(`/api/settings/owners/${OWNER_ID}/${TIMEOUT.key}`);
    expect(request.request.method).toBe('PUT');
    expect(request.request.body).toEqual({ value: 10 });
  });

  it('rejects an owner ID that is not a UUID', async () => {
    const fixture = await setup();
    const page = fixture.componentInstance as unknown as Page;

    page.ownerIdInput = 'not-an-id';
    page.loadOwner();
    await fixture.whenStable();

    httpMock.expectNone((r) => r.url.startsWith('/api/settings/owners'));
    expect((fixture.nativeElement as HTMLElement).textContent).toContain('must be a UUID');
  });
});
