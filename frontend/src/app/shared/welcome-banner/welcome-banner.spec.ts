// ---------------------------------------------------------------
// Tests for WelcomeBanner: greeting, role, message and the button.
// ---------------------------------------------------------------
import { TestBed } from '@angular/core/testing';
import { provideRouter } from '@angular/router';

import { WelcomeBanner } from './welcome-banner';

describe('WelcomeBanner', () => {
  function render(inputs: Record<string, string | null>) {
    TestBed.configureTestingModule({ providers: [provideRouter([])] });
    const fixture = TestBed.createComponent(WelcomeBanner);
    for (const [key, value] of Object.entries(inputs)) {
      fixture.componentRef.setInput(key, value);
    }
    fixture.detectChanges();
    return fixture.nativeElement as HTMLElement;
  }

  it('greets the user by name with their role and button', () => {
    const el = render({
      name: 'Kesar',
      role: 'Godown owner',
      message: 'List your space.',
      actionLabel: 'Add a godown',
      actionLink: '/owner/warehouses/new',
    });
    expect(el.querySelector('h1')?.textContent).toContain('Namaste, Kesar');
    expect(el.querySelector('.role')?.textContent).toContain('Godown owner');
    const action = el.querySelector('a.action') as HTMLAnchorElement;
    expect(action.textContent).toContain('Add a godown');
    expect(action.getAttribute('href')).toBe('/owner/warehouses/new');
  });

  it('falls back to a friendly greeting without a name', () => {
    const el = render({ name: null });
    expect(el.querySelector('h1')?.textContent).toContain('Namaste, friend');
    expect(el.querySelector('a.action')).toBeNull();
  });
});
