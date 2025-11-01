import React, { useState } from 'react';
import StockPredictionCard from './ui/StockPredictionCard';
import { SearchIcon } from './Icons';

const PredictionsPage = () => {
    const [ticker, setTicker] = useState('');
    const [predictionData, setPredictionData] = useState(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState('');

    const handleSearch = async (e) => {
        e.preventDefault();
        
        if (!ticker.trim()) {
            setError('Please enter a stock ticker');
            return;
        }

        setLoading(true);
        setError('');
        setPredictionData(null);

        try {
            const response = await fetch(`http://localhost:5001/predict/${ticker.toUpperCase()}`);
            
            if (!response.ok) {
                throw new Error('Failed to fetch prediction data');
            }

            const data = await response.json();
            setPredictionData(data);
        } catch (err) {
            setError(`Error: Could not fetch predictions for ${ticker.toUpperCase()}. Please check the ticker and try again.`);
            console.error('Prediction fetch error:', err);
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="container mx-auto px-6 py-8 max-w-5xl">
            <div className="text-center mb-8 animate-fade-in">
                <h1 className="text-4xl font-bold text-gray-900 mb-2">
                    Stock Price Predictions
                </h1>
                <p className="text-gray-600">
                    Get 7-week price predictions powered by machine learning
                </p>
            </div>

            {/* Search Form */}
            <div className="bg-white rounded-xl shadow-lg p-6 mb-8 animate-fade-in">
                <form onSubmit={handleSearch} className="flex gap-4">
                    <div className="flex-1">
                        <div className="relative">
                            <input
                                type="text"
                                value={ticker}
                                onChange={(e) => setTicker(e.target.value.toUpperCase())}
                                placeholder="Enter stock ticker (e.g., AAPL, TSLA, MSFT)"
                                className="w-full px-4 py-3 pl-12 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none transition-all text-lg"
                            />
                            <SearchIcon className="absolute left-4 top-1/2 transform -translate-y-1/2 text-gray-400 w-5 h-5" />
                        </div>
                    </div>
                    <button
                        type="submit"
                        disabled={loading}
                        className={`px-8 py-3 rounded-lg font-semibold text-white transition-all ${
                            loading
                                ? 'bg-gray-400 cursor-not-allowed'
                                : 'bg-blue-600 hover:bg-blue-700 active:scale-95'
                        }`}
                    >
                        {loading ? 'Predicting...' : 'Predict'}
                    </button>
                </form>
            </div>

            {/* Error Message */}
            {error && (
                <div className="bg-red-50 border border-red-200 text-red-700 px-6 py-4 rounded-lg mb-8 animate-fade-in">
                    <p className="font-medium">{error}</p>
                </div>
            )}

            {/* Loading State */}
            {loading && (
                <div className="text-center py-12 animate-fade-in">
                    <div className="inline-block animate-spin rounded-full h-12 w-12 border-4 border-blue-600 border-t-transparent"></div>
                    <p className="mt-4 text-gray-600">Analyzing stock data and generating predictions...</p>
                </div>
            )}

            {/* Prediction Results */}
            {predictionData && !loading && (
                <div className="animate-fade-in">
                    <div className="bg-gradient-to-r from-blue-50 to-indigo-50 rounded-xl p-6 mb-6 border border-blue-100">
                        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                            <div className="text-center">
                                <p className="text-sm text-gray-600 mb-1">Recent Date</p>
                                <p className="text-xl font-bold text-gray-900">{predictionData.recentDate}</p>
                            </div>
                            <div className="text-center">
                                <p className="text-sm text-gray-600 mb-1">Actual Close</p>
                                <p className="text-xl font-bold text-green-600">${predictionData.recentClose}</p>
                            </div>
                            <div className="text-center">
                                <p className="text-sm text-gray-600 mb-1">Predicted Close</p>
                                <p className="text-xl font-bold text-blue-600">${predictionData.recentPredicted}</p>
                            </div>
                        </div>
                    </div>

                    <StockPredictionCard data={predictionData} />

                    <div className="mt-6 bg-blue-50 border border-blue-200 rounded-lg p-4">
                        <h3 className="font-semibold text-blue-900 mb-2">About These Predictions</h3>
                        <ul className="text-sm text-blue-800 space-y-1">
                            <li>• Predictions are based on historical price patterns using machine learning</li>
                            <li>• Lower prediction error percentage indicates higher accuracy</li>
                            <li>• Use predictions as one of many tools for investment research</li>
                            <li>• Past performance does not guarantee future results</li>
                        </ul>
                    </div>
                </div>
            )}

            {/* Empty State */}
            {!predictionData && !loading && !error && (
                <div className="text-center py-16 animate-fade-in">
                    <div className="inline-block p-6 bg-gray-100 rounded-full mb-4">
                        <svg className="w-16 h-16 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                        </svg>
                    </div>
                    <h3 className="text-xl font-semibold text-gray-700 mb-2">
                        Enter a stock ticker to see predictions
                    </h3>
                    <p className="text-gray-500">
                        Get AI-powered 7-week price forecasts for any stock
                    </p>
                </div>
            )}
        </div>
    );
};

export default PredictionsPage;
