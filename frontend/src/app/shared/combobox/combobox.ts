// ---------------------------------------------------------------
// Combobox: a dropdown you can type into. Type to filter the list, or
// open it and pick. Works with ngModel like a <select>; the value is
// the chosen option's `value` ('' = nothing chosen).
//
// Keyboard: Down/Up move, Enter picks, Escape closes.
//
// Usage:
//   <app-combobox inputId="city" name="city" [options]="cityOptions()"
//     placeholder="Type or select a city" [(ngModel)]="cityId" />
// ---------------------------------------------------------------
import { Component, computed, forwardRef, input, signal } from '@angular/core';
import { ControlValueAccessor, NG_VALUE_ACCESSOR } from '@angular/forms';

import { Icon } from '../icon/icon';

export interface ComboOption {
  value: string;
  label: string;
}

/** Turn master-data rows ({id, name}) into combobox options. */
export function optionsFrom(items: readonly { id: string; name: string }[]): ComboOption[] {
  return items.map((item) => ({ value: item.id, label: item.name }));
}

let nextId = 0;

@Component({
  selector: 'app-combobox',
  imports: [Icon],
  templateUrl: './combobox.html',
  styleUrl: './combobox.scss',
  providers: [{ provide: NG_VALUE_ACCESSOR, useExisting: forwardRef(() => Combobox), multi: true }],
})
export class Combobox implements ControlValueAccessor {
  readonly options = input<ComboOption[]>([]);
  readonly placeholder = input('Type or select');
  /** Show an "x" to go back to nothing chosen (e.g. for "Any" filters). */
  readonly allowClear = input(false);
  /** id for the text box, so a <label for="..."> can point at it. */
  readonly inputId = input(`combo-${nextId++}`);
  readonly emptyText = input('No matches');

  protected readonly listId = `combo-list-${nextId++}`;
  protected readonly value = signal('');
  protected readonly query = signal('');
  protected readonly typing = signal(false);
  protected readonly open = signal(false);
  protected readonly active = signal(0);
  protected readonly disabled = signal(false);

  /** Label of the chosen option (shown when not typing). */
  protected readonly selectedLabel = computed(
    () => this.options().find((option) => option.value === this.value())?.label ?? '',
  );

  /** Options matching what was typed (all of them when not typing). */
  protected readonly shown = computed(() => {
    const words = this.typing() ? this.query().trim().toLowerCase() : '';
    const all = this.options();
    return words ? all.filter((option) => option.label.toLowerCase().includes(words)) : all;
  });

  protected readonly text = computed(() => (this.typing() ? this.query() : this.selectedLabel()));

  private onChange: (value: string) => void = () => {};
  private onTouched: () => void = () => {};

  // ---------- user actions ----------

  protected onInput(text: string): void {
    this.typing.set(true);
    this.query.set(text);
    this.active.set(0);
    this.open.set(true);
  }

  protected openList(): void {
    if (this.disabled()) return;
    const index = this.shown().findIndex((option) => option.value === this.value());
    this.active.set(Math.max(index, 0));
    this.open.set(true);
  }

  protected toggle(): void {
    if (this.open()) {
      this.close();
    } else {
      this.openList();
    }
  }

  protected onKeydown(event: KeyboardEvent): void {
    const count = this.shown().length;
    switch (event.key) {
      case 'ArrowDown':
        event.preventDefault();
        if (!this.open()) {
          this.openList();
        } else if (count) {
          this.active.set((this.active() + 1) % count);
        }
        break;
      case 'ArrowUp':
        event.preventDefault();
        if (count) this.active.set((this.active() - 1 + count) % count);
        break;
      case 'Enter':
        if (this.open() && count) {
          event.preventDefault();
          this.choose(this.shown()[Math.min(this.active(), count - 1)]);
        }
        break;
      case 'Escape':
        if (this.open()) {
          event.preventDefault();
          this.close();
        }
        break;
    }
  }

  protected choose(option: ComboOption): void {
    this.value.set(option.value);
    this.close();
    this.onChange(option.value);
    this.onTouched();
  }

  protected clear(): void {
    this.choose({ value: '', label: '' });
  }

  /** Leaving the box: close the list and show the chosen label again. */
  protected onBlur(): void {
    this.close();
    this.onTouched();
  }

  private close(): void {
    this.open.set(false);
    this.typing.set(false);
    this.query.set('');
  }

  // ---------- ControlValueAccessor (makes ngModel work) ----------

  writeValue(value: string | null): void {
    this.value.set(value ?? '');
  }

  registerOnChange(fn: (value: string) => void): void {
    this.onChange = fn;
  }

  registerOnTouched(fn: () => void): void {
    this.onTouched = fn;
  }

  setDisabledState(disabled: boolean): void {
    this.disabled.set(disabled);
    if (disabled) this.close();
  }
}
