import { Component, OnInit, OnDestroy, ViewChild, ElementRef } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ButtonModule } from 'primeng/button';
import { DialogModule } from 'primeng/dialog';
import { InputTextModule } from 'primeng/inputtext';
import { AvatarModule } from 'primeng/avatar';
import { BadgeModule } from 'primeng/badge';
import { TooltipModule } from 'primeng/tooltip';
import { AIService, ChatMessage } from '../../services/ai.service';
import { Subscription } from 'rxjs';

@Component({
  selector: 'app-ai-chat',
  standalone: true,
  imports: [
    CommonModule,
    FormsModule,
    ButtonModule,
    DialogModule,
    InputTextModule,
    AvatarModule,
    BadgeModule,
    TooltipModule
  ],
  templateUrl: './ai-chat.component.html'
})
export class AiChatComponent implements OnInit, OnDestroy {
  @ViewChild('chatMessages') chatMessagesContainer!: ElementRef;
  
  isOpen = false;
  messages: ChatMessage[] = [];
  newMessage = '';
  isTyping = false;
  unreadCount = 0;
  
  private subscription = new Subscription();

  constructor(private aiService: AIService) {}

  ngOnInit(): void {
    this.subscription.add(
      this.aiService.chatMessages$.subscribe(messages => {
        const previousCount = this.messages.length;
        this.messages = messages;
        
        // Update unread count if chat is closed
        if (!this.isOpen && messages.length > previousCount) {
          this.unreadCount += messages.length - previousCount;
        }
        
        // Auto-scroll to bottom
        setTimeout(() => this.scrollToBottom(), 100);
      })
    );
  }

  ngOnDestroy(): void {
    this.subscription.unsubscribe();
  }

  toggleChat(): void {
    this.isOpen = !this.isOpen;
    if (this.isOpen) {
      this.unreadCount = 0;
      setTimeout(() => this.scrollToBottom(), 100);
    }
  }

  closeChat(): void {
    this.isOpen = false;
  }

  sendMessage(): void {
    if (!this.newMessage.trim()) return;

    // Add user message
    const userMessage: ChatMessage = {
      message: this.newMessage,
      isUser: true,
      timestamp: new Date()
    };
    this.aiService.addChatMessage(userMessage);

    const messageToSend = this.newMessage;
    this.newMessage = '';
    this.isTyping = true;

    // Send to AI service
    this.aiService.sendChatMessage(messageToSend).subscribe({
      next: (response) => {
        this.isTyping = false;
        if (response.success) {
          const aiMessage: ChatMessage = {
            message: response.data.response,
            isUser: false,
            timestamp: new Date(),
            suggestions: response.data.suggestions
          };
          this.aiService.addChatMessage(aiMessage);
        }
      },
      error: (error) => {
        this.isTyping = false;
        console.error('Chat error:', error);
        const errorMessage: ChatMessage = {
          message: 'Sorry, I encountered an error. Please try again.',
          isUser: false,
          timestamp: new Date()
        };
        this.aiService.addChatMessage(errorMessage);
      }
    });
  }

  selectSuggestion(suggestion: string): void {
    this.newMessage = suggestion;
    this.sendMessage();
  }

  onKeyPress(event: KeyboardEvent): void {
    if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault();
      this.sendMessage();
    }
  }

  clearChat(): void {
    this.aiService.clearChatMessages();
  }

  private scrollToBottom(): void {
    if (this.chatMessagesContainer) {
      const element = this.chatMessagesContainer.nativeElement;
      element.scrollTop = element.scrollHeight;
    }
  }

  formatTime(timestamp: Date): string {
    return timestamp.toLocaleTimeString('en-US', { 
      hour: '2-digit', 
      minute: '2-digit' 
    });
  }
}