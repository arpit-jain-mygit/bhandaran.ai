// ---------------------------------------------------------------
// Tests for Combobox: typing filters, clicking and Enter pick, the
// chosen label shows, ngModel gets the value, and clear resets it.
// ---------------------------------------------------------------
import { Component, signal } from '@angular/core';
import { TestBed } from '@angular/core/testing';
import { FormsModule } from '@angular/forms';

import { ComboOption, Combobox } from './combobox';

@Component({
  imports: [Combobox, FormsModule],
  template: `<app-combobox
    name="city"
    [options]="options"
    [allowClear]="true"
    [(ngModel)]="value"
  />`,
})
class Host {
  options: ComboOption[] = [
    { value: 'v', label: 'Vidisha' },
    { value: 's', label: 'Sironj' },
    { value: 'b', label: 'Bhopal' },
  ];
  value = signal('');
}

describe('Combobox', () => {
  async function setup(start = '') {
    TestBed.configureTestingModule({ imports: [Host] });
    const fixture = TestBed.createComponent(Host);
    fixture.componentInstance.value.set(start);
    fixture.detectChanges();
    await fixture.whenStable();
    fixture.detectChanges();
    const el = fixture.nativeElement as HTMLElement;
    const input = el.querySelector('input') as HTMLInputElement;
    return { fixture, el, input };
  }

  function type(input: HTMLInputElement, text: string) {
    input.value = text;
    input.dispatchEvent(new Event('input'));
  }

  function key(input: HTMLInputElement, name: string) {
    input.dispatchEvent(new KeyboardEvent('keydown', { key: name }));
  }

  it('shows the chosen label', async () => {
    const { input } = await setup('s');
    expect(input.value).toBe('Sironj');
  });

  it('filters the list as you type', async () => {
    const { fixture, el, input } = await setup();
    type(input, 'sh'); // matches only "Vidisha"... and nothing else
    fixture.detectChanges();
    const labels = [...el.querySelectorAll('li[role="option"]')].map((li) =>
      li.textContent?.trim(),
    );
    expect(labels).toEqual(['Vidisha']);
  });

  it('picks an option with a click', async () => {
    const { fixture, el, input } = await setup();
    input.dispatchEvent(new Event('focus'));
    fixture.detectChanges();
    const bhopal = [...el.querySelectorAll('li[role="option"]')].find((li) =>
      li.textContent?.includes('Bhopal'),
    ) as HTMLElement;
    bhopal.dispatchEvent(new MouseEvent('mousedown'));
    fixture.detectChanges();
    expect(fixture.componentInstance.value()).toBe('b');
    expect(input.value).toBe('Bhopal');
    expect(el.querySelector('ul')).toBeNull();
  });

  it('picks with the keyboard', async () => {
    const { fixture, input } = await setup();
    type(input, 'ir'); // Sironj
    key(input, 'Enter');
    fixture.detectChanges();
    expect(fixture.componentInstance.value()).toBe('s');
  });

  it('clears back to nothing chosen', async () => {
    const { fixture, el } = await setup('v');
    (el.querySelector('button.clear') as HTMLButtonElement).click();
    fixture.detectChanges();
    expect(fixture.componentInstance.value()).toBe('');
  });
});
