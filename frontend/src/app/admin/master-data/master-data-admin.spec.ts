// ---------------------------------------------------------------
// Tests for Admin > Master data: the table shows items (including
// disabled ones), and "Disable" sends the right PATCH.
// ---------------------------------------------------------------
import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { TestBed } from '@angular/core/testing';

import { MasterDataAdmin } from './master-data-admin';

const wheat = { id: 'w1', code: 'WHEAT', name: 'Wheat', sort_order: 10, is_active: true };
const old = { id: 'o1', code: 'OLD', name: 'Old crop', sort_order: 20, is_active: false };

describe('MasterDataAdmin', () => {
  let httpMock: HttpTestingController;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [MasterDataAdmin],
      providers: [provideHttpClient(), provideHttpClientTesting()],
    }).compileComponents();
    httpMock = TestBed.inject(HttpTestingController);
  });

  /** Create the page and answer its two start-up requests. */
  async function setup() {
    const fixture = TestBed.createComponent(MasterDataAdmin);
    fixture.detectChanges();
    httpMock.expectOne((r) => r.url === '/api/master/states').flush([]);
    const list = httpMock.expectOne((r) => r.url === '/api/master/stock-types');
    expect(list.request.params.get('include_inactive')).toBe('true');
    list.flush([wheat, old]);
    await fixture.whenStable();
    return fixture;
  }

  it('lists active and disabled items', async () => {
    const fixture = await setup();
    const rows = (fixture.nativeElement as HTMLElement).querySelectorAll('tbody tr');

    expect(rows.length).toBe(2);
    expect(rows[1].classList).toContain('inactive');
  });

  it('sends is_active=false when "Disable" is clicked', async () => {
    const fixture = await setup();
    const disable = Array.from(
      (fixture.nativeElement as HTMLElement).querySelectorAll('button'),
    ).find((button) => button.textContent?.trim() === 'Disable') as HTMLButtonElement;

    disable.click();

    const request = httpMock.expectOne('/api/master/stock-types/w1');
    expect(request.request.method).toBe('PATCH');
    expect(request.request.body).toEqual({ is_active: false });
  });
});
