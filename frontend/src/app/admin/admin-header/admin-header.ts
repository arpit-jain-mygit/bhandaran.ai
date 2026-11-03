// ---------------------------------------------------------------
// Top of every admin page: the admin menu (Master data, Platform
// settings). Access itself is checked by the route guard (ADMIN role)
// and again by the API.
// ---------------------------------------------------------------
import { Component } from '@angular/core';
import { RouterLink, RouterLinkActive } from '@angular/router';

@Component({
  selector: 'app-admin-header',
  imports: [RouterLink, RouterLinkActive],
  templateUrl: './admin-header.html',
  styleUrl: './admin-header.scss',
})
export class AdminHeader {}
