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
import { DropdownModule } from 'primeng/dropdown';
import { SliderModule } from 'primeng/slider';
import { CheckboxModule } from 'primeng/checkbox';
import { InputSwitchModule } from 'primeng/inputswitch';
import { MessageService } from 'primeng/api';

import { TradingService, PositionSizeConfig, TradingEnvironment } from '../../services/trading.service';
import { SettingsService } from '../../services/settings.service';

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
    TabViewModule,
    DropdownModule,
    SliderModule,
    CheckboxModule,
    InputSwitchModule
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

  // Auto trading configuration
  autoTradingEnabled: boolean = true;

  // Current configurations from backend
  currentPositionConfig: any = null;
  currentTradingConfig: any = null;
  walletBalance: number = 0;

  // Trading Environment Configuration
  useTestnet: boolean = false;
  currentEnvironment: TradingEnvironment | null = null;
  minimumRequirements: any = null;

  // Loading states
  loadingPosition = false;
  loadingRisk = false;
  savingPosition = false;
  savingRisk = false;
  savingAutoTrading = false;
  savingEnvironment = false;
  loadingMinimumReqs = false;
  
  // Technical Indicator Settings
  technicalIndicatorWeights = {
    rsi_weight: 1.0,
    macd_weight: 1.0,
    volume_weight: 1.0,
    candlestick_weight: 2.0,
    bollinger_weight: 1.0,
    ma_weight: 1.0
  };

  rsiSettings = {
    period: 14,
    overbought: 70,
    oversold: 30
  };

  macdSettings = {
    fast_period: 12,
    slow_period: 26,
    signal_period: 9
  };

  bollingerSettings = {
    period: 20,
    deviation: 2.0
  };

  maSettings = {
    short_ma: 20,
    long_ma: 50,
    ma_type: 'EMA'
  };

  volumeSettings = {
    volume_threshold_multiplier: 1.5,
    high_volume_threshold: 2.0
  };

  candlestickSettings = {
    sensitivity: 'medium',
    min_pattern_score: 0.7
  };

  // AI/ML Settings
  aiMlSettings = {
    ai_signal_weight: 2.0,
    ai_confidence_threshold: 60.0,
    ml_models: {
      lstm_enabled: true,
      random_forest_enabled: true,
      gradient_boosting_enabled: true
    },
    market_regime_detection: true,
    sentiment_analysis: false,
    ensemble_method: 'weighted'
  };

  // Notification Settings
  notificationSettings = {
    signal_notifications: {
      enabled: true,
      email: false,
      push: true,
      in_app: true,
      min_confidence: 70
    },
    trade_notifications: {
      enabled: true,
      execution_alerts: true,
      profit_loss_alerts: true,
      risk_alerts: true
    },
    system_notifications: {
      enabled: true,
      connection_issues: true,
      error_alerts: true,
      maintenance_alerts: false
    }
  };

  // Stop Loss/Take Profit Settings
  stopLossTakeProfitSettings = {
    stop_loss_percentage: 0.05,  // 5%
    take_profit_percentage: 0.10, // 10%
    use_atr_based_sl_tp: false,
    atr_multiplier_sl: 1.5,
    atr_multiplier_tp: 2.0
  };

  // Display values for percentage inputs (converted to percentage for UI)
  stopLossPercentageDisplay: number = 5.0;
  takeProfitPercentageDisplay: number = 10.0;

  // Loading states for new settings
  loadingTechnicalSettings = false;
  savingTechnicalSettings = false;
  loadingAIMLSettings = false;
  savingAIMLSettings = false;
  loadingNotificationSettings = false;
  savingNotificationSettings = false;
  loadingStopLossTakeProfit = false;
  savingStopLossTakeProfit = false;

  // Dropdown options
  maTypeOptions = [
    { label: 'EMA (Exponential)', value: 'EMA' },
    { label: 'SMA (Simple)', value: 'SMA' },
    { label: 'WMA (Weighted)', value: 'WMA' }
  ];

  sensitivityOptions = [
    { label: 'Alacsony', value: 'low' },
    { label: 'Közepes', value: 'medium' },
    { label: 'Magas', value: 'high' }
  ];

  ensembleMethodOptions = [
    { label: 'Súlyozott átlag', value: 'weighted' },
    { label: 'Szavazás', value: 'voting' },
    { label: 'Stacking', value: 'stacking' }
  ];

  constructor(
    private tradingService: TradingService,
    private messageService: MessageService,
    private settingsService: SettingsService
  ) {}

  ngOnInit(): void {
    this.loadAllConfigs();
    this.loadWalletBalance();
    this.loadTradingMode();
    this.loadTradingEnvironment();
    this.loadAdvancedSettings();
    this.loadStopLossTakeProfitSettings();
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
        
        // Set default values on error
        this.riskConfig = {
          max_daily_trades: 10,
          daily_loss_limit: 5.0,
          max_position_size: 2.0
        };
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
          this.autoTradingEnabled = response.data.auto_trading_enabled || false;
        }
      },
      error: (error) => {
        console.warn('Could not load trading mode:', error);
        // Default to automatic mode if loading fails
        this.autoTradingEnabled = true;
      }
    });
  }

  onAutoTradingToggle(): void {
    // This method is called when the toggle switch changes
    console.log('Auto trading toggled to:', this.autoTradingEnabled);
  }

  saveAutoTradingSettings(): void {
    this.savingAutoTrading = true;

    // Add timeout for better user experience
    const timeoutId = setTimeout(() => {
      if (this.savingAutoTrading) {
        this.showWarning('Lassú válasz', 'A mentés tovább tart a vártnál, kérlek várj...');
      }
    }, 3000);

    this.tradingService.setAutoTrading(this.autoTradingEnabled).subscribe({
      next: (response: any) => {
        clearTimeout(timeoutId);
        this.savingAutoTrading = false;
        if (response.success) {
          // Update the local state
          this.tradingService.updateAutoTradingState(this.autoTradingEnabled);
          this.showSuccess(
            'Auto-trading beállítás mentve',
            `Automatikus kereskedés ${this.autoTradingEnabled ? 'bekapcsolva' : 'kikapcsolva'}`
          );
        } else {
          this.showError('Mentési hiba', response.error || 'Ismeretlen hiba történt');
        }
      },
      error: (error: any) => {
        clearTimeout(timeoutId);
        this.savingAutoTrading = false;
        this.showError('Hálózati hiba', 'Nem sikerült menteni a beállítást: ' + error.message);
      }
    });
  }

  savePositionSizeConfig(): void {
    // Validate and show detailed error messages
    const validationErrors = this.getPositionConfigValidationErrors();
    if (validationErrors.length > 0) {
      const errorMessage = 'Kérlek javítsd ki a következő hibákat:\n\n' + validationErrors.join('\n');
      this.showError('Érvénytelen beállítások', errorMessage);
      return;
    }

    this.savingPosition = true;

    // First validate the configuration
    this.tradingService.validatePositionSizeConfig(this.positionSizeConfig).subscribe({
      next: (validationResponse) => {
        if (!validationResponse.success) {
          this.savingPosition = false;
          
          // Show detailed validation error
          const details = (validationResponse as any).details;
          let errorMessage = validationResponse.error || 'Position size konfiguráció érvénytelen';
          
          if (details) {
            errorMessage += `\n\nRészletek:`;
            errorMessage += `\nWallet egyenleg: $${details.wallet_balance?.toFixed(2)}`;
            
            if (details.mode) {
              errorMessage += `\nMód: ${details.mode}`;
            } else {
              errorMessage += `\nSzámított position size: $${details.calculated_position_size?.toFixed(2)}`;
              if (details.percentage) {
                errorMessage += `\nSzázalék: ${details.percentage}%`;
              }
            }
            
            if (details.validation_errors?.length > 0) {
              errorMessage += `\n\nMinimum követelmények:`;
              details.validation_errors.forEach((err: any) => {
                errorMessage += `\n• ${err.symbol}: minimum $${err.minimum_required}`;
              });
            }
            
            if (details.recommendation) {
              errorMessage += `\n\nJavaslat: ${details.recommendation}`;
            }
          }
          
          this.showError('Érvénytelen konfiguráció', errorMessage);
          return;
        }
        
        // If validation passes, save the configuration
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
      },
      error: (error) => {
        this.savingPosition = false;
        this.showError('Validációs hiba', 'Nem sikerült ellenőrizni a beállításokat: ' + error.message);
      }
    });
  }

  saveRiskManagementConfig(): void {
    // Validate and show detailed error messages
    const validationErrors = this.getRiskConfigValidationErrors();
    if (validationErrors.length > 0) {
      const errorMessage = 'Kérlek javítsd ki a következő hibákat:\n\n' + validationErrors.join('\n');
      this.showError('Érvénytelen beállítások', errorMessage);
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
    // Check if all required fields have valid values
    const maxDailyTrades = this.riskConfig.max_daily_trades;
    const dailyLossLimit = this.riskConfig.daily_loss_limit;
    const maxPositionSize = this.riskConfig.max_position_size;
    
    return !!(maxDailyTrades && maxDailyTrades >= 1 && maxDailyTrades <= 100) &&
           !!(dailyLossLimit && dailyLossLimit >= 0.1 && dailyLossLimit <= 50) &&
           !!(maxPositionSize && maxPositionSize >= 0.1 && maxPositionSize <= 20);
  }

  getRiskConfigValidationErrors(): string[] {
    const errors: string[] = [];
    
    // Check max daily trades
    const maxDailyTrades = this.riskConfig.max_daily_trades;
    if (!maxDailyTrades || maxDailyTrades < 1 || maxDailyTrades > 100) {
      errors.push('• Napi Trade Limit: 1 és 100 között kell lennie (jelenleg: ' + (maxDailyTrades || 'nincs megadva') + ')');
    }
    
    // Check daily loss limit
    const dailyLossLimit = this.riskConfig.daily_loss_limit;
    if (!dailyLossLimit || dailyLossLimit < 0.1 || dailyLossLimit > 50) {
      errors.push('• Napi Veszteség Limit: 0.1% és 50% között kell lennie (jelenleg: ' + (dailyLossLimit || 'nincs megadva') + '%)');
    }
    
    // Check max position size
    const maxPositionSize = this.riskConfig.max_position_size;
    if (!maxPositionSize || maxPositionSize < 0.1 || maxPositionSize > 20) {
      errors.push('• Maximum Pozíció Méret: 0.1% és 20% között kell lennie (jelenleg: ' + (maxPositionSize || 'nincs megadva') + '%)');
    }
    
    return errors;
  }

  getPositionConfigValidationErrors(): string[] {
    const errors: string[] = [];
    
    if (this.positionSizeConfig.mode === 'percentage') {
      const maxPercentage = this.positionSizeConfig.max_percentage;
      if (!maxPercentage || maxPercentage < 0.1 || maxPercentage > 10) {
        errors.push('• Maximum Százalék: 0.1% és 10% között kell lennie (jelenleg: ' + (maxPercentage || 'nincs megadva') + '%)');
      }
    } else if (this.positionSizeConfig.mode === 'fixed_usd') {
      const fixedAmount = this.positionSizeConfig.fixed_amount_usd;
      if (!fixedAmount || fixedAmount < 1 || fixedAmount > 10000) {
        errors.push('• Fix USD Összeg: $1 és $10,000 között kell lennie (jelenleg: $' + (fixedAmount || 'nincs megadva') + ')');
      }
    } else {
      errors.push('• Pozíció méret mód: Válassz egy érvényes módot (százalékos vagy fix USD)');
    }
    
    return errors;
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

  // Trading Environment Methods
  loadTradingEnvironment(): void {
    this.tradingService.getTradingEnvironment().subscribe({
      next: (response) => {
        if (response.success) {
          this.currentEnvironment = response.data;
          this.useTestnet = response.data.testnet;
        }
      },
      error: (error) => {
        console.warn('Could not load trading environment:', error);
        // Default to mainnet if loading fails
        this.useTestnet = false;
      }
    });
  }

  onEnvironmentChange(): void {
    // This method is called when the radio button selection changes
    // The actual saving happens when the user clicks the save button
    console.log('Environment changed to:', this.useTestnet ? 'testnet' : 'mainnet');
  }

  saveEnvironmentChange(): void {
    this.savingEnvironment = true;

    this.tradingService.switchTradingEnvironment(this.useTestnet).subscribe({
      next: (response) => {
        this.savingEnvironment = false;
        if (response.success) {
          this.currentEnvironment = response.data;
          this.showSuccess(
            'Kereskedési környezet váltva',
            `${this.useTestnet ? 'Testnet (fake pénz)' : 'Mainnet (valós pénz)'} környezet beállítva`
          );
          // Reload wallet balance after environment change
          this.loadWalletBalance();
          
          // Trigger a global wallet refresh event for dashboard
          window.dispatchEvent(new CustomEvent('walletEnvironmentChanged'));
        } else {
          this.showError('Váltási hiba', response.error || 'Ismeretlen hiba történt');
        }
      },
      error: (error) => {
        this.savingEnvironment = false;
        this.showError('Hálózati hiba', 'Nem sikerült váltani a környezetet: ' + error.message);
      }
    });
  }

  loadMinimumRequirements(): void {
    this.loadingMinimumReqs = true;

    this.tradingService.getMinimumRequirements().subscribe({
      next: (response) => {
        this.loadingMinimumReqs = false;
        if (response.success) {
          this.minimumRequirements = response.data;
          this.showSuccess(
            'Minimum követelmények betöltve',
            'A Binance minimum kereskedési követelmények frissítve'
          );
        } else {
          this.showError('Betöltési hiba', response.error || 'Ismeretlen hiba történt');
        }
      },
      error: (error) => {
        this.loadingMinimumReqs = false;
        this.showError('Hálózati hiba', 'Nem sikerült betölteni a követelményeket: ' + error.message);
      }
    });
  }

  // Technical Indicator Settings Methods
  loadTechnicalIndicatorSettings(): void {
    this.loadingTechnicalSettings = true;
    
    this.settingsService.getTechnicalAnalysisSettings().subscribe({
      next: (data) => {
        this.loadingTechnicalSettings = false;
        this.technicalIndicatorWeights = data.technical_indicator_weights || this.technicalIndicatorWeights;
        this.rsiSettings = data.rsi_settings || this.rsiSettings;
        this.macdSettings = data.macd_settings || this.macdSettings;
        this.bollingerSettings = data.bollinger_settings || this.bollingerSettings;
        this.maSettings = data.ma_settings || this.maSettings;
        this.volumeSettings = data.volume_settings || this.volumeSettings;
        this.candlestickSettings = data.candlestick_settings || this.candlestickSettings;
      },
      error: (error) => {
        this.loadingTechnicalSettings = false;
        this.showError('Technical beállítások betöltése sikertelen', error.message);
      }
    });
  }

  saveTechnicalIndicatorSettings(): void {
    this.savingTechnicalSettings = true;
    
    const settings = {
      technical_indicator_weights: this.technicalIndicatorWeights,
      rsi_settings: this.rsiSettings,
      macd_settings: this.macdSettings,
      bollinger_settings: this.bollingerSettings,
      ma_settings: this.maSettings,
      volume_settings: this.volumeSettings,
      candlestick_settings: this.candlestickSettings
    };

    this.settingsService.updateTechnicalAnalysisSettings(settings).subscribe({
      next: (response) => {
        this.savingTechnicalSettings = false;
        this.showSuccess('Technical beállítások mentve', 'A technikai indikátor beállítások sikeresen frissítve');
      },
      error: (error) => {
        this.savingTechnicalSettings = false;
        this.showError('Hálózati hiba', 'Nem sikerült menteni a beállításokat: ' + error.message);
      }
    });
  }

  // AI/ML Settings Methods
  loadAIMLSettings(): void {
    this.loadingAIMLSettings = true;
    
    this.settingsService.getAIMLSettings().subscribe({
      next: (data) => {
        this.loadingAIMLSettings = false;
        this.aiMlSettings = data.ai_ml_settings || this.aiMlSettings;
      },
      error: (error) => {
        this.loadingAIMLSettings = false;
        this.showError('AI/ML beállítások betöltése sikertelen', error.message);
      }
    });
  }

  saveAIMLSettings(): void {
    this.savingAIMLSettings = true;
    
    const settings = {
      ai_ml_settings: this.aiMlSettings
    };

    this.settingsService.updateAIMLSettings(settings).subscribe({
      next: (response) => {
        this.savingAIMLSettings = false;
        this.showSuccess('AI/ML beállítások mentve', 'A mesterséges intelligencia beállítások sikeresen frissítve');
      },
      error: (error) => {
        this.savingAIMLSettings = false;
        this.showError('Hálózati hiba', 'Nem sikerült menteni a beállításokat: ' + error.message);
      }
    });
  }

  // Notification Settings Methods
  loadNotificationSettings(): void {
    this.loadingNotificationSettings = true;
    
    this.settingsService.getNotificationSettings().subscribe({
      next: (data) => {
        this.loadingNotificationSettings = false;
        this.notificationSettings = data.notification_settings || this.notificationSettings;
      },
      error: (error) => {
        this.loadingNotificationSettings = false;
        this.showError('Értesítési beállítások betöltése sikertelen', error.message);
      }
    });
  }

  saveNotificationSettings(): void {
    this.savingNotificationSettings = true;
    
    // Send the notification settings directly as the backend expects
    const settings = {
      notification_settings: this.notificationSettings
    };

    console.log('Saving notification settings:', settings);

    this.settingsService.updateNotificationSettings(settings).subscribe({
      next: (response) => {
        this.savingNotificationSettings = false;
        console.log('Notification settings saved successfully:', response);
        this.showSuccess('Értesítési beállítások mentve', 'Az értesítési beállítások sikeresen frissítve');
      },
      error: (error) => {
        this.savingNotificationSettings = false;
        console.error('Error saving notification settings:', error);
        this.showError('Hálózati hiba', 'Nem sikerült menteni a beállításokat: ' + (error.error?.detail || error.message));
      }
    });
  }

  // Load all advanced settings
  loadAdvancedSettings(): void {
    this.loadTechnicalIndicatorSettings();
    this.loadAIMLSettings();
    this.loadNotificationSettings();
  }

  // Reset methods for each category
  resetTechnicalIndicatorSettings(): void {
    this.technicalIndicatorWeights = {
      rsi_weight: 1.0,
      macd_weight: 1.0,
      volume_weight: 1.0,
      candlestick_weight: 2.0,
      bollinger_weight: 1.0,
      ma_weight: 1.0
    };

    this.rsiSettings = {
      period: 14,
      overbought: 70,
      oversold: 30
    };

    this.macdSettings = {
      fast_period: 12,
      slow_period: 26,
      signal_period: 9
    };

    this.bollingerSettings = {
      period: 20,
      deviation: 2.0
    };

    this.maSettings = {
      short_ma: 20,
      long_ma: 50,
      ma_type: 'EMA'
    };

    this.volumeSettings = {
      volume_threshold_multiplier: 1.5,
      high_volume_threshold: 2.0
    };

    this.candlestickSettings = {
      sensitivity: 'medium',
      min_pattern_score: 0.7
    };

    this.showSuccess('Alaphelyzetbe állítva', 'A technikai indikátor beállítások visszaállítva az alapértékekre');
  }

  resetAIMLSettings(): void {
    this.aiMlSettings = {
      ai_signal_weight: 2.0,
      ai_confidence_threshold: 60.0,
      ml_models: {
        lstm_enabled: true,
        random_forest_enabled: true,
        gradient_boosting_enabled: true
      },
      market_regime_detection: true,
      sentiment_analysis: false,
      ensemble_method: 'weighted'
    };

    this.showSuccess('Alaphelyzetbe állítva', 'Az AI/ML beállítások visszaállítva az alapértékekre');
  }

  resetNotificationSettings(): void {
    this.notificationSettings = {
      signal_notifications: {
        enabled: true,
        email: false,
        push: true,
        in_app: true,
        min_confidence: 70
      },
      trade_notifications: {
        enabled: true,
        execution_alerts: true,
        profit_loss_alerts: true,
        risk_alerts: true
      },
      system_notifications: {
        enabled: true,
        connection_issues: true,
        error_alerts: true,
        maintenance_alerts: false
      }
    };

    this.showSuccess('Alaphelyzetbe állítva', 'Az értesítési beállítások visszaállítva az alapértékekre');
  }

  resetPositionSizeSettings(): void {
    this.positionSizeConfig = {
      mode: 'percentage',
      max_percentage: 2.0,
      fixed_amount_usd: 100
    };

    this.showSuccess('Alaphelyzetbe állítva', 'A pozíció méret beállítások visszaállítva az alapértékekre');
  }

  resetRiskManagementSettings(): void {
    this.riskConfig = {
      max_daily_trades: 10,
      daily_loss_limit: 5.0,
      max_position_size: 2.0
    };

    this.showSuccess('Alaphelyzetbe állítva', 'A kockázatkezelési beállítások visszaállítva az alapértékekre');
  }

  resetAutoTradingSettings(): void {
    this.autoTradingEnabled = true;
    this.showSuccess('Alaphelyzetbe állítva', 'Az automatikus kereskedés bekapcsolva');
  }

  resetTradingEnvironmentSettings(): void {
    this.useTestnet = true;
    this.showSuccess('Alaphelyzetbe állítva', 'A kereskedési környezet visszaállítva testnet módra');
  }

  // Stop Loss/Take Profit Settings Methods
  loadStopLossTakeProfitSettings(): void {
    this.loadingStopLossTakeProfit = true;
    
    this.settingsService.getStopLossTakeProfitSettings().subscribe({
      next: (response) => {
        this.loadingStopLossTakeProfit = false;
        if (response.success) {
          const data = response.data;
          this.stopLossTakeProfitSettings = {
            stop_loss_percentage: data.stop_loss_percentage || 0.05,
            take_profit_percentage: data.take_profit_percentage || 0.10,
            use_atr_based_sl_tp: data.use_atr_based_sl_tp || false,
            atr_multiplier_sl: data.atr_multiplier_sl || 1.5,
            atr_multiplier_tp: data.atr_multiplier_tp || 2.0
          };
          
          // Update display values (convert to percentage)
          this.stopLossPercentageDisplay = this.stopLossTakeProfitSettings.stop_loss_percentage * 100;
          this.takeProfitPercentageDisplay = this.stopLossTakeProfitSettings.take_profit_percentage * 100;
        }
      },
      error: (error) => {
        this.loadingStopLossTakeProfit = false;
        this.showError('Stop Loss/Take Profit beállítások betöltése sikertelen', error.message);
      }
    });
  }

  onStopLossTakeProfitModeChange(): void {
    // This method is called when the radio button selection changes
    console.log('Stop Loss/Take Profit mode changed to:', this.stopLossTakeProfitSettings.use_atr_based_sl_tp ? 'ATR' : 'Percentage');
  }

  saveStopLossTakeProfitSettings(): void {
    this.savingStopLossTakeProfit = true;

    // Convert percentage display values back to decimal
    const settingsToSave = {
      stop_loss_percentage: this.stopLossPercentageDisplay / 100,
      take_profit_percentage: this.takeProfitPercentageDisplay / 100,
      use_atr_based_sl_tp: this.stopLossTakeProfitSettings.use_atr_based_sl_tp,
      atr_multiplier_sl: this.stopLossTakeProfitSettings.atr_multiplier_sl,
      atr_multiplier_tp: this.stopLossTakeProfitSettings.atr_multiplier_tp
    };

    this.settingsService.updateStopLossTakeProfitSettings(settingsToSave).subscribe({
      next: (response) => {
        this.savingStopLossTakeProfit = false;
        if (response.success) {
          // Update local settings
          this.stopLossTakeProfitSettings = settingsToSave;
          this.showSuccess('Stop Loss/Take Profit beállítások mentve', 'A beállítások sikeresen frissítve');
        } else {
          this.showError('Mentési hiba', response.error || 'Ismeretlen hiba történt');
        }
      },
      error: (error) => {
        this.savingStopLossTakeProfit = false;
        this.showError('Hálózati hiba', 'Nem sikerült menteni a beállításokat: ' + error.message);
      }
    });
  }

  resetStopLossTakeProfitSettings(): void {
    this.stopLossTakeProfitSettings = {
      stop_loss_percentage: 0.05,  // 5%
      take_profit_percentage: 0.10, // 10%
      use_atr_based_sl_tp: false,
      atr_multiplier_sl: 1.5,
      atr_multiplier_tp: 2.0
    };

    // Update display values
    this.stopLossPercentageDisplay = 5.0;
    this.takeProfitPercentageDisplay = 10.0;

    this.showSuccess('Alaphelyzetbe állítva', 'A Stop Loss/Take Profit beállítások visszaállítva az alapértékekre');
  }

}