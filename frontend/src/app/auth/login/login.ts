// ---------------------------------------------------------------
// Login page (M3): email address -> 6-digit code -> (new users only)
// name + "I am an Owner / Renter". Afterwards the user goes back to
// the page they wanted (?next=...) or to their own main screen.
// ---------------------------------------------------------------
import { Component, inject, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { HttpErrorResponse } from '@angular/common/http';
import { ActivatedRoute, Router } from '@angular/router';
import { Observable } from 'rxjs';

import { apiErrorMessage } from '../../core/api-error';
import { AuthService, User } from '../../core/auth.service';
import { GrainLoader } from '../../shared/grain-loader/grain-loader';

type Step = 'email' | 'code' | 'signup';

@Component({
  selector: 'app-login',
  imports: [FormsModule, GrainLoader],
  templateUrl: './login.html',
  styleUrl: './login.scss',
})
export class Login {
  private readonly auth = inject(AuthService);
  private readonly router = inject(Router);
  private readonly route = inject(ActivatedRoute);

  protected readonly step = signal<Step>('email');
  protected readonly busy = signal(false);
  protected readonly error = signal('');
  // Local development only: the server shows the code instead of SMS.
  protected readonly devCode = signal<string | null>(null);

  protected email = '';
  protected code = '';
  protected name = '';
  protected role: 'OWNER' | 'RENTER' = 'OWNER';
  private signupToken = '';

  // ---------- step 1: email ----------

  protected sendCode(): void {
    this.run(this.auth.requestOtp(this.email), (sent) => {
      this.devCode.set(sent.dev_code);
      this.code = '';
      this.step.set('code');
    });
  }

  // ---------- step 2: code ----------

  protected verify(): void {
    this.run(this.auth.verifyOtp(this.email, this.code), (result) => {
      if (result.status === 'logged_in' && result.user) {
        this.goOn(result.user);
      } else if (result.signup_token) {
        this.signupToken = result.signup_token;
        this.step.set('signup');
      }
    });
  }

  protected changeEmail(): void {
    this.error.set('');
    this.devCode.set(null);
    this.step.set('email');
  }

  // ---------- step 3: new account ----------

  protected createAccount(): void {
    this.run(
      this.auth.signup(this.signupToken, this.name, this.role),
      (user) => this.goOn(user),
      (error) => {
        // The sign-up window closed: start again with a fresh code.
        if (error.status !== 401) return false;
        this.signupToken = '';
        this.step.set('email');
        this.error.set('Your sign-up expired. Please request a new code.');
        return true;
      },
    );
  }

  // ---------- helpers ----------

  /** Back to the page the user wanted, else their own main screen. */
  private goOn(user: User): void {
    const next = this.route.snapshot.queryParamMap.get('next');
    // Only follow app-internal paths (never another website).
    const safeNext = next && next.startsWith('/') && !next.startsWith('//') ? next : null;
    this.router.navigateByUrl(safeNext ?? this.auth.homeFor(user));
  }

  /** Runs a request. onError returns true when it handled the error itself. */
  private run<T>(
    request: Observable<T>,
    onSuccess: (value: T) => void,
    onError?: (error: HttpErrorResponse) => boolean,
  ): void {
    this.busy.set(true);
    this.error.set('');
    request.subscribe({
      next: (value) => {
        this.busy.set(false);
        onSuccess(value);
      },
      error: (error: HttpErrorResponse) => {
        this.busy.set(false);
        if (!onError?.(error)) {
          this.error.set(apiErrorMessage(error));
        }
      },
    });
  }
}
