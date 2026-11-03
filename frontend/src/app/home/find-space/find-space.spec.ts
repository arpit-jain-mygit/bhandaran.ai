// ---------------------------------------------------------------
// Tests for the "Find space" dropdowns: lists load from the API,
// and choosing a state loads that state's cities.
// ---------------------------------------------------------------
import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { TestBed } from '@angular/core/testing';
import { provideRouter } from '@angular/router';

import { FindSpace } from './find-space';

const item = (id: string, name: string) => ({
  id,
  code: id.toUpperCase(),
  name,
  sort_order: 0,
  is_active: true,
});

describe('FindSpace', () => {
  let httpMock: HttpTestingController;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [FindSpace],
      providers: [provideHttpClient(), provideHttpClientTesting(), provideRouter([])],
    }).compileComponents();
    httpMock = TestBed.inject(HttpTestingController);
  });

  /** Answer the three list requests made on start-up. */
  function flushLists(): void {
    httpMock.expectOne((r) => r.url === '/api/master/states').flush([item('mp', 'Madhya Pradesh')]);
    httpMock
      .expectOne((r) => r.url === '/api/master/storage-types')
      .flush([item('cold', 'Cold storage')]);
    httpMock.expectOne((r) => r.url === '/api/master/stock-types').flush([item('wheat', 'Wheat')]);
  }

  /** Visible option texts of a <select>. */
  function options(element: HTMLElement, name: string): string[] {
    const select = element.querySelector(`select[name="${name}"]`) as HTMLSelectElement;
    return Array.from(select.options).map((option) => option.textContent?.trim() ?? '');
  }

  it('fills the dropdowns from master data', async () => {
    const fixture = TestBed.createComponent(FindSpace);
    fixture.detectChanges();
    flushLists();
    await fixture.whenStable();

    const element = fixture.nativeElement as HTMLElement;
    expect(options(element, 'state')).toContain('Madhya Pradesh');
    expect(options(element, 'storageType')).toContain('Cold storage');
    expect(options(element, 'stockType')).toContain('Wheat');
  });

  it('cascades state -> district -> city / town', async () => {
    const fixture = TestBed.createComponent(FindSpace);
    fixture.detectChanges();
    flushLists();
    await fixture.whenStable();
    const form = fixture.componentInstance as unknown as {
      onStateChange(id: string): void;
      onDistrictChange(id: string): void;
    };

    // User picks "Madhya Pradesh" -> its districts load.
    form.onStateChange('mp');
    const districts = httpMock.expectOne((r) => r.url === '/api/master/districts');
    expect(districts.request.params.get('state_id')).toBe('mp');
    districts.flush([{ id: 'ind-d', state_id: 'mp', name: 'Indore', is_active: true }]);
    await fixture.whenStable();
    expect(options(fixture.nativeElement, 'district')).toContain('Indore');

    // User picks the "Indore" district -> its towns load.
    form.onDistrictChange('ind-d');
    const cities = httpMock.expectOne((r) => r.url === '/api/master/cities');
    expect(cities.request.params.get('district_id')).toBe('ind-d');
    cities.flush([
      { id: 'mhow', district_id: 'ind-d', state_id: 'mp', name: 'Mhow', is_active: true },
    ]);
    await fixture.whenStable();
    expect(options(fixture.nativeElement, 'city')).toContain('Mhow');
  });

  it('clears district and town when the state changes', async () => {
    const fixture = TestBed.createComponent(FindSpace);
    fixture.detectChanges();
    flushLists();
    const form = fixture.componentInstance as unknown as {
      onStateChange(id: string): void;
      districtId: string;
      cityId: string;
    };
    form.districtId = 'old-district';
    form.cityId = 'old-town';

    form.onStateChange('mp');
    httpMock.expectOne((r) => r.url === '/api/master/districts').flush([]);

    expect(form.districtId).toBe('');
    expect(form.cityId).toBe('');
  });
});
