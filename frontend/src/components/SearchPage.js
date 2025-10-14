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
    { label: '1M', value: '1mo' },
    { label: '6M', value: '6mo' },
    { label: '1Y', value: '1y' },
];
/* OLD CHART
const StockChart = ({ chartData, ticker, onTimeFrameChange, activeTimeFrame }) => {
    const [chartType, setChartType] = useState('line');

    const chartConfig = useMemo(() => {
        if (!chartData || chartData.length === 0) return null;

        const labels = chartData.map(d => new Date(d.date));

        const options = {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { display: false },
                title: {
                    display: true,
                    text: `${ticker} Price History (${activeTimeFrame.label})`,
                    font: { size: 18 },
                    padding: { top: 10, bottom: 20 }
                },
            },
            scales: {
                x: {
                    type: 'time',
                    time: {
                        unit: activeTimeFrame.value === '1d' ? 'hour' : 'day',
                        tooltipFormat: 'MMM dd, yyyy HH:mm',
                    },
                    grid: { display: false }
                },
                y: {
                     grid: { color: 'rgba(200, 200, 200, 0.1)' }
                }
            },
            interaction: {
                intersect: false,
                mode: 'index',
            },
            elements: {
                point: {
                    radius: 0 // Hide points on the line
                }
            }
        };

        let data;
        let ChartComponent = Line;

        if (chartType === 'line') {
            data = {
                labels,
                datasets: [{
                    label: 'Price',
                    data: chartData.map(d => d.close),
                    fill: 'start',
                    // Logic for gradient background color
                    backgroundColor: (context) => {
                        const ctx = context.chart.ctx;
                        const gradient = ctx.createLinearGradient(0, 0, 0, 400);
                        const lastPrice = chartData[chartData.length - 1].close;
                        const firstPrice = chartData[0].close;
                        const isUp = lastPrice >= firstPrice;
                        gradient.addColorStop(0, isUp ? 'rgba(16, 185, 129, 0.4)' : 'rgba(239, 68, 68, 0.4)');
                        gradient.addColorStop(1, 'rgba(0, 0, 0, 0)');
                        return gradient;
                    },
                     // Logic for segmented line color (red/green)
                    segment: {
                        borderColor: (ctx) => {
                            const y1 = ctx.p0.parsed.y;
                            const y2 = ctx.p1.parsed.y;
                            return y2 >= y1 ? '#10B981' : '#EF4444';
                        }
                    },
                    borderWidth: 2,
                }]
            };
        } else { // Candlestick
             data = {
                datasets: [{
                    label: `${ticker} OHLC`,
                    data: chartData.map(d => ({
                        x: new Date(d.date).valueOf(),
                        o: d.open,
                        h: d.high,
                        l: d.low,
                        c: d.close
                    }))
                }]
            };
            ChartComponent = Chart; // Use the generic Chart component for custom types
        }

        return { type: chartType, options, data, ChartComponent };

    }, [chartData, chartType, ticker, activeTimeFrame]);

    if (!chartConfig) return null;
    const { type, options, data, ChartComponent } = chartConfig;

    return (
        <div className="mt-8 bg-white p-4 sm:p-6 rounded-xl shadow-lg animate-fade-in">
            <div className="flex flex-col sm:flex-row justify-between items-center mb-4 gap-4">
                 <div className="flex items-center space-x-1 bg-gray-100 p-1 rounded-lg">
                    {timeFrames.map((frame) => (
                        <button
                            key={frame.value}
                            onClick={() => onTimeFrameChange(frame)}
                            className={`px-3 py-1 text-sm font-semibold rounded-md transition-colors duration-200 ${
                                activeTimeFrame.value === frame.value
                                ? 'bg-blue-600 text-white shadow'
                                : 'text-gray-600 hover:bg-gray-200'
                            }`}
                        >
                            {frame.label}
                        </button>
                    ))}
                </div>
                <select
                    value={chartType}
                    onChange={(e) => setChartType(e.target.value)}
                    className="p-2 border rounded-lg bg-gray-50 focus:ring-2 focus:ring-blue-500 outline-none text-sm"
                >
                    <option value="line">Line Chart</option>
                    <option value="candlestick">Candlestick</option>
                </select>
            </div>
            <div className="h-96">
                <ChartComponent type={type} options={options} data={data} />
            </div>
        </div>
    );
};


const StockDataCard = ({ data, onAddToWatchlist }) => {
    const isPositive = data.change >= 0;
    const changeColor = isPositive ? 'text-green-500' : 'text-red-500';

    const DataRow = ({ label, value }) => (
        <div className="flex justify-between py-3 border-b border-gray-200 last:border-b-0">
            <span className="text-sm text-gray-500">{label}</span>
            <span className="text-sm font-medium text-gray-800">{String(value)}</span>
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
                    <button
                        onClick={() => onAddToWatchlist(data.symbol)}
                        className="mt-4 bg-blue-500 text-white font-semibold py-2 px-4 rounded-lg hover:bg-blue-600 transition-colors"
                    >
                        + Add to Watchlist
                    </button>
                </div>
            </div>
            <div className="mt-6">
                <DataRow label="Market Cap" value={data.marketCap} />
                <DataRow label="P/E Ratio" value={data.peRatio} />
                <DataRow label="52 Week High" value={`$${data.week52High.toFixed(2)}`} />
                <DataRow label="52 Week Low" value={`$${data.week52Low.toFixed(2)}`} />
            </div>
        </div>
    );
};
*/
const SearchPage = () => {
    const [ticker, setTicker] = useState('');
    const [searchedTicker, setSearchedTicker] = useState('');
    const [stockData, setStockData] = useState(null);
    const [chartData, setChartData] = useState(null);
    const [activeTimeFrame, setActiveTimeFrame] = useState(timeFrames.find(f => f.value === '6mo'));
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

        const defaultTimeFrame = timeFrames.find(f => f.value === '6mo');
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
                {error && !chartLoading && <div className="text-red-500 text-center p-4 bg-red-100 rounded-lg">{error}</div>}
                {stockData && <StockDataCard data={stockData} onAddToWatchlist={handleAddToWatchlist} />}
                {chartLoading && <div className="text-center p-8 text-gray-500">Loading chart...</div>}
                {chartData && !chartLoading && (
                    <StockChart
                        chartData={chartData}
                        ticker={searchedTicker}
                        onTimeFrameChange={handleTimeFrameChange}
                        activeTimeFrame={activeTimeFrame}
                    />
                )}
            </div>
        </div>
    );
};

export default SearchPage;

