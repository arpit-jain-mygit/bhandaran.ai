// ---------------------------------------------------------------
// Root component: the app "shell" (header with nav + page area).
// Pages are swapped inside <router-outlet> based on the URL
// (routes are listed in app.routes.ts).
// ---------------------------------------------------------------
import { Component } from '@angular/core';
import { RouterLink, RouterLinkActive, RouterOutlet } from '@angular/router';

@Component({
  selector: 'app-root',
  imports: [RouterOutlet, RouterLink, RouterLinkActive],
  templateUrl: './app.html',
  styleUrl: './app.scss',
})
export class App {}
