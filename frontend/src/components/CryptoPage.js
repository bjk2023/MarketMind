import React, { useState, useEffect } from 'react';
// Import necessary icons from Lucide
import { Bitcoin, RefreshCw } from 'lucide-react';

// Defines the API base URL, defaulting to local host for development
const API_URL = process.env.REACT_APP_API_URL || 'http://127.0.0.1:5001';

const CryptoPage = () => {
    // State for data fetched from the API
    const [cryptos, setCryptos] = useState([]); // List of available cryptocurrencies
    const [currencies, setCurrencies] = useState([]); // List of target fiat currencies
    
    // State for user selection and input
    const [fromCrypto, setFromCrypto] = useState('BTC');
    const [toCurrency, setToCurrency] = useState('USD');
    const [amount, setAmount] = useState(1);
    
    // State for the conversion result and status
    const [exchangeData, setExchangeData] = useState(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState('');

    // Predefined popular conversion pairs for quick access buttons
    const popularPairs = [
        { from: 'BTC', to: 'USD', label: 'BTC → USD' },
        { from: 'ETH', to: 'USD', label: 'ETH → USD' },
        { from: 'BNB', to: 'USD', label: 'BNB → USD' },
        { from: 'SOL', to: 'USD', label: 'SOL → USD' },
        { from: 'XRP', to: 'USD', label: 'XRP → USD' },
        { from: 'DOGE', to: 'USD', label: 'DOGE → USD' },
    ];

    // Effect Hook: Fetches initial data on component mount
    useEffect(() => {
        fetchCryptos();
        fetchCurrencies();
        handleConvert(); // Run an initial conversion for default pair (BTC/USD)
    }, []); // Empty dependency array ensures this runs only once

    // API Call to fetch the list of available crypto assets
    const fetchCryptos = async () => {
        try {
            // FIX: Corrected template literal syntax from single quotes to backticks (``)
            const response = await fetch(`${API_URL}/crypto/list`);
            const data = await response.json();
            setCryptos(data);
        } catch (err) {
            console.error('Error fetching cryptos:', err);
        }
    };

    // API Call to fetch the list of available target fiat currencies
    const fetchCurrencies = async () => {
        try {
            // FIX: Corrected template literal syntax
            const response = await fetch(`${API_URL}/crypto/currencies`);
            const data = await response.json();
            setCurrencies(data);
        } catch (err) {
            console.error('Error fetching currencies:', err);
        }
    };

    // API Call to fetch the actual exchange rate and current prices
    const handleConvert = async () => {
        setLoading(true);
        setError('');
        
        try {
            const response = await fetch(
                `${API_URL}/crypto/convert?from=${fromCrypto}&to=${toCurrency}`
            );
            
            if (!response.ok) {
                throw new Error('Failed to fetch exchange rate');
            }

            const data = await response.json();
            setExchangeData(data);
        } catch (err) {
            setError('Could not fetch crypto exchange rate. Please try again.');
            console.error('Conversion error:', err);
        } finally {
            setLoading(false);
        }
    };

    // Handler for the popular quick-access buttons
    const handleQuickPair = (from, to) => {
        setFromCrypto(from);
        setToCurrency(to);
        // Delay conversion slightly to ensure state update is processed
        setTimeout(handleConvert, 100); 
    };

    // Derived values for display
    const convertedAmount = exchangeData ? (amount * exchangeData.exchange_rate).toFixed(2) : '0.00';
    const formattedRate = exchangeData ? exchangeData.exchange_rate.toLocaleString(undefined, {minimumFractionDigits: 2, maximumFractionDigits: 2}) : '0.00';

    return (
        <div className="container mx-auto px-6 py-8 max-w-6xl">
            {/* Header Section */}
            <div className="text-center mb-8 animate-fade-in">
                <div className="flex items-center justify-center mb-2">
                    <Bitcoin className="w-10 h-10 text-purple-600 dark:text-purple-400 mr-3" />
                    <h1 className="text-4xl font-bold text-gray-900 dark:text-white">
                        Cryptocurrency Exchange
                    </h1>
                </div>
                <p className="text-gray-600 dark:text-gray-400">
                    Real-time cryptocurrency prices powered by Alpha Vantage
                </p>
            </div>

            {/* Main Converter Card */}
            <div className="bg-white dark:bg-gray-800 rounded-xl shadow-lg p-8 mb-8 animate-fade-in transition-colors duration-200">
                <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-6">Crypto Converter</h2>
                
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6 items-end">
                    {/* Input: Amount and From Crypto Selection */}
                    <div>
                        <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                            From Cryptocurrency
                        </label>
                        <div className="space-y-2">
                            <input
                                type="number"
                                value={amount}
                                onChange={(e) => setAmount(e.target.value)}
                                className="w-full px-4 py-3 border border-gray-300 dark:border-gray-600 dark:bg-gray-700 dark:text-white rounded-lg focus:ring-2 focus:ring-purple-500 outline-none"
                                placeholder="Amount"
                                min="0"
                                step="0.00000001"
                            />
                            <select
                                value={fromCrypto}
                                onChange={(e) => setFromCrypto(e.target.value)}
                                className="w-full px-4 py-3 border border-gray-300 dark:border-gray-600 dark:bg-gray-700 dark:text-white rounded-lg focus:ring-2 focus:ring-purple-500 outline-none"
                            >
                                {/* Populate options from fetched cryptos */}
                                {cryptos.map((crypto) => (
                                    <option key={crypto.code} value={crypto.code}>
                                        {crypto.icon} {crypto.code} - {crypto.name}
                                    </option>
                                ))}
                            </select>
                        </div>
                    </div>

                    {/* Output: Converted Amount and To Currency Selection */}
                    <div>
                        <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                            To Fiat Currency
                        </label>
                        <div className="space-y-2">
                            {/* Display the calculated converted amount */}
                            <div className="w-full px-4 py-3 border border-gray-300 dark:border-gray-600 dark:bg-gray-900 dark:text-white rounded-lg font-bold text-lg bg-gray-50">
                                {loading ? '...' : `${currencies.find(c => c.code === toCurrency)?.symbol || '$'}${convertedAmount}`}
                            </div>
                            <select
                                value={toCurrency}
                                onChange={(e) => setToCurrency(e.target.value)}
                                className="w-full px-4 py-3 border border-gray-300 dark:border-gray-600 dark:bg-gray-700 dark:text-white rounded-lg focus:ring-2 focus:ring-purple-500 outline-none"
                            >
                                {/* Populate options from fetched fiat currencies */}
                                {currencies.map((curr) => (
                                    <option key={curr.code} value={curr.code}>
                                        {curr.flag} {curr.code} - {curr.name}
                                    </option>
                                ))}
                            </select>
                        </div>
                    </div>
                </div>

                {/* Convert Button */}
                <div className="mt-6">
                    <button
                        onClick={handleConvert}
                        disabled={loading}
                        className={`w-full py-3 rounded-lg font-semibold text-white transition-all ${
                            loading
                                ? 'bg-gray-400 cursor-not-allowed'
                                : 'bg-purple-600 hover:bg-purple-700 active:scale-95'
                        }`}
                    >
                        {loading ? 'Converting...' : 'Convert'}
                    </button>
                </div>

                {/* Error Message and Retry Button */}
                {error && (
                    <div className="mt-4 bg-red-50 dark:bg-red-900/30 border border-red-200 dark:border-red-800 text-red-700 dark:text-red-300 px-4 py-3 rounded-lg flex items-center justify-between">
                        <span>{error}</span>
                        <button
                            onClick={() => {
                                setError('');
                                handleConvert();
                            }}
                            className="flex items-center space-x-2 px-3 py-1 bg-red-600 hover:bg-red-700 text-white rounded-lg transition-all text-sm"
                        >
                            <RefreshCw className="w-4 h-4" />
                            <span>Retry</span>
                        </button>
                    </div>
                )}
            </div>

            {/* Exchange Rate Details Card */}
            {exchangeData && !loading && (
                <div className="bg-gradient-to-r from-purple-50 to-pink-50 dark:from-purple-900/30 dark:to-pink-900/30 rounded-xl p-6 mb-8 animate-fade-in border border-purple-100 dark:border-purple-800">
                    <div className="grid grid-cols-1 md:grid-cols-4 gap-4 text-center">
                        {/* Current Exchange Rate */}
                        <div>
                            <p className="text-sm text-gray-600 dark:text-gray-400 mb-1">Exchange Rate</p>
                            <p className="text-2xl font-bold text-gray-900 dark:text-white">
                                ${formattedRate}
                            </p>
                            <p className="text-xs text-gray-500 dark:text-gray-500 mt-1">
                                1 {exchangeData.from_crypto.code} = ${exchangeData.exchange_rate.toLocaleString(undefined, {maximumFractionDigits: 2})} {exchangeData.to_currency.code}
                            </p>
                        </div>
                        {/* Bid Price */}
                        <div>
                            <p className="text-sm text-gray-600 dark:text-gray-400 mb-1">Bid Price</p>
                            <p className="text-xl font-bold text-green-600 dark:text-green-400">
                                ${exchangeData.bid_price.toLocaleString(undefined, {maximumFractionDigits: 2})}
                            </p>
                        </div>
                        {/* Ask Price */}
                        <div>
                            <p className="text-sm text-gray-600 dark:text-gray-400 mb-1">Ask Price</p>
                            <p className="text-xl font-bold text-red-600 dark:text-red-400">
                                ${exchangeData.ask_price.toLocaleString(undefined, {maximumFractionDigits: 2})}
                            </p>
                        </div>
                        {/* Last Updated Timezone */}
                        <div>
                            <p className="text-sm text-gray-600 dark:text-gray-400 mb-1">Last Updated</p>
                            <p className="text-sm font-semibold text-gray-900 dark:text-white">
                                {new Date(exchangeData.last_refreshed).toLocaleString()}
                            </p>
                            <p className="text-xs text-gray-500 dark:text-gray-500 mt-1">
                                {exchangeData.timezone}
                            </p>
                        </div>
                    </div>
                </div>
            )}

            {/* Popular Pairs Quick Buttons */}
            <div className="bg-white dark:bg-gray-800 rounded-xl shadow-lg p-6 mb-8 animate-fade-in">
                <h3 className="text-xl font-bold text-gray-900 dark:text-white mb-4">Popular Cryptocurrencies</h3>
                <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3">
                    {popularPairs.map((pair, index) => (
                        <button
                            key={index}
                            onClick={() => handleQuickPair(pair.from, pair.to)}
                            className={`px-4 py-3 rounded-lg font-semibold transition-all ${
                                fromCrypto === pair.from && toCurrency === pair.to
                                    ? 'bg-purple-600 text-white'
                                    : 'bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 hover:bg-purple-100 dark:hover:bg-purple-900/30'
                            }`}
                        >
                            {pair.label}
                        </button>
                    ))}
                </div>
            </div>

            {/* Crypto Info Grid (Top 8 Cryptos) */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 animate-fade-in">
                {cryptos.slice(0, 8).map((crypto) => (
                    <button
                        key={crypto.code}
                        onClick={() => {
                            setFromCrypto(crypto.code);
                            // Trigger conversion for the newly selected crypto
                            setTimeout(handleConvert, 100);
                        }}
                        className="bg-white dark:bg-gray-800 rounded-lg p-4 hover:shadow-lg transition-all active:scale-95 text-left"
                    >
                        <div className="flex items-center space-x-3">
                            <span className="text-3xl">{crypto.icon}</span>
                            <div>
                                <p className="font-bold text-gray-900 dark:text-white">{crypto.code}</p>
                                <p className="text-sm text-gray-500 dark:text-gray-400">{crypto.name}</p>
                            </div>
                        </div>
                    </button>
                ))}
            </div>

            {/* Info Note / Disclaimer */}
            <div className="mt-8 bg-purple-50 dark:bg-purple-900/20 border border-purple-200 dark:border-purple-800 rounded-lg p-4 animate-fade-in">
                <p className="text-sm text-purple-800 dark:text-purple-300">
                    <strong>Note:</strong> Cryptocurrency prices are highly volatile and provided by Alpha Vantage. 
                    Prices shown are for informational purposes only. This is not financial advice. 
                    Always do your own research (DYOR) before investing in cryptocurrencies.
                </p>
            </div>
        </div>
    );
};

export default CryptoPage;