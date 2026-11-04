// ---------------------------------------------------------------
// Admin > Delete test data. Step 1: list what would be removed.
// Step 2: type DELETE and confirm. Nothing is removed until step 2.
// ---------------------------------------------------------------
import { Component, inject, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { Observable } from 'rxjs';

import { apiErrorMessage } from '../../core/api-error';
import { CleanupPlan, CleanupRequest, CleanupService } from '../../core/cleanup.service';
import { GrainLoader } from '../../shared/grain-loader/grain-loader';
import { Icon } from '../../shared/icon/icon';
import { AdminHeader } from '../admin-header/admin-header';

const UUID_PATTERN = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;

// Emails and IDs can be separated by commas, spaces or new lines.
function split(text: string): string[] {
  return [
    ...new Set(
      text
        .split(/[\s,]+/)
        .map((item) => item.trim())
        .filter(Boolean),
    ),
  ];
}

@Component({
  selector: 'app-test-data-admin',
  imports: [FormsModule, GrainLoader, Icon, AdminHeader],
  templateUrl: './test-data-admin.html',
  styleUrl: './test-data-admin.scss',
})
export class TestDataAdmin {
  private readonly api = inject(CleanupService);

  protected emailsText = '';
  protected godownsText = '';
  protected confirmText = '';

  protected readonly busy = signal(false);
  protected readonly error = signal('');
  protected readonly notice = signal('');
  // What the last preview found. Cleared when the inputs change.
  protected readonly plan = signal<CleanupPlan | null>(null);

  /** Deleting needs a fresh preview and the word DELETE typed exactly. */
  protected canDelete(): boolean {
    return this.plan() !== null && this.confirmText === 'DELETE' && !this.busy();
  }

  private request(): CleanupRequest {
    return { emails: split(this.emailsText), warehouse_ids: split(this.godownsText) };
  }

  protected check(): void {
    const request = this.request();
    const badId = request.warehouse_ids.find((id) => !UUID_PATTERN.test(id));
    if (badId) {
      this.error.set(
        `"${badId}" is not a godown ID. IDs look like 3f2b8a1c-1234-4abc-8def-0123456789ab. Use the ID from the godown's page address, not its name.`,
      );
      return;
    }
    if (!request.emails.length && !request.warehouse_ids.length) {
      this.error.set('Enter at least one email or godown ID.');
      return;
    }
    this.run(this.api.preview(request), (plan) => this.plan.set(plan));
  }

  protected remove(): void {
    if (!this.canDelete()) return;
    this.run(this.api.remove(this.request()), (plan) => {
      this.notice.set(this.summary(plan, 'Deleted.'));
      this.plan.set(null);
      this.confirmText = '';
      this.emailsText = '';
      this.godownsText = '';
      if (plan.photo_files_left) {
        this.error.set(`${plan.photo_files_left} photo file(s) could not be removed from storage.`);
      }
    });
  }

  /** A change to the inputs makes the old preview out of date. */
  protected inputsChanged(): void {
    this.plan.set(null);
    this.confirmText = '';
  }

  private summary(plan: CleanupPlan, lead: string): string {
    const parts = [
      `${plan.accounts.length} account(s)`,
      `${plan.warehouses} godown(s)`,
      `${plan.bookings} booking(s)`,
      `${plan.photos} photo(s)`,
    ];
    return `${lead} ${parts.join(', ')}.`;
  }

  private run(request: Observable<CleanupPlan>, onDone: (plan: CleanupPlan) => void): void {
    this.busy.set(true);
    this.error.set('');
    this.notice.set('');
    request.subscribe({
      next: (plan) => {
        this.busy.set(false);
        onDone(plan);
      },
      error: (error) => {
        this.busy.set(false);
        this.error.set(apiErrorMessage(error));
      },
    });
  }
}
