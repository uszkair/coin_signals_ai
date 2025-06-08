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
import { TabViewModule } from 'primeng/tabview';
import { MessageService } from 'primeng/api';

import { TradingService, PositionSizeConfig } from '../../services/trading.service';

@Component({
  selector: 'app-settings',
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
    DividerModule,
    TabViewModule
  ],
  providers: [MessageService],
  templateUrl: './settings.component.html'
})
export class SettingsComponent implements OnInit {
  // Position Size Configuration
  positionSizeConfig: PositionSizeConfig = {
    mode: 'percentage',
    max_percentage: 2.0,
    fixed_amount_usd: 100
  };

  // Risk Management Configuration
  riskConfig = {
    max_daily_trades: 10,
    daily_loss_limit: 5.0,  // percentage
    max_position_size: 2.0  // percentage
  };

  // Trading mode configuration
  tradingMode: 'manual' | 'automatic' = 'manual';

  // Current configurations from backend
  currentPositionConfig: any = null;
  currentTradingConfig: any = null;
  walletBalance: number = 0;

  // Loading states
  loadingPosition = false;
  loadingRisk = false;
  savingPosition = false;
  savingRisk = false;
  savingTradingMode = false;

  constructor(
    private tradingService: TradingService,
    private messageService: MessageService
  ) {}

  ngOnInit(): void {
    this.loadAllConfigs();
    this.loadWalletBalance();
    this.loadTradingMode();
  }

  loadAllConfigs(): void {
    this.loadPositionSizeConfig();
    this.loadRiskManagementConfig();
  }

  loadPositionSizeConfig(): void {
    this.loadingPosition = true;
    
    this.tradingService.getPositionSizeConfig().subscribe({
      next: (response) => {
        this.loadingPosition = false;
        if (response.success) {
          this.currentPositionConfig = response.data;
          this.positionSizeConfig = {
            mode: response.data.mode,
            max_percentage: response.data.max_percentage,
            fixed_amount_usd: response.data.fixed_amount_usd
          };
        }
      },
      error: (error) => {
        this.loadingPosition = false;
        this.showError('Pozíció méret beállítások betöltése sikertelen', error.message);
      }
    });
  }

  loadRiskManagementConfig(): void {
    this.loadingRisk = true;
    
    this.tradingService.getTradingConfig().subscribe({
      next: (response) => {
        this.loadingRisk = false;
        if (response.success) {
          this.currentTradingConfig = response.data;
          this.riskConfig = {
            max_daily_trades: response.data.max_daily_trades || 10,
            daily_loss_limit: (response.data.daily_loss_limit || 0.05) * 100, // Convert to percentage
            max_position_size: (response.data.max_position_size || 0.02) * 100 // Convert to percentage
          };
        }
      },
      error: (error) => {
        this.loadingRisk = false;
        this.showError('Risk management beállítások betöltése sikertelen', error.message);
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

  loadTradingMode(): void {
    this.tradingService.getAutoTradingStatus().subscribe({
      next: (response) => {
        if (response.success) {
          this.tradingMode = response.data.auto_trading_enabled ? 'automatic' : 'manual';
        }
      },
      error: (error) => {
        console.warn('Could not load trading mode:', error);
        // Default to manual mode if loading fails
        this.tradingMode = 'manual';
      }
    });
  }

  onTradingModeChange(): void {
    // This method is called when the radio button selection changes
    // The actual saving happens when the user clicks the save button
    console.log('Trading mode changed to:', this.tradingMode);
  }

  saveTradingMode(): void {
    this.savingTradingMode = true;
    const enableAutoTrading = this.tradingMode === 'automatic';

    this.tradingService.setAutoTrading(enableAutoTrading).subscribe({
      next: (response: any) => {
        this.savingTradingMode = false;
        if (response.success) {
          // Update the local state
          this.tradingService.updateAutoTradingState(enableAutoTrading);
          this.showSuccess(
            'Kereskedési mód mentve',
            `${this.tradingMode === 'automatic' ? 'Automatikus' : 'Manuális'} kereskedés beállítva`
          );
        } else {
          this.showError('Mentési hiba', response.error || 'Ismeretlen hiba történt');
        }
      },
      error: (error: any) => {
        this.savingTradingMode = false;
        this.showError('Hálózati hiba', 'Nem sikerült menteni a kereskedési módot: ' + error.message);
      }
    });
  }

  savePositionSizeConfig(): void {
    if (!this.isPositionConfigValid()) {
      this.showWarning('Érvénytelen beállítás', 'Kérlek töltsd ki az összes kötelező mezőt');
      return;
    }

    this.savingPosition = true;

    this.tradingService.updatePositionSizeConfig(this.positionSizeConfig).subscribe({
      next: (response) => {
        this.savingPosition = false;
        if (response.success) {
          this.currentPositionConfig = response.data;
          this.showSuccess('Pozíció méret beállítások mentve', 'A beállítások sikeresen frissítve');
        } else {
          this.showError('Mentési hiba', response.error || 'Ismeretlen hiba történt');
        }
      },
      error: (error) => {
        this.savingPosition = false;
        this.showError('Hálózati hiba', 'Nem sikerült menteni a beállításokat: ' + error.message);
      }
    });
  }

  saveRiskManagementConfig(): void {
    if (!this.isRiskConfigValid()) {
      this.showWarning('Érvénytelen beállítás', 'Kérlek ellenőrizd a megadott értékeket');
      return;
    }

    this.savingRisk = true;

    const configToSave = {
      max_daily_trades: this.riskConfig.max_daily_trades,
      daily_loss_limit: this.riskConfig.daily_loss_limit / 100, // Convert to decimal
      max_position_size: this.riskConfig.max_position_size / 100 // Convert to decimal
    };

    this.tradingService.updateTradingConfig(configToSave).subscribe({
      next: (response) => {
        this.savingRisk = false;
        if (response.success) {
          this.currentTradingConfig = response.data.current_config;
          this.showSuccess('Risk management beállítások mentve', 'A beállítások sikeresen frissítve');
        } else {
          this.showError('Mentési hiba', response.error || 'Ismeretlen hiba történt');
        }
      },
      error: (error) => {
        this.savingRisk = false;
        this.showError('Hálózati hiba', 'Nem sikerült menteni a beállításokat: ' + error.message);
      }
    });
  }

  onPositionModeChange(): void {
    // Reset values when mode changes
    if (this.positionSizeConfig.mode === 'percentage') {
      this.positionSizeConfig.fixed_amount_usd = undefined;
      if (!this.positionSizeConfig.max_percentage) {
        this.positionSizeConfig.max_percentage = 2.0;
      }
    } else {
      this.positionSizeConfig.max_percentage = undefined;
      if (!this.positionSizeConfig.fixed_amount_usd) {
        this.positionSizeConfig.fixed_amount_usd = 100;
      }
    }
  }

  isPositionConfigValid(): boolean {
    if (this.positionSizeConfig.mode === 'percentage') {
      return !!(this.positionSizeConfig.max_percentage && 
                this.positionSizeConfig.max_percentage >= 0.1 && 
                this.positionSizeConfig.max_percentage <= 10);
    } else {
      return !!(this.positionSizeConfig.fixed_amount_usd && 
                this.positionSizeConfig.fixed_amount_usd >= 1 && 
                this.positionSizeConfig.fixed_amount_usd <= 10000);
    }
  }

  isRiskConfigValid(): boolean {
    return this.riskConfig.max_daily_trades >= 1 && 
           this.riskConfig.max_daily_trades <= 100 &&
           this.riskConfig.daily_loss_limit >= 0.1 && 
           this.riskConfig.daily_loss_limit <= 50 &&
           this.riskConfig.max_position_size >= 0.1 && 
           this.riskConfig.max_position_size <= 20;
  }

  calculateExampleAmount(): number {
    if (this.positionSizeConfig.max_percentage && this.walletBalance) {
      return (this.walletBalance * this.positionSizeConfig.max_percentage) / 100;
    }
    return 0;
  }

  calculateDailyLossAmount(): number {
    if (this.riskConfig.daily_loss_limit && this.walletBalance) {
      return (this.walletBalance * this.riskConfig.daily_loss_limit) / 100;
    }
    return 0;
  }

  calculateMaxPositionAmount(): number {
    if (this.riskConfig.max_position_size && this.walletBalance) {
      return (this.walletBalance * this.riskConfig.max_position_size) / 100;
    }
    return 0;
  }

  // Helper methods for notifications
  private showSuccess(summary: string, detail: string): void {
    this.messageService.add({
      severity: 'success',
      summary,
      detail,
      life: 5000
    });
  }

  private showError(summary: string, detail: string): void {
    this.messageService.add({
      severity: 'error',
      summary,
      detail,
      life: 8000
    });
  }

  private showWarning(summary: string, detail: string): void {
    this.messageService.add({
      severity: 'warn',
      summary,
      detail,
      life: 5000
    });
  }
}