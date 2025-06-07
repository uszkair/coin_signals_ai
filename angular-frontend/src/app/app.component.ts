import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterOutlet } from '@angular/router';
import { SidebarComponent } from './components/sidebar/sidebar.component';
import { AiChatComponent } from './components/ai-chat/ai-chat.component';
import { SmartNotificationsComponent } from './components/smart-notifications/smart-notifications.component';

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [
    CommonModule,
    RouterOutlet,
    SidebarComponent,
    AiChatComponent,
    SmartNotificationsComponent
  ],
  templateUrl: './app.component.html',
  styleUrls: []
})
export class AppComponent {
  title = 'Coin Signals AI Frontend';
}