// ---------------------------------------------------------------
// Icon: small line icons drawn as inline SVG (no icon font, no extra
// package). They take the text colour (currentColor) and are hidden
// from screen readers, so always put text or an aria-label next to one.
//
// Usage: <app-icon name="search" />   <app-icon name="user" [size]="20" />
// ---------------------------------------------------------------
import { Component, input } from '@angular/core';

export type IconName =
  | 'arrow-left'
  | 'calendar'
  | 'check'
  | 'chevron-down'
  | 'clipboard'
  | 'home'
  | 'image'
  | 'list'
  | 'log-in'
  | 'log-out'
  | 'mail'
  | 'map-pin'
  | 'menu'
  | 'package'
  | 'plus'
  | 'save'
  | 'search'
  | 'send'
  | 'shield'
  | 'sliders'
  | 'trash'
  | 'user'
  | 'user-plus'
  | 'warehouse'
  | 'x';

@Component({
  selector: 'app-icon',
  templateUrl: './icon.html',
  styleUrl: './icon.scss',
})
export class Icon {
  readonly name = input.required<IconName>();
  readonly size = input(18);
}
