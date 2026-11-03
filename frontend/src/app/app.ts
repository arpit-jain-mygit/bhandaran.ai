// ---------------------------------------------------------------
// Root component: the app "shell" (header with nav + page area).
// Pages are swapped inside <router-outlet> based on the URL
// (routes are listed in app.routes.ts).
// ---------------------------------------------------------------
import { Component, OnInit, inject } from '@angular/core';
import { Router, RouterLink, RouterLinkActive, RouterOutlet } from '@angular/router';

import { AuthService } from './core/auth.service';

@Component({
  selector: 'app-root',
  imports: [RouterOutlet, RouterLink, RouterLinkActive],
  templateUrl: './app.html',
  styleUrl: './app.scss',
})
export class App implements OnInit {
  protected readonly auth = inject(AuthService);
  private readonly router = inject(Router);

  // Find out once at start-up who is logged in (cookie check).
  ngOnInit(): void {
    this.auth.ensureLoaded().subscribe();
  }

  protected logout(): void {
    this.auth.logout().subscribe(() => this.router.navigateByUrl('/'));
  }
}
