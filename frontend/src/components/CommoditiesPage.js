import React, { useState, useEffect } from 'react';

const CommoditiesPage = () => {
    const [commodities, setCommodities] = useState([]);
    const [selectedCommodity, setSelectedCommodity] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState('');

    useEffect(() => {
        fetchCommodities();
    }, []);

    const fetchCommodities = async () => {
        setLoading(true);
        setError('');
        
        try {
            const response = await fetch('http://localhost:5001/commodities/list');
            const data = await response.json();
            setCommodities(data);
            
            // Load first commodity by default
            if (data.length > 0) {
                await loadCommodityPrice(data[0].code);
            }
        } catch (err) {
            setError('Could not fetch commodities list.');
            console.error('Fetch error:', err);
        } finally {
            setLoading(false);
        }
    };

    const loadCommodityPrice = async (code) => {
        try {
            const response = await fetch(`http://localhost:5001/commodities/price/${code}`);
            const data = await response.json();
            setSelectedCommodity(data);
        } catch (err) {
            console.error('Price fetch error:', err);
        }
    };

    const handleCommoditySelect = (code) => {
        loadCommodityPrice(code);
    };

    // Group commodities by category
    const groupedCommodities = commodities.reduce((acc, comm) => {
        if (!acc[comm.category]) {
            acc[comm.category] = [];
        }
        acc[comm.category].push(comm);
        return acc;
    }, {});

    return (
        <div className="container mx-auto px-6 py-8 max-w-7xl">
            {/* Header */}
            <div className="text-center mb-8 animate-fade-in">
                <h1 className="text-4xl font-bold text-gray-900 dark:text-white mb-2">
                    📊 Commodities Market
                </h1>
                <p className="text-gray-600 dark:text-gray-400">
                    Real-time prices for energy, metals, and agricultural commodities
                </p>
            </div>

            {loading && (
                <div className="text-center py-12">
                    <div className="inline-block animate-spin rounded-full h-12 w-12 border-4 border-orange-600 border-t-transparent"></div>
                    <p className="mt-4 text-gray-600 dark:text-gray-400">Loading commodities...</p>
                </div>
            )}

            {error && (
                <div className="bg-red-50 dark:bg-red-900/30 border border-red-200 dark:border-red-800 text-red-700 dark:text-red-300 px-6 py-4 rounded-lg mb-8">
                    {error}
                </div>
            )}

            {!loading && selectedCommodity && (
                <div className="space-y-8 animate-fade-in">
                    {/* Current Selection Card */}
                    <div className="bg-gradient-to-r from-orange-50 to-amber-50 dark:from-orange-900/30 dark:to-amber-900/30 rounded-xl p-8 border border-orange-100 dark:border-orange-800">
                        <div className="flex items-center justify-between mb-6">
                            <div className="flex items-center space-x-4">
                                <span className="text-5xl">{selectedCommodity.icon}</span>
                                <div>
                                    <h2 className="text-3xl font-bold text-gray-900 dark:text-white">
                                        {selectedCommodity.name}
                                    </h2>
                                    <p className="text-gray-600 dark:text-gray-400">{selectedCommodity.full_name}</p>
                                </div>
                            </div>
                            <span className="px-4 py-2 bg-orange-600 text-white rounded-lg font-semibold">
                                {selectedCommodity.category}
                            </span>
                        </div>

                        <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
                            <div className="bg-white dark:bg-gray-800 rounded-lg p-4">
                                <p className="text-sm text-gray-600 dark:text-gray-400 mb-1">Current Price</p>
                                <p className="text-3xl font-bold text-gray-900 dark:text-white">
                                    ${selectedCommodity.current_price.toLocaleString()}
                                </p>
                                <p className="text-xs text-gray-500 dark:text-gray-500 mt-1">
                                    {selectedCommodity.unit}
                                </p>
                            </div>

                            <div className="bg-white dark:bg-gray-800 rounded-lg p-4">
                                <p className="text-sm text-gray-600 dark:text-gray-400 mb-1">Previous Price</p>
                                <p className="text-2xl font-bold text-gray-700 dark:text-gray-300">
                                    ${selectedCommodity.previous_price.toLocaleString()}
                                </p>
                            </div>

                            <div className="bg-white dark:bg-gray-800 rounded-lg p-4">
                                <p className="text-sm text-gray-600 dark:text-gray-400 mb-1">Change</p>
                                <p className={`text-2xl font-bold ${
                                    selectedCommodity.price_change >= 0 
                                        ? 'text-green-600 dark:text-green-400' 
                                        : 'text-red-600 dark:text-red-400'
                                }`}>
                                    {selectedCommodity.price_change >= 0 ? '+' : ''}${selectedCommodity.price_change}
                                </p>
                            </div>

                            <div className="bg-white dark:bg-gray-800 rounded-lg p-4">
                                <p className="text-sm text-gray-600 dark:text-gray-400 mb-1">% Change</p>
                                <p className={`text-2xl font-bold ${
                                    selectedCommodity.price_change_percent >= 0 
                                        ? 'text-green-600 dark:text-green-400' 
                                        : 'text-red-600 dark:text-red-400'
                                }`}>
                                    {selectedCommodity.price_change_percent >= 0 ? '+' : ''}{selectedCommodity.price_change_percent}%
                                </p>
                            </div>
                        </div>

                        <div className="mt-4 text-center">
                            <p className="text-sm text-gray-600 dark:text-gray-400">
                                Last Updated: {selectedCommodity.date}
                            </p>
                        </div>
                    </div>

                    {/* Commodities Grid by Category */}
                    {Object.entries(groupedCommodities).map(([category, items]) => (
                        <div key={category} className="bg-white dark:bg-gray-800 rounded-xl shadow-lg p-6">
                            <h3 className="text-2xl font-bold text-gray-900 dark:text-white mb-4 flex items-center">
                                {category === 'Energy' && '⚡'}
                                {category === 'Metals' && '🔩'}
                                {category === 'Agriculture' && '🌾'}
                                <span className="ml-2">{category}</span>
                            </h3>
                            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                                {items.map((commodity) => (
                                    <button
                                        key={commodity.code}
                                        onClick={() => handleCommoditySelect(commodity.code)}
                                        className={`p-4 rounded-lg text-left transition-all hover:shadow-lg active:scale-95 ${
                                            selectedCommodity && selectedCommodity.code === commodity.code
                                                ? 'bg-orange-100 dark:bg-orange-900/30 border-2 border-orange-500'
                                                : 'bg-gray-50 dark:bg-gray-700 border-2 border-transparent hover:border-orange-300 dark:hover:border-orange-700'
                                        }`}
                                    >
                                        <div className="flex items-center space-x-3">
                                            <span className="text-3xl">{commodity.icon}</span>
                                            <div className="flex-1">
                                                <p className="font-bold text-gray-900 dark:text-white">
                                                    {commodity.name}
                                                </p>
                                                <p className="text-xs text-gray-500 dark:text-gray-400">
                                                    {commodity.unit}
                                                </p>
                                            </div>
                                            <svg className="w-5 h-5 text-orange-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                                            </svg>
                                        </div>
                                    </button>
                                ))}
                            </div>
                        </div>
                    ))}

                    {/* Info Note */}
                    <div className="bg-amber-50 dark:bg-amber-900/20 border border-amber-200 dark:border-amber-800 rounded-lg p-4">
                        <h3 className="font-semibold text-amber-900 dark:text-amber-300 mb-2">About Commodities</h3>
                        <ul className="text-sm text-amber-800 dark:text-amber-300 space-y-1">
                            <li>• <strong>Energy:</strong> Crude oil (WTI, Brent) and natural gas prices</li>
                            <li>• <strong>Metals:</strong> Industrial metals like copper and aluminum</li>
                            <li>• <strong>Agriculture:</strong> Soft commodities like wheat, corn, coffee, sugar, and cotton</li>
                            <li>• Prices are provided by Alpha Vantage and updated daily</li>
                            <li>• This data is for informational purposes only, not financial advice</li>
                        </ul>
                    </div>
                </div>
            )}
        </div>
    );
};

export default CommoditiesPage;
