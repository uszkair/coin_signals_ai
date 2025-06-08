import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';

// PrimeNG imports
import { CardModule } from 'primeng/card';
import { ButtonModule } from 'primeng/button';
import { InputNumberModule } from 'primeng/inputnumber';
import { RadioButtonModule } from 'primeng/radiobutton';
import { ToastModule } from 'primeng/toast';
import { ProgressSpinnerModule } from 'primeng/progressspinner';
import { DividerModule } from 'primeng/divider';
import { MessageService } from 'primeng/api';

import { TradingService, PositionSizeConfig } from '../../services/trading.service';

@Component({
  selector: 'app-position-size-settings',
  standalone: true,
  imports: [
    CommonModule,
    FormsModule,
    CardModule,
    ButtonModule,
    InputNumberModule,
    RadioButtonModule,
    ToastModule,
    ProgressSpinnerModule,
    DividerModule
  ],
  providers: [MessageService],
  template: `
    <p-card header="Pozíció Méret Beállítások" styleClass="mb-4">
      <div class="grid">
        <div class="col-12">
          <div class="field">
            <label class="text-lg font-semibold mb-3 block">Pozíció Méret Módja</label>
            
            <div class="flex flex-column gap-3">
              <div class="flex align-items-center">
                <p-radioButton 
                  name="mode" 
                  value="percentage" 
                  [(ngModel)]="config.mode"
                  inputId="percentage"
                  (onChange)="onModeChange()">
                </p-radioButton>
                <label for="percentage" class="ml-2 cursor-pointer">
                  <strong>Százalékos</strong> - A portfólió százaléka alapján
                </label>
              </div>
              
              <div class="flex align-items-center">
                <p-radioButton 
                  name="mode" 
                  value="fixed_usd" 
                  [(ngModel)]="config.mode"
                  inputId="fixed_usd"
                  (onChange)="onModeChange()">
                </p-radioButton>
                <label for="fixed_usd" class="ml-2 cursor-pointer">
                  <strong>Fix USD összeg</strong> - Minden kereskedéshez ugyanaz az összeg
                </label>
              </div>
            </div>
          </div>
        </div>

        <div class="col-12">
          <p-divider></p-divider>
        </div>

        <!-- Percentage Mode Settings -->
        <div class="col-12" *ngIf="config.mode === 'percentage'">
          <div class="field">
            <label for="maxPercentage" class="block text-900 font-medium mb-2">
              Maximum Százalék (%)
            </label>
            <p-inputNumber
              id="maxPercentage"
              [(ngModel)]="config.max_percentage"
              [min]="0.1"
              [max]="10"
              [step]="0.1"
              suffix="%"
              placeholder="pl. 2.5"
              styleClass="w-full">
            </p-inputNumber>
            <small class="text-600">
              Minden kereskedés maximum ennyi százalékot használ a teljes portfólióból (0.1% - 10%)
            </small>
          </div>

          <div class="bg-blue-50 border-left-3 border-blue-500 p-3 mt-3" *ngIf="config.max_percentage && walletBalance">
            <div class="text-blue-900">
              <i class="pi pi-info-circle mr-2"></i>
              <strong>Példa számítás:</strong>
            </div>
            <div class="text-blue-800 mt-2">
              Jelenlegi portfólió: <strong>\${{ walletBalance | number:'1.2-2' }}</strong><br>
              {{ config.max_percentage }}% = <strong>\${{ calculateExampleAmount() | number:'1.2-2' }}</strong> per kereskedés
            </div>
          </div>
        </div>

        <!-- Fixed USD Mode Settings -->
        <div class="col-12" *ngIf="config.mode === 'fixed_usd'">
          <div class="field">
            <label for="fixedAmount" class="block text-900 font-medium mb-2">
              Fix USD Összeg
            </label>
            <p-inputNumber
              id="fixedAmount"
              [(ngModel)]="config.fixed_amount_usd"
              [min]="1"
              [max]="10000"
              [step]="1"
              prefix="$"
              placeholder="pl. 100"
              styleClass="w-full">
            </p-inputNumber>
            <small class="text-600">
              Minden kereskedés pontosan ezt az összeget használja ($1 - $10,000)
            </small>
          </div>

          <div class="bg-orange-50 border-left-3 border-orange-500 p-3 mt-3" *ngIf="config.fixed_amount_usd && walletBalance">
            <div class="text-orange-900">
              <i class="pi pi-exclamation-triangle mr-2"></i>
              <strong>Figyelem:</strong>
            </div>
            <div class="text-orange-800 mt-2">
              Fix összeg: <strong>\${{ config.fixed_amount_usd }}</strong><br>
              Ez a portfólió <strong>{{ (config.fixed_amount_usd / walletBalance * 100) | number:'1.1-1' }}%-a</strong>
              <span *ngIf="(config.fixed_amount_usd / walletBalance * 100) > 5" class="text-red-600">
                <br><i class="pi pi-exclamation-triangle"></i> Magas kockázat! (>5%)
              </span>
            </div>
          </div>
        </div>

        <div class="col-12">
          <p-divider></p-divider>
        </div>

        <div class="col-12">
          <div class="flex justify-content-between align-items-center">
            <p-button 
              label="Betöltés" 
              icon="pi pi-refresh" 
              severity="secondary"
              [loading]="loading"
              (onClick)="loadConfig()">
            </p-button>
            
            <p-button 
              label="Mentés" 
              icon="pi pi-save" 
              [loading]="saving"
              [disabled]="!isConfigValid()"
              (onClick)="saveConfig()">
            </p-button>
          </div>
        </div>

        <div class="col-12" *ngIf="currentConfig">
          <div class="bg-gray-50 border-round p-3">
            <div class="text-900 font-semibold mb-2">
              <i class="pi pi-cog mr-2"></i>Jelenlegi Beállítás
            </div>
            <div class="text-700">
              <strong>Mód:</strong> {{ currentConfig.mode === 'percentage' ? 'Százalékos' : 'Fix USD' }}<br>
              <span *ngIf="currentConfig.mode === 'percentage'">
                <strong>Maximum százalék:</strong> {{ currentConfig.max_percentage }}%
              </span>
              <span *ngIf="currentConfig.mode === 'fixed_usd'">
                <strong>Fix összeg:</strong> ${{ currentConfig.fixed_amount_usd }}
              </span>
            </div>
          </div>
        </div>
      </div>
    </p-card>

    <p-toast></p-toast>
  `,
  styles: [`
    :host {
      display: block;
    }
    
    .field {
      margin-bottom: 1rem;
    }
    
    .cursor-pointer {
      cursor: pointer;
    }
  `]
})
export class PositionSizeSettingsComponent implements OnInit {
  config: PositionSizeConfig = {
    mode: 'percentage',
    max_percentage: 2.0,
    fixed_amount_usd: 100
  };

  currentConfig: any = null;
  walletBalance: number = 0;
  loading = false;
  saving = false;

  constructor(
    private tradingService: TradingService,
    private messageService: MessageService
  ) {}

  ngOnInit(): void {
    this.loadConfig();
    this.loadWalletBalance();
  }

  loadConfig(): void {
    this.loading = true;
    
    this.tradingService.getPositionSizeConfig().subscribe({
      next: (response) => {
        this.loading = false;
        if (response.success) {
          this.currentConfig = response.data;
          this.config = {
            mode: response.data.mode,
            max_percentage: response.data.max_percentage,
            fixed_amount_usd: response.data.fixed_amount_usd
          };
        }
      },
      error: (error) => {
        this.loading = false;
        this.messageService.add({
          severity: 'error',
          summary: 'Hiba',
          detail: 'Nem sikerült betölteni a beállításokat: ' + error.message,
          life: 5000
        });
      }
    });
  }

  loadWalletBalance(): void {
    this.tradingService.getWalletBalance().subscribe({
      next: (response) => {
        if (response.success) {
          this.walletBalance = response.data.total_balance_usdt || 0;
        }
      },
      error: (error) => {
        console.warn('Could not load wallet balance:', error);
      }
    });
  }

  saveConfig(): void {
    if (!this.isConfigValid()) {
      this.messageService.add({
        severity: 'warn',
        summary: 'Érvénytelen Beállítás',
        detail: 'Kérlek töltsd ki az összes kötelező mezőt',
        life: 5000
      });
      return;
    }

    this.saving = true;

    this.tradingService.updatePositionSizeConfig(this.config).subscribe({
      next: (response) => {
        this.saving = false;
        if (response.success) {
          this.currentConfig = response.data;
          this.messageService.add({
            severity: 'success',
            summary: 'Beállítások Mentve',
            detail: 'A pozíció méret beállítások sikeresen frissítve',
            life: 5000
          });
        } else {
          this.messageService.add({
            severity: 'error',
            summary: 'Mentési Hiba',
            detail: response.error || 'Ismeretlen hiba történt',
            life: 5000
          });
        }
      },
      error: (error) => {
        this.saving = false;
        this.messageService.add({
          severity: 'error',
          summary: 'Hálózati Hiba',
          detail: 'Nem sikerült menteni a beállításokat: ' + error.message,
          life: 5000
        });
      }
    });
  }

  onModeChange(): void {
    // Reset values when mode changes
    if (this.config.mode === 'percentage') {
      this.config.fixed_amount_usd = undefined;
      if (!this.config.max_percentage) {
        this.config.max_percentage = 2.0;
      }
    } else {
      this.config.max_percentage = undefined;
      if (!this.config.fixed_amount_usd) {
        this.config.fixed_amount_usd = 100;
      }
    }
  }

  isConfigValid(): boolean {
    if (this.config.mode === 'percentage') {
      return !!(this.config.max_percentage && 
                this.config.max_percentage >= 0.1 && 
                this.config.max_percentage <= 10);
    } else {
      return !!(this.config.fixed_amount_usd && 
                this.config.fixed_amount_usd >= 1 && 
                this.config.fixed_amount_usd <= 10000);
    }
  }

  calculateExampleAmount(): number {
    if (this.config.max_percentage && this.walletBalance) {
      return (this.walletBalance * this.config.max_percentage) / 100;
    }
    return 0;
  }
}