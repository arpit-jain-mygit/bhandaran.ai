// ---------------------------------------------------------------
// Tests for Owner > Bookings: the form accepts a record-only booking
// (name, no email) and still asks for a name when there is no email.
// ---------------------------------------------------------------
import { provideHttpClient } from '@angular/common/http';
import { provideHttpClientTesting } from '@angular/common/http/testing';
import { TestBed } from '@angular/core/testing';
import { provideRouter } from '@angular/router';

import { OwnerBookings } from './owner-bookings';

describe('OwnerBookings form', () => {
  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [OwnerBookings],
      providers: [provideRouter([]), provideHttpClient(), provideHttpClientTesting()],
    }).compileComponents();
  });

  // Reach protected members the way the template does.
  type Form = {
    warehouseId: string;
    renterEmail: string;
    renterName: string;
    stockTypeId: string;
    quantity: number | null;
    startDate: string;
    endDate: string;
    rate: string;
    formProblems(): string[];
  };

  function form(): Form {
    const fixture = TestBed.createComponent(OwnerBookings);
    return fixture.componentInstance as unknown as Form;
  }

  function fillRest(page: Form): void {
    page.warehouseId = 'g1';
    page.stockTypeId = 's1';
    page.quantity = 10;
    page.startDate = '2030-01-01';
    page.endDate = '2030-02-01';
    page.rate = '12.5';
  }

  it('accepts a record-only booking with just a name', () => {
    const page = form();
    fillRest(page);
    page.renterName = 'Walk-in Ravi';

    expect(page.formProblems()).toEqual([]);
  });

  it('asks for a name or email when both are empty', () => {
    const page = form();
    fillRest(page);

    expect(page.formProblems()).toEqual(["the renter's name (or their email)"]);
  });

  it('accepts an email without a name', () => {
    const page = form();
    fillRest(page);
    page.renterEmail = 'renter@example.test';

    expect(page.formProblems()).toEqual([]);
  });
});
