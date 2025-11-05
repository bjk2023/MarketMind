import React, { useState, useMemo } from 'react';
import { SearchIcon, TrendingUpIcon, TrendingDownIcon } from './Icons';
import StockChart from './charts/StockChart';
import StockDataCard from './ui/StockDataCard';
import { Line, Chart } from 'react-chartjs-2';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  TimeScale,
  Filler, // Filler is needed for gradient backgrounds
} from 'chart.js';
import { CandlestickController, CandlestickElement } from 'chartjs-chart-financial';
import 'chartjs-adapter-date-fns';

// Register all necessary components for Chart.js
ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  TimeScale,
  Filler, // Register Filler plugin
  CandlestickController,
  CandlestickElement
);

const timeFrames = [
    { label: '1D', value: '1d' },
    { label: '5D', value: '5d' },
    { label: '14D', value: '14d' },
    { label: '1M', value: '1mo' },
    { label: '6M', value: '6mo' },
    { label: '1Y', value: '1y' },
];

const SearchPage = () => {
    const [ticker, setTicker] = useState('');
    const [searchedTicker, setSearchedTicker] = useState('');
    const [stockData, setStockData] = useState(null);
    const [chartData, setChartData] = useState(null);
    const [activeTimeFrame, setActiveTimeFrame] = useState(timeFrames.find(f => f.value === '14d'));
    const [loading, setLoading] = useState(false);
    const [chartLoading, setChartLoading] = useState(false);
    const [error, setError] = useState('');


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

    const handleSearch = async (e) => {
        e.preventDefault();
        if (!ticker) return;

        setLoading(true);
        setStockData(null);
        setChartData(null);
        setError('');

        const defaultTimeFrame = timeFrames.find(f => f.value === '14d');
        setActiveTimeFrame(defaultTimeFrame);

        try {
            const stockResponse = await fetch(`http://127.0.0.1:5001/stock/${ticker}`);
            if (!stockResponse.ok) {
                const errorData = await stockResponse.json();
                throw new Error(errorData.error || 'Stock data not found');
            }
            const stockJson = await stockResponse.json();
            setStockData(stockJson);
            setSearchedTicker(ticker);

            await fetchChartData(ticker, defaultTimeFrame);

        } catch (err) {
            setError(err.message || 'An error occurred. Try "AAPL", "GOOGL", or "TSLA".');
            setSearchedTicker('');
        } finally {
            setLoading(false);
        }

    };

    const handleTimeFrameChange = (timeFrame) => {
        setActiveTimeFrame(timeFrame);
        if (searchedTicker) {
            fetchChartData(searchedTicker, timeFrame);
        }
    };

    const handleAddToWatchlist = async (tickerToAdd) => {
        try {
            const response = await fetch(`http://127.0.0.1:5001/watchlist/${tickerToAdd}`, {
                method: 'POST',
            });
            const result = await response.json();
             // You can use a more sophisticated notification system later
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
            </div>
            <div className="w-full max-w-4xl mt-4">
                {error && !chartLoading && <div className="text-red-500 text-center p-4 bg-red-100 dark:bg-red-900/30 dark:text-red-300 rounded-lg">{error}</div>}
                {stockData && <StockDataCard data={stockData} onAddToWatchlist={handleAddToWatchlist} />}
                {chartLoading && <div className="text-center p-8 text-gray-500 dark:text-gray-400">Loading chart...</div>}
                {chartData && !chartLoading && (
                    <StockChart
                        chartData={chartData}
                        ticker={searchedTicker}
                        onTimeFrameChange={handleTimeFrameChange}
                    />
                )}
            </div>

        </div>
    );
};

export default SearchPage;