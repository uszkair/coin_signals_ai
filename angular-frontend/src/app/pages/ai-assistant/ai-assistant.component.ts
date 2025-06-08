import { Component, OnInit, ViewChild } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterModule } from '@angular/router';
import { FormsModule } from '@angular/forms';
import { AiChatComponent } from '../../components/ai-chat/ai-chat.component';
import { SmartNotificationsComponent } from '../../components/smart-notifications/smart-notifications.component';
import { CardModule } from 'primeng/card';
import { ButtonModule } from 'primeng/button';
import { TabViewModule } from 'primeng/tabview';
import { DividerModule } from 'primeng/divider';

@Component({
  selector: 'app-ai-assistant',
  standalone: true,
  imports: [
    CommonModule,
    RouterModule,
    FormsModule,
    AiChatComponent,
    SmartNotificationsComponent,
    CardModule,
    ButtonModule,
    TabViewModule,
    DividerModule
  ],
  templateUrl: './ai-assistant.component.html'
})
export class AiAssistantComponent implements OnInit {
  @ViewChild(AiChatComponent) aiChatComponent!: AiChatComponent;

  ngOnInit() {
    // Component initialization
  }

  openChat() {
    if (this.aiChatComponent) {
      this.aiChatComponent.isOpen = true;
    }
  }

  closeChat() {
    if (this.aiChatComponent) {
      this.aiChatComponent.closeChat();
    }
  }
}