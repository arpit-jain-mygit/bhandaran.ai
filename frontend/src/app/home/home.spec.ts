// ---------------------------------------------------------------
// Tests for the Home page: heading and the search form are shown.
// ---------------------------------------------------------------
import { provideHttpClient } from '@angular/common/http';
import { provideHttpClientTesting } from '@angular/common/http/testing';
import { TestBed } from '@angular/core/testing';
import { provideRouter } from '@angular/router';

import { Home } from './home';

describe('Home', () => {
  it('shows the heading and the search form', async () => {
    await TestBed.configureTestingModule({
      imports: [Home],
      providers: [provideHttpClient(), provideHttpClientTesting(), provideRouter([])],
    }).compileComponents();
    const fixture = TestBed.createComponent(Home);
    fixture.detectChanges();

    const element = fixture.nativeElement as HTMLElement;
    expect(element.querySelector('h1')?.textContent).toContain('Godown space');
    expect(element.querySelector('app-find-space')).not.toBeNull();
    expect(element.textContent).not.toContain('System status');
  });
});
