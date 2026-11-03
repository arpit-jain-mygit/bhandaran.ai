// ---------------------------------------------------------------
// Root component: the app "shell" (header + page area).
// Pages are swapped inside <router-outlet> based on the URL
// (routes are listed in app.routes.ts).
// ---------------------------------------------------------------
import { Component } from '@angular/core';
import { RouterOutlet } from '@angular/router';

@Component({
  selector: 'app-root',
  imports: [RouterOutlet],
  templateUrl: './app.html',
  styleUrl: './app.scss',
})
export class App {}
