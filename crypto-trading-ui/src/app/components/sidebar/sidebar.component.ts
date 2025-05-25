import { Component } from '@angular/core';
import { RouterLink, RouterLinkActive } from '@angular/router';

@Component({
  selector: 'app-sidebar',
  standalone: true,
  imports: [RouterLink, RouterLinkActive],
  templateUrl: './sidebar.component.html',
  styleUrl: './sidebar.component.scss'
})
export class SidebarComponent {
  menuItems = [
    { 
      label: 'Dashboard', 
      icon: 'pi pi-chart-line', 
      route: '/dashboard' 
    },
    { 
      label: 'Trading History', 
      icon: 'pi pi-history', 
      route: '/history' 
    },
    { 
      label: 'Portfolio', 
      icon: 'pi pi-wallet', 
      route: '/portfolio' 
    }
  ];
}