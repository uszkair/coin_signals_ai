import axios from 'axios'
import { useQuery, useMutation } from 'react-query'

// Base API configuration
const api = axios.create({
  baseURL: '/api',
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Custom hook for fetching a single coin signal
export const useSignal = (symbol, interval = '1h', mode = 'swing', options = {}) => {
  return useQuery(
    ['signal', symbol, interval, mode],
    async () => {
      const response = await api.get(`/signal/${symbol}`, {
        params: { interval, mode }
      })
      return response.data
    },
    {
      enabled: !!symbol,
      refetchInterval: 60000, // Refetch every minute
      ...options,
    }
  )
}

// Custom hook for fetching multi-timeframe signal
export const useSignalMTF = (symbol, mode = 'swing', options = {}) => {
  return useQuery(
    ['signal-mtf', symbol, mode],
    async () => {
      const response = await api.get(`/signal-mtf/${symbol}`, {
        params: { mode }
      })
      return response.data
    },
    {
      enabled: !!symbol,
      refetchInterval: 60000, // Refetch every minute
      ...options,
    }
  )
}

// Custom hook for fetching signals for multiple coins
export const useSignals = (symbols = null, interval = '1h', mode = 'swing', options = {}) => {
  return useQuery(
    ['signals', interval, mode, symbols?.join(',')],
    async () => {
      const response = await api.get('/signals', {
        params: { 
          symbols: symbols?.join(','),
          interval, 
          mode 
        }
      })
      return response.data
    },
    {
      refetchInterval: 60000, // Refetch every minute
      ...options,
    }
  )
}

// Custom hook for fetching market data
export const useMarketData = (symbol, interval = '1h', limit = 100, options = {}) => {
  return useQuery(
    ['marketdata', symbol, interval, limit],
    async () => {
      const response = await api.get(`/marketdata/${symbol}`, {
        params: { interval, limit }
      })
      return response.data
    },
    {
      enabled: !!symbol,
      ...options,
    }
  )
}

// Custom hook for fetching available symbols
export const useSymbols = (options = {}) => {
  return useQuery(
    ['symbols'],
    async () => {
      const response = await api.get('/symbols')
      return response.data.symbols
    },
    {
      staleTime: Infinity, // Symbols don't change often
      ...options,
    }
  )
}

export default {
  useSignal,
  useSignalMTF,
  useSignals,
  useMarketData,
  useSymbols,
}