import React, { useState, useEffect } from 'react'; // <-- 'useMemo' removed
import { SearchIcon } from './Icons';
import StockDataCard from './ui/StockDataCard';
import PredictionPreviewCard from './ui/PredictionPreviewCard';
import StockChart from './charts/StockChart'; 

const timeFrames = [
    { label: '1D', value: '1d' },
    { label: '5D', value: '5d' },
    { label: '14D', value: '14d' },
    { label: '1M', value: '1mo' },
    { label: '6M', value: '6mo' },
    { label: '1Y', value: '1y' },
];

const SearchPage = ({ onNavigateToPredictions }) => {
    const [ticker, setTicker] = useState('');
    const [searchedTicker, setSearchedTicker] = useState('');
    const [stockData, setStockData] = useState(null);
    const [chartData, setChartData] = useState(null);
    const [activeTimeFrame, setActiveTimeFrame] = useState(timeFrames.find(f => f.value === '14d'));
    const [loading, setLoading] = useState(false);
    const [chartLoading, setChartLoading] = useState(false);
    const [error, setError] = useState('');
    const [recentSearches, setRecentSearches] = useState([]);
    const [predictionData, setPredictionData] = useState(null);
    
    const [compareTicker, setCompareTicker] = useState('');
    const [comparisonData, setComparisonData] = useState(null);

    useEffect(() => {
        const saved = localStorage.getItem('recentSearches');
        if (saved) {
            try {
                setRecentSearches(JSON.parse(saved));
            } catch (e) {
                console.error('Failed to load recent searches:', e);
            }
        }
    }, []);

    const saveRecentSearch = (searchTicker) => {
        const updated = [searchTicker.toUpperCase(), ...recentSearches.filter(t => t !== searchTicker.toUpperCase())].slice(0, 8);
        setRecentSearches(updated);
        localStorage.setItem('recentSearches', JSON.stringify(updated));
    };

    const clearRecentSearches = () => {
        setRecentSearches([]);
        localStorage.removeItem('recentSearches');
    };


    const fetchChartData = async (symbol, timeFrame) => {
        setChartLoading(true);
        setError('');
        try {
            const chartResponse = await fetch(`http://127.0.0.1:5001/chart/${symbol}?period=${timeFrame.value}`);
            if (!chartResponse.ok) {
                const errorData = await chartResponse.json();
                throw new Error(errorData.error || 'Chart data not found');
            }
            const chartJson = await chartResponse.json();
            setChartData(chartJson);
        } catch (err) {
            setError(err.message);
            setChartData(null);
        } finally {
            setChartLoading(false);
        }
    };
    
    const executeSearch = async (searchTicker) => {
        setLoading(true);
        setStockData(null);
        setChartData(null);
        setPredictionData(null);
        setComparisonData(null); 
        setCompareTicker('');
        setError('');

        const defaultTimeFrame = timeFrames.find(f => f.value === '14d');
        setActiveTimeFrame(defaultTimeFrame);

        try {
            const stockResponse = await fetch(`http://127.0.0.1:5001/stock/${searchTicker}`);
            if (!stockResponse.ok) {
                const errorData = await stockResponse.json();
                throw new Error(errorData.error || 'Stock data not found');
            }
            const stockJson = await stockResponse.json();
            setStockData(stockJson);
            setSearchedTicker(searchTicker);
            saveRecentSearch(searchTicker);

            await fetchChartData(searchTicker, defaultTimeFrame);
            
            try {
                const predResponse = await fetch(`http://127.0.0.1:5001/predict/${searchTicker}`);
                if (predResponse.ok) {
                    const predJson = await predResponse.json();
                    setPredictionData(predJson);
                } else {
                    setPredictionData(null);
                }
            } catch {
                setPredictionData(null);
            }

        } catch (err) {
            setError(err.message || 'An error occurred. Try "AAPL", "GOOGL", or "TSLA".');
            setSearchedTicker('');
        } finally {
            setLoading(false);
        }
    };
    
    const handleAddComparison = async (e) => {
        e.preventDefault();
        if (!compareTicker || !activeTimeFrame) return;
        
        try {
            const chartResponse = await fetch(`http://127.0.0.1:5001/chart/${compareTicker}?period=${activeTimeFrame.value}`);
            if (!chartResponse.ok) {
                throw new Error('Comparison ticker data not found');
            }
            const chartJson = await chartResponse.json();
            setComparisonData({ ticker: compareTicker.toUpperCase(), data: chartJson });
            setCompareTicker(''); 
        } catch (err) {
            alert(err.message);
        }
    };

    const handleSearch = (e) => {
        e.preventDefault();
        if (ticker) {
            executeSearch(ticker);
        }
    };

    const handleRecentSearchClick = (recentTicker) => {
        setTicker(recentTicker);
        executeSearch(recentTicker);
    };

    const handleTimeFrameChange = (timeFrame) => {
        setActiveTimeFrame(timeFrame);
        if (searchedTicker) {
            fetchChartData(searchedTicker, timeFrame);
            if (comparisonData) {
                (async () => {
                    try {
                        const chartResponse = await fetch(`http://127.0.0.1:5001/chart/${comparisonData.ticker}?period=${timeFrame.value}`);
                        const chartJson = await chartResponse.json();
                        setComparisonData({ ...comparisonData, data: chartJson });
                    } catch {
                        setComparisonData(null);
                    }
                })();
            }
        }
    };

    const handleAddToWatchlist = async (tickerToAdd) => {
        try {
            const response = await fetch(`http://127.0.0.1:5001/watchlist/${tickerToAdd}`, {
                method: 'POST',
            });
            const result = await response.json();
            alert(result.message);
        } catch (err) {
            alert('Failed to add stock to watchlist. Is the server running?');
        }
    };

    return (
        <div className="container mx-auto px-4 py-16 flex flex-col items-center">
            <div className="w-full max-w-2xl text-center">
                <h1 className="text-5xl font-extrabold text-gray-800 dark:text-white">Stock Ticker Search</h1>
                <p className="text-lg text-gray-500 dark:text-gray-400 mt-3">Enter a stock symbol to get the latest data.</p>
                <form onSubmit={handleSearch} className="mt-8 flex relative">
                    <div className="absolute left-4 top-1/2 transform -translate-y-1/2">
                        <SearchIcon />
                    </div>
                    <input
                        type="text"
                        value={ticker}
                        onChange={(e) => setTicker(e.target.value.toUpperCase())}
                        placeholder="e.g., AAPL"
                        className="w-full pl-12 pr-4 py-4 text-lg border-2 border-gray-200 dark:border-gray-600 dark:bg-gray-800 dark:text-white rounded-l-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none transition-shadow"
                    />
                    <button
                        type="submit"
                        disabled={loading}
                        className="bg-blue-600 text-white font-bold px-8 py-4 rounded-r-lg hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-opacity-50 transition-colors disabled:bg-blue-300"
                    >
                        {loading ? '...' : 'Search'}
                    </button>
                </form>
                
                {recentSearches.length > 0 && (
                    <div className="mt-6 animate-fade-in">
                        <div className="flex items-center justify-between mb-3">
                            <p className="text-sm text-gray-600 dark:text-gray-400">Recent Searches</p>
                            <button
                                onClick={clearRecentSearches}
                                className="text-xs text-red-500 hover:text-red-600 dark:text-red-400 dark:hover:text-red-300 font-medium"
                            >
                                Clear All
                            </button>
                        </div>
                        <div className="flex flex-wrap gap-2">
                            {recentSearches.map((recentTicker) => (
                                <button
                                    key={recentTicker}
                                    onClick={() => handleRecentSearchClick(recentTicker)}
                                    className="px-4 py-2 bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 rounded-full text-sm font-medium hover:bg-blue-100 dark:hover:bg-blue-900/30 hover:text-blue-700 dark:hover:text-blue-400 transition-colors"
                                >
                                    {recentTicker}
                                </button>
                            ))}
                        </div>
                    </div>
                )}
            </div>
            <div className="w-full max-w-4xl mt-4">
                {error && !chartLoading && <div className="text-red-500 text-center p-4 bg-red-100 dark:bg-red-900/30 dark:text-red-300 rounded-lg">{error}</div>}
                
                {stockData && <StockDataCard data={stockData} onAddToWatchlist={handleAddToWatchlist} />}
                
                {predictionData && (
                    <PredictionPreviewCard 
                        predictionData={predictionData}
                        onViewFullPredictions={() => {
                            if (onNavigateToPredictions) {
                                onNavigateToPredictions(searchedTicker);
                            }
                        }}
                    />
                )}
                {chartLoading && <div className="text-center p-8 text-gray-500 dark:text-gray-400">Loading chart...</div>}
                {chartData && !chartLoading && (
                    <div className="mt-8 bg-white dark:bg-gray-800 p-4 sm:p-6 rounded-xl shadow-lg animate-fade-in">
                        {/* --- Comparison Input --- */}
                        <form onSubmit={handleAddComparison} className="flex gap-2 mb-4">
                            <input
                                type="text"
                                value={compareTicker}
                                onChange={(e) => setCompareTicker(e.target.value.toUpperCase())}
                                placeholder="Compare (e.g., MSFT)"
                                className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 dark:bg-gray-700 dark:text-white rounded-lg focus:ring-2 focus:ring-blue-500 outline-none"
                            />
                            <button
                                type="submit"
                                className="px-6 py-2 bg-gray-600 hover:bg-gray-700 text-white rounded-lg font-semibold transition-all"
                            >
                                Add
                            </button>
                        </form>
                        
                        {/* --- The Chart Component --- */}
                        <StockChart
                            chartData={chartData}
                            ticker={searchedTicker}
                            onTimeFrameChange={handleTimeFrameChange}
                            activeTimeFrame={activeTimeFrame}
                            comparisonData={comparisonData} // Pass comparison data
                        />
                    </div>
                )}
            </div>

        </div>
    );
};

export default SearchPage;