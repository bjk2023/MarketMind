import React, { useState, useMemo } from 'react';
import { SearchIcon, TrendingUpIcon, TrendingDownIcon } from './Icons';
import { Line, Bar, Chart } from 'react-chartjs-2';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  Title,
  Tooltip,
  Legend,
  TimeScale,
} from 'chart.js';
import { CandlestickController, CandlestickElement, OhlcController, OhlcElement } from 'chartjs-chart-financial';
import 'chartjs-adapter-date-fns';

// Register all necessary components for Chart.js
ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  Title,
  Tooltip,
  Legend,
  TimeScale,
  CandlestickController,
  CandlestickElement,
  OhlcController,
  OhlcElement
);


const StockChart = ({ chartData }) => {
    const [chartType, setChartType] = useState('line');

    const chartConfig = useMemo(() => {
        if (!chartData || chartData.length === 0) return null;
        const labels = chartData.map(d => d.date);
        const options = {
            responsive: true,
            plugins: { legend: { position: 'top' }, title: { display: true, text: 'Stock Price History (Last 100 Days)', font: { size: 18 } } },
            scales: { x: { type: 'time', time: { unit: 'day' }, ticks: { source: 'auto' } } },
        };

        let data;
        if (chartType === 'candlestick') {
            data = { datasets: [{ label: 'OHLC', data: chartData.map(d => ({ x: new Date(d.date).valueOf(), o: d.open, h: d.high, l: d.low, c: d.close })) }] };
        } else {
             data = { labels, datasets: [{ label: 'Closing Price', data: chartData.map(d => d.close), borderColor: 'rgb(53, 162, 235)', backgroundColor: 'rgba(53, 162, 235, 0.5)' }] };
        }
        return { type: chartType, options, data };
    }, [chartData, chartType]);

    if (!chartConfig) return null;

    return (
         <div className="mt-8 bg-white p-6 rounded-xl shadow-lg animate-fade-in">
            <div className="flex justify-end mb-4">
                <select value={chartType} onChange={(e) => setChartType(e.target.value)} className="p-2 border rounded-lg bg-gray-50 focus:ring-2 focus:ring-blue-500 outline-none">
                    <option value="line">Line Chart</option>
                    <option value="bar">Bar Chart</option>
                    <option value="candlestick">Candlestick Chart</option>
                </select>
            </div>
            {chartType === 'line' && <Line options={chartConfig.options} data={chartConfig.data} />}
            {chartType === 'bar' && <Bar options={chartConfig.options} data={chartConfig.data} />}
            {chartType === 'candlestick' && <Chart type='candlestick' options={chartConfig.options} data={chartConfig.data} />}
        </div>
    );
};

// --- THIS COMPONENT IS UPDATED ---
const StockDataCard = ({ data, onAddToWatchlist }) => {
    const isPositive = data.change >= 0;
    const changeColor = isPositive ? 'text-green-500' : 'text-red-500';

    const DataRow = ({ label, value }) => (
        <div className="flex justify-between py-3 border-b border-gray-200 last:border-b-0">
            <span className="text-sm text-gray-500">{label}</span>
            <span className="text-sm font-medium text-gray-800">{value}</span>
        </div>
    );

    return (
        <div className="mt-8 bg-white p-6 rounded-xl shadow-lg animate-fade-in">
            <div className="flex justify-between items-start">
                <div>
                    <h2 className="text-2xl font-bold text-gray-900">{data.companyName} ({data.symbol})</h2>
                    <p className="text-3xl font-bold text-gray-800 mt-2">${data.price.toFixed(2)}</p>
                </div>
                <div className="text-right">
                    <div className={`flex items-center justify-end text-lg font-semibold ${changeColor}`}>
                         {isPositive ? <TrendingUpIcon className="h-6 w-6 mr-1" /> : <TrendingDownIcon className="h-6 w-6 mr-1" />}
                        <span>{data.change.toFixed(2)} ({data.changePercent.toFixed(2)}%)</span>
                    </div>
                     {/* --- THIS BUTTON IS NEW --- */}
                    <button
                        onClick={() => onAddToWatchlist(data.symbol)}
                        className="mt-4 bg-blue-500 text-white font-semibold py-2 px-4 rounded-lg hover:bg-blue-600 transition-colors"
                    >
                        + Add to Watchlist
                    </button>
                </div>
            </div>
            <div className="mt-6 space-y-2">
                <DataRow label="Market Cap" value={data.marketCap} />
                <DataRow label="P/E Ratio" value={data.peRatio} />
                <DataRow label="52 Week High" value={`$${data.week52High.toFixed(2)}`} />
                <DataRow label="52 Week Low" value={`$${data.week52Low.toFixed(2)}`} />
            </div>
        </div>
    );
};

const StockPredictionCard = ({ data }) => {
    const isPositive = data.predictedClose >= data.lastActualClose;
    const change = data.predictedClose - data.lastActualClose;
    const changePercent = (change / data.lastActualClose) * 100;
    const changeColor = isPositive ? 'text-green-500' : 'text-red-500';

    return (
        <div className="mt-8 bg-white p-6 rounded-xl shadow-lg animate-fade-in">
            <div className="flex justify-between items-start">
                <div>
                    <h2 className="text-2xl font-bold text-gray-900">
                        {data.companyName} ({data.symbol})
                    </h2>
                    <p className="text-3xl font-bold text-gray-800 mt-2">
                        Predicted Close: ${data.predictedClose.toFixed(2)}
                    </p>
                    <p className="text-sm text-gray-500 mt-1">
                        Last Actual Close: ${data.lastActualClose.toFixed(2)}
                    </p>
                    <p className="text-sm text-gray-500">
                        Date: {data.nextDate}
                    </p>
                </div>
                <div className={`flex items-center text-lg font-semibold ${changeColor}`}>
                    {isPositive ? (
                        <TrendingUpIcon className="h-6 w-6 mr-1" />
                    ) : (
                        <TrendingDownIcon className="h-6 w-6 mr-1" />
                    )}
                    <span>
                        {change >= 0 ? '+' : ''}
                        {change.toFixed(2)} ({changePercent.toFixed(2)}%)
                    </span>
                </div>
            </div>
        </div>
    );
};

const SearchPage = () => {
    const [ticker, setTicker] = useState('');
    const [stockData, setStockData] = useState(null);
    const [chartData, setChartData] = useState(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState('');
    const [predictionData, setPredictionData] = useState(null);


    const handleSearch = async (e) => {
        e.preventDefault();
        if (!ticker) return;

        setLoading(true);
        setStockData(null);
        setChartData(null);
        setError('');

        try {
            const stockResponse = await fetch(`http://127.0.0.1:5001/stock/${ticker}`);
            if (!stockResponse.ok) {
                const errorData = await stockResponse.json();
                throw new Error(errorData.error || 'Stock data not found');
            }
            const stockJson = await stockResponse.json();
            setStockData(stockJson);

            const chartResponse = await fetch(`http://127.0.0.1:5001/chart/${ticker}`);
             if (!chartResponse.ok) {
                const errorData = await chartResponse.json();
                throw new Error(errorData.error || 'Chart data not found');
            }
            const chartJson = await chartResponse.json();
            setChartData(chartJson);

        } catch (err) {
            setError(err.message || 'An error occurred. Try "AAPL", "GOOGL", or "TSLA".');
        } finally {
            setLoading(false);
        }
        try {
            // Fetch stock data (your existing code)
            const stockResponse = await fetch(`http://127.0.0.1:5001/stock/${ticker}`);
            if (!stockResponse.ok) {
                const errorData = await stockResponse.json();
                throw new Error(errorData.error || 'Stock data not found');
            }
            const stockJson = await stockResponse.json();
            setStockData(stockJson);

            // Fetch prediction data
            const predictionResponse = await fetch(`http://127.0.0.1:5001/predict/${ticker}`);
            if (!predictionResponse.ok) {
                const errorData = await predictionResponse.json();
                throw new Error(errorData.error || 'Prediction not found');
            }
            const predictionJson = await predictionResponse.json();
            setPredictionData(predictionJson);

        // Existing chart fetch...
        } catch (err) {
            setError(err.message || 'An error occurred. Try "AAPL", "GOOGL", or "TSLA".');
        } finally {
            setLoading(false);
        }

    };

    // --- THIS FUNCTION IS NEW ---
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
                <h1 className="text-5xl font-extrabold text-gray-800">Stock Ticker Search</h1>
                <p className="text-lg text-gray-500 mt-3">Enter a stock symbol to get the latest data.</p>
                <form onSubmit={handleSearch} className="mt-8 flex relative">
                    <div className="absolute left-4 top-1/2 transform -translate-y-1/2">
                        <SearchIcon />
                    </div>
                    <input
                        type="text"
                        value={ticker}
                        onChange={(e) => setTicker(e.target.value.toUpperCase())}
                        placeholder="e.g., AAPL"
                        className="w-full pl-12 pr-4 py-4 text-lg border-2 border-gray-200 rounded-l-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none transition-shadow"
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
                {error && <div className="text-red-500 text-center p-4 bg-red-100 rounded-lg">{error}</div>}

                {/* Regular stock data */}
                {stockData && <StockDataCard data={stockData} onAddToWatchlist={handleAddToWatchlist} />}

                {/* Prediction card below */}
                {predictionData && <StockPredictionCard data={predictionData} />}
                
                {/* Chart */}
                {chartData && <StockChart chartData={chartData} />}
            </div>

        </div>
    );
};

export default SearchPage;