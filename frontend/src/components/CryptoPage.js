import React, { useState, useEffect } from 'react';

const CryptoPage = () => {
    const [cryptos, setCryptos] = useState([]);
    const [currencies, setCurrencies] = useState([]);
    const [fromCrypto, setFromCrypto] = useState('BTC');
    const [toCurrency, setToCurrency] = useState('USD');
    const [amount, setAmount] = useState(1);
    const [exchangeData, setExchangeData] = useState(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState('');

    // Popular crypto pairs for quick access
    const popularPairs = [
        { from: 'BTC', to: 'USD', label: 'BTC → USD' },
        { from: 'ETH', to: 'USD', label: 'ETH → USD' },
        { from: 'BNB', to: 'USD', label: 'BNB → USD' },
        { from: 'SOL', to: 'USD', label: 'SOL → USD' },
        { from: 'XRP', to: 'USD', label: 'XRP → USD' },
        { from: 'DOGE', to: 'USD', label: 'DOGE → USD' },
    ];

    // Fetch available cryptos and currencies on mount
    useEffect(() => {
        fetchCryptos();
        fetchCurrencies();
        handleConvert(); // Initial conversion
    }, []);

    const fetchCryptos = async () => {
        try {
            const response = await fetch('http://localhost:5001/crypto/list');
            const data = await response.json();
            setCryptos(data);
        } catch (err) {
            console.error('Error fetching cryptos:', err);
        }
    };

    const fetchCurrencies = async () => {
        try {
            const response = await fetch('http://localhost:5001/crypto/currencies');
            const data = await response.json();
            setCurrencies(data);
        } catch (err) {
            console.error('Error fetching currencies:', err);
        }
    };

    const handleConvert = async () => {
        setLoading(true);
        setError('');
        
        try {
            const response = await fetch(
                `http://localhost:5001/crypto/convert?from=${fromCrypto}&to=${toCurrency}`
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

    const handleQuickPair = (from, to) => {
        setFromCrypto(from);
        setToCurrency(to);
        setTimeout(handleConvert, 100);
    };

    const convertedAmount = exchangeData ? (amount * exchangeData.exchange_rate).toFixed(2) : '0.00';
    const formattedRate = exchangeData ? exchangeData.exchange_rate.toLocaleString(undefined, {minimumFractionDigits: 2, maximumFractionDigits: 2}) : '0.00';

    return (
        <div className="container mx-auto px-6 py-8 max-w-6xl">
            {/* Header */}
            <div className="text-center mb-8 animate-fade-in">
                <h1 className="text-4xl font-bold text-gray-900 dark:text-white mb-2">
                    🪙 Cryptocurrency Exchange
                </h1>
                <p className="text-gray-600 dark:text-gray-400">
                    Real-time cryptocurrency prices powered by Alpha Vantage
                </p>
            </div>

            {/* Main Converter Card */}
            <div className="bg-white dark:bg-gray-800 rounded-xl shadow-lg p-8 mb-8 animate-fade-in transition-colors duration-200">
                <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-6">Crypto Converter</h2>
                
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6 items-end">
                    {/* From Crypto */}
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
                                {cryptos.map((crypto) => (
                                    <option key={crypto.code} value={crypto.code}>
                                        {crypto.icon} {crypto.code} - {crypto.name}
                                    </option>
                                ))}
                            </select>
                        </div>
                    </div>

                    {/* To Currency */}
                    <div>
                        <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                            To Fiat Currency
                        </label>
                        <div className="space-y-2">
                            <div className="w-full px-4 py-3 border border-gray-300 dark:border-gray-600 dark:bg-gray-900 dark:text-white rounded-lg font-bold text-lg bg-gray-50">
                                {loading ? '...' : `${currencies.find(c => c.code === toCurrency)?.symbol || '$'}${convertedAmount}`}
                            </div>
                            <select
                                value={toCurrency}
                                onChange={(e) => setToCurrency(e.target.value)}
                                className="w-full px-4 py-3 border border-gray-300 dark:border-gray-600 dark:bg-gray-700 dark:text-white rounded-lg focus:ring-2 focus:ring-purple-500 outline-none"
                            >
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

                {/* Error Message */}
                {error && (
                    <div className="mt-4 bg-red-50 dark:bg-red-900/30 border border-red-200 dark:border-red-800 text-red-700 dark:text-red-300 px-4 py-3 rounded-lg">
                        {error}
                    </div>
                )}
            </div>

            {/* Exchange Rate Details */}
            {exchangeData && !loading && (
                <div className="bg-gradient-to-r from-purple-50 to-pink-50 dark:from-purple-900/30 dark:to-pink-900/30 rounded-xl p-6 mb-8 animate-fade-in border border-purple-100 dark:border-purple-800">
                    <div className="grid grid-cols-1 md:grid-cols-4 gap-4 text-center">
                        <div>
                            <p className="text-sm text-gray-600 dark:text-gray-400 mb-1">Exchange Rate</p>
                            <p className="text-2xl font-bold text-gray-900 dark:text-white">
                                ${formattedRate}
                            </p>
                            <p className="text-xs text-gray-500 dark:text-gray-500 mt-1">
                                1 {exchangeData.from_crypto.code} = ${exchangeData.exchange_rate.toLocaleString(undefined, {maximumFractionDigits: 2})} {exchangeData.to_currency.code}
                            </p>
                        </div>
                        <div>
                            <p className="text-sm text-gray-600 dark:text-gray-400 mb-1">Bid Price</p>
                            <p className="text-xl font-bold text-green-600 dark:text-green-400">
                                ${exchangeData.bid_price.toLocaleString(undefined, {maximumFractionDigits: 2})}
                            </p>
                        </div>
                        <div>
                            <p className="text-sm text-gray-600 dark:text-gray-400 mb-1">Ask Price</p>
                            <p className="text-xl font-bold text-red-600 dark:text-red-400">
                                ${exchangeData.ask_price.toLocaleString(undefined, {maximumFractionDigits: 2})}
                            </p>
                        </div>
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

            {/* Popular Pairs */}
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

            {/* Crypto Info Grid */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 animate-fade-in">
                {cryptos.slice(0, 8).map((crypto) => (
                    <button
                        key={crypto.code}
                        onClick={() => {
                            setFromCrypto(crypto.code);
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

            {/* Info Note */}
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
