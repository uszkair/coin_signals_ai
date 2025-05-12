import React, { useEffect, useRef } from 'react';

/**
 * Component to overlay signal markers on the TradingView chart
 * @param {Object} props - Component props
 * @param {Array} props.signals - Array of signal objects
 * @param {Object} props.widget - TradingView widget instance
 * @param {Function} props.onMarkerClick - Function to call when a marker is clicked
 */
const SignalChartOverlay = ({ signals, widget, onMarkerClick }) => {
  const markersRef = useRef([]);

  useEffect(() => {
    // Clear existing markers when component unmounts or signals change
    return () => {
      if (markersRef.current.length > 0) {
        markersRef.current.forEach(marker => {
          if (marker && marker.remove) {
            marker.remove();
          }
        });
        markersRef.current = [];
      }
    };
  }, []);

  useEffect(() => {
    // Add markers to the chart when signals or widget changes
    if (!widget || !signals || signals.length === 0) {
      return;
    }

    // Wait for the widget to be fully loaded
    const checkWidgetReady = setInterval(() => {
      if (widget.chart && typeof widget.chart === 'function') {
        clearInterval(checkWidgetReady);
        addMarkersToChart();
      }
    }, 500);

    return () => {
      clearInterval(checkWidgetReady);
    };
  }, [widget, signals]);

  const addMarkersToChart = () => {
    // Clear existing markers
    markersRef.current.forEach(marker => {
      if (marker && marker.remove) {
        marker.remove();
      }
    });
    markersRef.current = [];

    // Get the chart instance
    const chart = widget.chart();
    if (!chart) {
      console.error('TradingView chart not available');
      return;
    }

    // Add markers for each signal
    signals.forEach(signal => {
      try {
        // Skip signals without timestamp
        if (!signal.timestamp) return;

        // Create marker options
        const options = {
          shape: signal.signal === 'BUY' ? 'arrow_up' : signal.signal === 'SELL' ? 'arrow_down' : 'circle',
          color: signal.signal === 'BUY' ? '#10b981' : signal.signal === 'SELL' ? '#ef4444' : '#f59e0b',
          text: signal.signal,
          tooltip: `
            <div style="font-size: 12px; padding: 5px;">
              <div><b>${signal.signal} Signal</b></div>
              <div>Pattern: ${signal.pattern}</div>
              <div>Entry: ${signal.entry?.toFixed(2) || 'N/A'}</div>
              <div>Stop Loss: ${signal.stop_loss?.toFixed(2) || 'N/A'}</div>
              <div>Take Profit: ${signal.take_profit?.toFixed(2) || 'N/A'}</div>
              <div>Score: ${signal.score}/4</div>
              <div>Outcome: ${signal.outcome || 'N/A'}</div>
              <div style="margin-top: 5px; font-style: italic;">Click for details</div>
            </div>
          `,
          size: 2,
        };

        // Convert timestamp to time value expected by TradingView
        const time = new Date(signal.timestamp).getTime();

        // Create the marker
        const marker = chart.createShape({ time, price: signal.entry }, options);

        // Add click event handler
        marker.onHit(() => {
          if (onMarkerClick) {
            onMarkerClick(signal);
          }
        });

        // Add horizontal lines for entry, stop loss, and take profit
        if (signal.entry) {
          const entryLine = chart.createShape(
            { time, price: signal.entry },
            {
              shape: 'horizontal_line',
              color: signal.signal === 'BUY' ? '#10b981' : signal.signal === 'SELL' ? '#ef4444' : '#f59e0b',
              disableSelection: true,
              disableSave: true,
              disableUndo: true,
              zIndex: 0,
              text: 'Entry',
              textColor: signal.signal === 'BUY' ? '#10b981' : signal.signal === 'SELL' ? '#ef4444' : '#f59e0b',
              linewidth: 2,
              linestyle: 2, // Dashed line
            }
          );
          markersRef.current.push(entryLine);
        }

        if (signal.stop_loss) {
          const slLine = chart.createShape(
            { time, price: signal.stop_loss },
            {
              shape: 'horizontal_line',
              color: '#ef4444',
              disableSelection: true,
              disableSave: true,
              disableUndo: true,
              zIndex: 0,
              text: 'Stop Loss',
              textColor: '#ef4444',
              linewidth: 1,
              linestyle: 2, // Dashed line
            }
          );
          markersRef.current.push(slLine);
        }

        if (signal.take_profit) {
          const tpLine = chart.createShape(
            { time, price: signal.take_profit },
            {
              shape: 'horizontal_line',
              color: '#10b981',
              disableSelection: true,
              disableSave: true,
              disableUndo: true,
              zIndex: 0,
              text: 'Take Profit',
              textColor: '#10b981',
              linewidth: 1,
              linestyle: 2, // Dashed line
            }
          );
          markersRef.current.push(tpLine);
        }

        // Store the marker reference for cleanup
        markersRef.current.push(marker);
      } catch (error) {
        console.error('Error adding marker to chart:', error);
      }
    });
  };

  // This component doesn't render anything visible
  return null;
};

export default SignalChartOverlay;