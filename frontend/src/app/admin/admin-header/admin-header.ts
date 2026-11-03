// ---------------------------------------------------------------
// Top of every admin page: the admin menu (Master data, Platform
// settings) and the TEMPORARY admin-key box (until M3 login).
// ---------------------------------------------------------------
import { Component, inject, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { RouterLink, RouterLinkActive } from '@angular/router';

import { AdminKeyStore } from '../../core/admin-key';

@Component({
  selector: 'app-admin-header',
  imports: [FormsModule, RouterLink, RouterLinkActive],
  templateUrl: './admin-header.html',
  styleUrl: './admin-header.scss',
})
export class AdminHeader {
  protected readonly adminKey = inject(AdminKeyStore);

  // Text in the key box (saved only when "Save key" is pressed).
  protected keyInput = this.adminKey.key();
  protected readonly saved = signal('');

  protected saveKey(): void {
    this.adminKey.set(this.keyInput);
    this.saved.set(this.keyInput.trim() ? 'Saved for this tab.' : 'Cleared.');
  }
}
