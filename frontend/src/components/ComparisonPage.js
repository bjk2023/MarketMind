import React, { useState } from 'react';
import { SearchIcon, TrendingUpIcon, TrendingDownIcon } from './Icons';

// Helper to format numbers
const formatNum = (num, isPercent = false) => {
    if (num === null || num === undefined || isNaN(num)) return 'N/A';
    const val = Number(num);
    if (isPercent) return `${val.toFixed(2)}%`;
    return val.toFixed(2);
};

// Stock comparison card
const ComparisonCard = ({ stock, label }) => {
    if (!stock) {
        return (
            <div className="bg-gray-100 rounded-lg p-6 flex items-center justify-center min-h-96">
                <p className="text-gray-500 text-lg">{label}</p>
            </div>
        );
    }

    const isPositive = stock.change >= 0;
    const changeColor = isPositive ? 'text-green-500' : 'text-red-500';

    return (
        <div className="bg-white rounded-lg p-6 shadow-lg">
            <div className="mb-6 pb-4 border-b">
                <h2 className="text-2xl font-bold text-gray-900">{stock.companyName}</h2>
                <p className="text-sm text-gray-500 mt-1">({stock.ticker})</p>
            </div>

            <div className="space-y-4">
                {/* Price */}
                <div>
                    <div className="flex justify-between items-start">
                        <div>
                            <p className="text-3xl font-bold text-gray-800">${formatNum(stock.price)}</p>
                            <div className={`flex items-center mt-2 text-lg font-semibold ${changeColor}`}>
                                {isPositive ? <TrendingUpIcon className="h-5 w-5 mr-1" /> : <TrendingDownIcon className="h-5 w-5 mr-1" />}
                                {isPositive ? '+' : ''}{formatNum(stock.change)} ({formatNum(stock.change_percent)}%)
                            </div>
                        </div>
                    </div>
                </div>

                {/* Divider */}
                <hr className="my-4" />

                {/* Metrics */}
                <div className="space-y-3">
                    <div className="flex justify-between py-2">
                        <span className="text-gray-600">Market Cap</span>
                        <span className="font-semibold text-gray-800">{stock.marketCap || 'N/A'}</span>
                    </div>
                    <div className="flex justify-between py-2">
                        <span className="text-gray-600">P/E Ratio</span>
                        <span className="font-semibold text-gray-800">{stock.peRatio ? formatNum(stock.peRatio) : 'N/A'}</span>
                    </div>
                    <div className="flex justify-between py-2">
                        <span className="text-gray-600">52W High</span>
                        <span className="font-semibold text-gray-800">${formatNum(stock.week_52_high)}</span>
                    </div>
                    <div className="flex justify-between py-2">
                        <span className="text-gray-600">52W Low</span>
                        <span className="font-semibold text-gray-800">${formatNum(stock.week_52_low)}</span>
                    </div>
                    <div className="flex justify-between py-2">
                        <span className="text-gray-600">52W Range</span>
                        <span className="font-semibold text-gray-800">
                            {(((stock.price - stock.week_52_low) / (stock.week_52_high - stock.week_52_low)) * 100).toFixed(0)}%
                        </span>
                    </div>
                </div>
            </div>
        </div>
    );
};

// Comparison metrics table
const ComparisonMetrics = ({ stock1, stock2 }) => {
    if (!stock1 || !stock2) return null;

    const metrics = [
        { label: 'Current Price', key: 'price', format: (val) => `$${formatNum(val)}` },
        { label: 'Price Change', key: 'change', format: (val) => `${val >= 0 ? '+' : ''}${formatNum(val)}` },
        { label: 'Change %', key: 'change_percent', format: (val) => `${val >= 0 ? '+' : ''}${formatNum(val, true)}` },
        { label: 'Market Cap', key: 'marketCap', format: (val) => val || 'N/A' },
        { label: 'P/E Ratio', key: 'peRatio', format: (val) => val ? formatNum(val) : 'N/A' },
        { label: '52W High', key: 'week_52_high', format: (val) => `$${formatNum(val)}` },
        { label: '52W Low', key: 'week_52_low', format: (val) => `$${formatNum(val)}` },
    ];

    return (
        <div className="bg-white rounded-lg shadow-lg overflow-hidden mt-8">
            <table className="w-full">
                <thead className="bg-gray-100 border-b">
                    <tr>
                        <th className="px-6 py-3 text-left text-sm font-semibold text-gray-700">Metric</th>
                        <th className="px-6 py-3 text-right text-sm font-semibold text-gray-700">{stock1.ticker}</th>
                        <th className="px-6 py-3 text-right text-sm font-semibold text-gray-700">{stock2.ticker}</th>
                        <th className="px-6 py-3 text-right text-sm font-semibold text-gray-700">Difference</th>
                    </tr>
                </thead>
                <tbody>
                    {metrics.map((metric, idx) => {
                        const val1 = stock1[metric.key];
                        const val2 = stock2[metric.key];
                        const isNumeric = typeof val1 === 'number' && typeof val2 === 'number';
                        const diff = isNumeric ? val1 - val2 : null;
                        const diffPercent = isNumeric && val2 !== 0 ? ((diff / val2) * 100).toFixed(2) : null;

                        return (
                            <tr key={idx} className="border-b border-gray-200 hover:bg-gray-50">
                                <td className="px-6 py-3 text-sm text-gray-700 font-medium">{metric.label}</td>
                                <td className="px-6 py-3 text-sm text-right text-gray-800 font-semibold">{metric.format(val1)}</td>
                                <td className="px-6 py-3 text-sm text-right text-gray-800 font-semibold">{metric.format(val2)}</td>
                                <td className={`px-6 py-3 text-sm text-right font-semibold ${diff > 0 ? 'text-green-600' : diff < 0 ? 'text-red-600' : 'text-gray-600'}`}>
                                    {diff !== null ? `${diff > 0 ? '+' : ''}${formatNum(diff)} (${diffPercent}%)` : 'N/A'}
                                </td>
                            </tr>
                        );
                    })}
                </tbody>
            </table>
        </div>
    );
};

const ComparisonPage = () => {
    const [ticker1, setTicker1] = useState('');
    const [ticker2, setTicker2] = useState('');
    const [stock1, setStock1] = useState(null);
    const [stock2, setStock2] = useState(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState('');

    const fetchStock = async (ticker) => {
        try {
            const response = await fetch(`http://127.0.0.1:5001/stock/${ticker.toUpperCase()}`);
            if (!response.ok) {
                throw new Error('Stock not found');
            }
            return await response.json();
        } catch (err) {
            throw new Error(`Failed to fetch ${ticker}: ${err.message}`);
        }
    };

    const handleCompare = async (e) => {
        e.preventDefault();
        if (!ticker1 || !ticker2) {
            setError('Please enter both stock symbols');
            return;
        }

        if (ticker1.toUpperCase() === ticker2.toUpperCase()) {
            setError('Please enter two different stock symbols');
            return;
        }

        setLoading(true);
        setError('');
        setStock1(null);
        setStock2(null);

        try {
            const [s1, s2] = await Promise.all([
                fetchStock(ticker1),
                fetchStock(ticker2)
            ]);
            setStock1(s1);
            setStock2(s2);
        } catch (err) {
            setError(err.message);
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="container mx-auto px-4 py-8">
            <h1 className="text-4xl font-bold text-gray-800 mb-8">Stock Comparison</h1>

            {/* Input Form */}
            <div className="bg-white rounded-lg shadow-lg p-8 mb-8">
                <form onSubmit={handleCompare} className="flex gap-4">
                    <div className="flex-1">
                        <input
                            type="text"
                            value={ticker1}
                            onChange={(e) => setTicker1(e.target.value.toUpperCase())}
                            placeholder="Stock 1 (e.g., AAPL)"
                            className="w-full px-4 py-3 border-2 border-gray-200 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none transition-shadow"
                        />
                    </div>
                    <div className="flex items-center text-2xl text-gray-400">vs</div>
                    <div className="flex-1">
                        <input
                            type="text"
                            value={ticker2}
                            onChange={(e) => setTicker2(e.target.value.toUpperCase())}
                            placeholder="Stock 2 (e.g., GOOGL)"
                            className="w-full px-4 py-3 border-2 border-gray-200 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none transition-shadow"
                        />
                    </div>
                    <button
                        type="submit"
                        disabled={loading}
                        className="bg-blue-600 text-white font-bold px-8 py-3 rounded-lg hover:bg-blue-700 transition-colors disabled:bg-blue-300"
                    >
                        {loading ? 'Comparing...' : 'Compare'}
                    </button>
                </form>

                {error && (
                    <div className="mt-4 text-red-600 bg-red-100 p-3 rounded-lg">
                        {error}
                    </div>
                )}
            </div>

            {/* Comparison Results */}
            {stock1 && stock2 && (
                <>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-8 mb-8">
                        <ComparisonCard stock={stock1} label="Stock 1" />
                        <ComparisonCard stock={stock2} label="Stock 2" />
                    </div>

                    <ComparisonMetrics stock1={stock1} stock2={stock2} />
                </>
            )}

            {!stock1 && !stock2 && !error && (
                <div className="text-center py-12">
                    <SearchIcon className="h-16 w-16 mx-auto text-gray-300 mb-4" />
                    <p className="text-lg text-gray-500">Enter two stock symbols to compare</p>
                </div>
            )}
        </div>
    );
};

export default ComparisonPage;
