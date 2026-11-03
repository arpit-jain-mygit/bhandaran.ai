// ---------------------------------------------------------------
// Tests for the grain-ring loading spinner.
// ---------------------------------------------------------------
import { TestBed } from '@angular/core/testing';

import { GrainLoader } from './grain-loader';

describe('GrainLoader', () => {
  beforeEach(async () => {
    await TestBed.configureTestingModule({ imports: [GrainLoader] }).compileComponents();
  });

  it('draws a ring of 12 grains: wheat, moong, masoor dal and kala chana', async () => {
    const fixture = TestBed.createComponent(GrainLoader);
    await fixture.whenStable();
    const element = fixture.nativeElement as HTMLElement;

    expect(element.querySelectorAll('.grain').length).toBe(12);
    for (const kind of ['wheat', 'moong', 'dal', 'chana']) {
      expect(element.querySelectorAll(`.grain.${kind}`).length).toBe(3);
    }
  });

  it('announces its label to screen readers and hides the drawing', async () => {
    const fixture = TestBed.createComponent(GrainLoader);
    fixture.componentRef.setInput('label', 'Checking API');
    await fixture.whenStable();
    const element = fixture.nativeElement as HTMLElement;

    expect(element.querySelector('[role="status"]')?.textContent?.trim()).toBe('Checking API');
    expect(element.querySelector('svg')?.getAttribute('aria-hidden')).toBe('true');
  });

  it('uses the requested size', async () => {
    const fixture = TestBed.createComponent(GrainLoader);
    fixture.componentRef.setInput('size', 24);
    await fixture.whenStable();
    const box = (fixture.nativeElement as HTMLElement).querySelector('.loader') as HTMLElement;

    expect(box.style.width).toBe('24px');
    expect(box.style.height).toBe('24px');
  });
});
