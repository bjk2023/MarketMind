import React, { useState, useMemo, forwardRef, useImperativeHandle } from 'react';
import { SearchIcon, TrendingUpIcon, TrendingDownIcon } from './Icons';
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
  Filler,
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
  Filler,
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

// Helper to format large numbers
const formatLargeNumber = (num) => {
    if (!num || isNaN(num)) return 'N/A';
    if (num >= 1e12) return `${(num / 1e12).toFixed(2)}T`;
    if (num >= 1e9) return `${(num / 1e9).toFixed(2)}B`;
    if (num >= 1e6) return `${(num / 1e6).toFixed(2)}M`;
    return num.toLocaleString();
};

// Helper to safely format numbers to 2 decimal places
const formatNum = (num, isPercent = false) => {
    if (num === null || num === undefined || isNaN(num)) return 'N/A';
    const val = Number(num);
    if (isPercent) return `${(val * 100).toFixed(2)}%`;
    return val.toFixed(2);
};

export const StockChart = ({ chartData, ticker, onTimeFrameChange, activeTimeFrame }) => {
    // ... (This component is unchanged)
    const [chartType, setChartType] = useState('line');

    const chartConfig = useMemo(() => {
        if (!chartData) return null;
        
        // Transform API response into array of objects
        let transformedData = chartData;
        if (chartData.dates && Array.isArray(chartData.dates)) {
            transformedData = chartData.dates.map((date, i) => ({
                date,
                open: chartData.opens?.[i] || 0,
                high: chartData.highs?.[i] || 0,
                low: chartData.lows?.[i] || 0,
                close: chartData.prices?.[i] || 0,
            }));
        }
        
        if (!transformedData || transformedData.length === 0) return null;
        
        const labels = transformedData.map(d => new Date(d.date));
        const options = {
            responsive: true, maintainAspectRatio: false,
            plugins: {
                legend: { display: false },
                title: { display: true, text: `${ticker} Price History (${activeTimeFrame.label})`, font: { size: 18 }, padding: { top: 10, bottom: 20 } },
            },
            scales: {
                x: { type: 'time', time: { unit: activeTimeFrame.value === '1d' ? 'hour' : 'day', tooltipFormat: 'MMM dd, yyyy HH:mm' }, grid: { display: false } },
                y: { grid: { color: 'rgba(200, 200, 200, 0.1)' } }
            },
            interaction: { intersect: false, mode: 'index' },
            elements: { point: { radius: 0 } }
        };
        let data;
        let ChartComponent = Line;
        if (chartType === 'line') {
            data = {
                labels,
                datasets: [{
                    label: 'Price', data: transformedData.map(d => d.close), fill: 'start',
                    backgroundColor: (context) => {
                        const ctx = context.chart.ctx;
                        const gradient = ctx.createLinearGradient(0, 0, 0, 400);
                        const lastPrice = transformedData[transformedData.length - 1].close;
                        const firstPrice = transformedData[0].close;
                        const isUp = lastPrice >= firstPrice;
                        gradient.addColorStop(0, isUp ? 'rgba(16, 185, 129, 0.4)' : 'rgba(239, 68, 68, 0.4)');
                        gradient.addColorStop(1, 'rgba(0, 0, 0, 0)');
                        return gradient;
                    },
                    segment: {
                        borderColor: (ctx) => (ctx.p1.parsed.y >= ctx.p0.parsed.y ? '#10B981' : '#EF4444'),
                    },
                    borderWidth: 2,
                }]
            };
        } else {
             data = {
                datasets: [{
                    label: `${ticker} OHLC`,
                    data: transformedData.map(d => ({ x: new Date(d.date).valueOf(), o: d.open, h: d.high, l: d.low, c: d.close }))
                }]
            };
            ChartComponent = Chart;
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
                            className={`px-3 py-1 text-sm font-semibold rounded-md transition-colors duration-200 ${ activeTimeFrame.value === frame.value ? 'bg-blue-600 text-white shadow' : 'text-gray-600 hover:bg-gray-200' }`}>
                            {frame.label}
                        </button>
                    ))}
                </div>
                <select value={chartType} onChange={(e) => setChartType(e.target.value)} className="p-2 border rounded-lg bg-gray-50 focus:ring-2 focus:ring-blue-500 outline-none text-sm">
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
    // ... (This component is unchanged)
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
                    <p className="text-3xl font-bold text-gray-800 mt-2">${formatNum(data.price)}</p>
                </div>
                <div className="text-right">
                    <div className={`flex items-center justify-end text-lg font-semibold ${changeColor}`}>
                         {isPositive ? <TrendingUpIcon className="h-6 w-6 mr-1" /> : <TrendingDownIcon className="h-6 w-6 mr-1" />}
                        <span>{formatNum(data.change)} ({formatNum(data.changePercent)}%)</span>
                    </div>
                    <button onClick={() => onAddToWatchlist(data.symbol)} className="mt-4 bg-blue-500 text-white font-semibold py-2 px-4 rounded-lg hover:bg-blue-600 transition-colors">
                        + Add to Watchlist
                    </button>
                </div>
            </div>
            <div className="mt-6">
                <DataRow label="Market Cap" value={data.marketCap} />
                <DataRow label="P/E Ratio (TTM)" value={formatNum(data.peRatio)} />
                <DataRow label="52 Week High" value={`$${formatNum(data.week52High)}`} />
                <DataRow label="52 Week Low" value={`$${formatNum(data.week52Low)}`} />
            </div>
        </div>
    );
};

// --- MODIFIED: Overview Component (now with "Read More") ---
const StockOverviewCard = ({ summary, financials }) => {
    const [isExpanded, setIsExpanded] = useState(false);
    if (!summary) return null;

    const truncatedSummary = isExpanded ? summary : `${summary.slice(0, 350)}...`;

    return (
        <div className="mt-8 bg-white p-6 rounded-xl shadow-lg animate-fade-in">
            <h2 className="text-2xl font-bold text-gray-900 mb-4">Overview</h2>
            <p className="text-gray-700 leading-relaxed mb-4">
                {truncatedSummary}
                {!isExpanded && (
                    <button onClick={() => setIsExpanded(true)} className="text-blue-600 font-medium ml-1 hover:underline">
                        Read More
                    </button>
                )}
            </p>
            
            {financials && financials.revenue && (
                <div>
                    <h3 className="text-lg font-bold text-gray-900 mb-2">
                        Quarterly Financials (as of {financials.quarterendDate})
                    </h3>
                    <div className="flex gap-4">
                        <div className="p-4 bg-gray-50 rounded-lg flex-1">
                            <h4 className="text-sm text-gray-500">Revenue</h4>
                            <p className="text-xl font-bold text-gray-900">{formatLargeNumber(financials.revenue)}</p>
                        </div>
                        <div className="p-4 bg-gray-50 rounded-lg flex-1">
                            <h4 className="text-sm text-gray-500">Net Income</h4>
                            <p className="text-xl font-bold text-gray-900">{formatLargeNumber(financials.netIncome)}</p>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
};

// --- NEW: Key Metrics Component ---
const KeyMetricsCard = ({ metrics }) => {
    if (!metrics) return null;

    const metricItems = [
        { label: 'Beta (5Y)', value: formatNum(metrics.beta) },
        { label: 'Forward P/E', value: formatNum(metrics.forwardPE) },
        { label: 'PEG Ratio', value: formatNum(metrics.pegRatio) },
        { label: 'Price/Book', value: formatNum(metrics.priceToBook) },
        { label: 'Dividend Yield', value: formatNum(metrics.dividendYield, true) },
    ];

    return (
        <div className="mt-8 bg-white p-6 rounded-xl shadow-lg animate-fade-in">
            <h2 className="text-2xl font-bold text-gray-900 mb-4">Key Metrics</h2>
            <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-4">
                {metricItems.map(item => (
                    <div key={item.label} className="p-4 bg-gray-50 rounded-lg text-center">
                        <h4 className="text-sm font-medium text-gray-500">{item.label}</h4>
                        <p className="text-2xl font-bold text-gray-900 mt-1">{item.value}</p>
                    </div>
                ))}
            </div>
        </div>
    );
};

// --- MODIFIED: Analyst Ratings (now more reliable) ---
const AnalystRatingsCard = ({ ratings, price }) => {
    if (!ratings || !ratings.recommendationKey || !ratings.targetMeanPrice) {
        return null; // Don't render if no ratings
    }

    const { recommendationKey, targetMeanPrice, numberOfAnalystOpinions } = ratings;
    const upsidePercent = ((targetMeanPrice - price) / price) * 100;
    
    // Determine rating color
    let ratingColor = "text-gray-700";
    const key = recommendationKey.toLowerCase();
    if (key.includes("buy")) ratingColor = "text-green-600";
    if (key.includes("sell")) ratingColor = "text-red-600";
    if (key.includes("hold")) ratingColor = "text-yellow-600";

    return (
        <div className="mt-8 bg-white p-6 rounded-xl shadow-lg animate-fade-in">
            <h2 className="text-2xl font-bold text-gray-900 mb-4">Analyst Ratings</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                {/* Rating */}
                <div className="flex flex-col items-center justify-center p-4 bg-gray-50 rounded-lg">
                    <h3 className="text-sm font-medium text-gray-500 uppercase tracking-wider">Analyst Rating</h3>
                    <p className={`text-5xl font-bold capitalize ${ratingColor} mt-2`}>
                        {recommendationKey}
                    </p>
                    <p className="text-sm text-gray-500 mt-1">Based on {numberOfAnalystOpinions} analysts</p>
                </div>
                
                {/* Price Target */}
                <div className="flex flex-col items-center justify-center p-4 bg-gray-50 rounded-lg">
                    <h3 className="text-sm font-medium text-gray-500 uppercase tracking-wider">Mean Price Target</h3>
                    <p className="text-5xl font-bold text-gray-900 mt-2">${formatNum(targetMeanPrice)}</p>
                    <p className={`text-lg font-semibold ${upsidePercent >= 0 ? 'text-green-600' : 'text-red-600'} mt-1`}>
                        {formatNum(upsidePercent)}% {upsidePercent >= 0 ? 'Upside' : 'Downside'}
                    </p>
                </div>
            </div>
        </div>
    );
};


const StockNewsCard = ({ newsData }) => {
    // ... (This component is unchanged)
    const formatDate = (dateString) => {
        try { return new Date(dateString).toLocaleDateString('en-US', { year: 'numeric', month: 'short', day: 'numeric' }); } 
        catch (e) { return 'N/A'; }
    };
    return (
        <div className="mt-8 bg-white p-4 sm:p-6 rounded-xl shadow-lg animate-fade-in">
            <h2 className="text-2xl font-bold text-gray-900 mb-4">Recent News</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                {newsData.map((newsItem, index) => (
                    <a key={index} href={newsItem.link} target="_blank" rel="noopener noreferrer" className="flex flex-col p-4 border rounded-lg hover:bg-gray-50 transition-colors">
                        <div className="flex-1">
                            <h3 className="text-lg font-semibold text-gray-800 mb-2 leading-snug">{newsItem.title}</h3>
                        </div>
                        {newsItem.thumbnail_url && (
                            <img src={newsItem.thumbnail_url} alt={newsItem.title} className="w-full h-40 object-cover rounded-md my-3" />
                        )}
                        <div className="flex justify-between items-center text-sm text-gray-500 mt-2">
                            <span className="font-medium truncate pr-4">{newsItem.publisher}</span>
                            <span className="flex-shrink-0">{formatDate(newsItem.publishTime)}</span>
                        </div>
                    </a>
                ))}
            </div>
        </div>
    );
};


const SearchPageComponent = forwardRef((_, ref) => {
    const [ticker, setTicker] = useState('');
    const [searchedTicker, setSearchedTicker] = useState('');
    const [stockData, setStockData] = useState(null);
    const [chartData, setChartData] = useState(null);
    const [newsData, setNewsData] = useState(null); 
    const [activeTimeFrame, setActiveTimeFrame] = useState(timeFrames.find(f => f.value === '6mo'));
    const [loading, setLoading] = useState(false);
    const [chartLoading, setChartLoading] = useState(false);
    const [newsLoading, setNewsLoading] = useState(false); 
    const [searchHistory, setSearchHistory] = useState(() => {
        // Load search history from localStorage on mount
        const saved = localStorage.getItem('searchHistory');
        return saved ? JSON.parse(saved) : [];
    });

    const [error, setError] = useState('');

    // Add ticker to search history
    const addToSearchHistory = (tickerSymbol) => {
        setSearchHistory(prevHistory => {
            // Remove if already exists, then add to beginning
            const filtered = prevHistory.filter(t => t !== tickerSymbol.toUpperCase());
            const newHistory = [tickerSymbol.toUpperCase(), ...filtered].slice(0, 5); // Keep only last 5
            localStorage.setItem('searchHistory', JSON.stringify(newHistory));
            return newHistory;
        });
    };

    // Clear search history
    const clearSearchHistory = () => {
        setSearchHistory([]);
        localStorage.removeItem('searchHistory');
    };

    // Expose performSearch method to parent
    useImperativeHandle(ref, () => ({
        performSearch: (tickerSymbol) => {
            setTicker(tickerSymbol);
            // Trigger search in the next render
            setTimeout(() => {
                handleSearch({ preventDefault: () => {} }, tickerSymbol);
            }, 0);
        }
    }));

    const fetchChartData = async (symbol, timeFrame) => {
        setChartLoading(true);
        try {
            const chartResponse = await fetch(`http://127.0.0.1:5001/chart/${symbol}?period=${timeFrame.value}`);
            if (!chartResponse.ok) { throw new Error('Chart data not found'); }
            const chartJson = await chartResponse.json();
            setChartData(chartJson);
        } catch (err) {
            console.warn(err.message); 
            setChartData(null);
        } finally {
            setChartLoading(false);
        }
    };

    const fetchNewsData = async (companyName) => {
        setNewsLoading(true);
        try {
            const query = encodeURIComponent(companyName);
            const newsResponse = await fetch(`http://127.0.0.1:5001/news?q=${query}`);
            if (!newsResponse.ok) { throw new Error('News data not found'); }
            const newsJson = await newsResponse.json();
            setNewsData(newsJson);
        } catch (err) {
            console.warn(err.message); 
            setNewsData(null);
        } finally {
            setNewsLoading(false);
        }
    };

    const handleSearch = async (e, tickerOverride = null) => {
        if (e && e.preventDefault) e.preventDefault();
        
        const searchTicker = tickerOverride || ticker;
        if (!searchTicker) return;

        setLoading(true);
        setStockData(null);
        setChartData(null);
        setNewsData(null); 
        setError('');

        const defaultTimeFrame = timeFrames.find(f => f.value === '6mo');
        setActiveTimeFrame(defaultTimeFrame);

        try {
            // Fetch the combined stock data
            const stockResponse = await fetch(`http://127.0.0.1:5001/stock/${searchTicker}`);
            if (!stockResponse.ok) {
                const errorData = await stockResponse.json();
                throw new Error(errorData.error || 'Stock data not found');
            }
            const stockJson = await stockResponse.json();
            setStockData(stockJson); 
            setSearchedTicker(searchTicker);
            addToSearchHistory(searchTicker); // Add to search history

            // Now fetch chart and news in parallel
            await Promise.all([
                fetchChartData(searchTicker, defaultTimeFrame),
                fetchNewsData(stockJson.companyName) // Pass company name to news
            ]);

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
                headers: {
                    'Content-Type': 'application/json',
                }
            });
            const result = await response.json();
            if (response.ok) {
                alert(result.message || `${tickerToAdd} added to watchlist!`);
            } else {
                alert(result.error || result.message || 'Failed to add to watchlist');
            }
        } catch (err) {
            console.error('Watchlist error:', err);
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

                {/* Search History */}
                {searchHistory.length > 0 && (
                    <div className="mt-6 text-left">
                        <h3 className="text-sm font-semibold text-gray-600 mb-3">Search History</h3>
                        <div className="flex flex-wrap gap-2">
                            {searchHistory.map((ticker) => (
                                <button
                                    key={ticker}
                                    onClick={() => {
                                        setTicker(ticker);
                                        setTimeout(() => {
                                            handleSearch({ preventDefault: () => {} }, ticker);
                                        }, 0);
                                    }}
                                    className="px-3 py-1 bg-gray-200 hover:bg-gray-300 text-gray-700 text-sm rounded-full transition-colors"
                                >
                                    {ticker}
                                </button>
                            ))}
                            <button
                                onClick={clearSearchHistory}
                                className="px-3 py-1 bg-red-100 hover:bg-red-200 text-red-700 text-sm rounded-full transition-colors"
                            >
                                Clear
                            </button>
                        </div>
                    </div>
                )}
            </div>
            
            {/* --- UPDATED: Main content area --- */}
            <div className="w-full max-w-4xl mt-4">
                {error && !loading && <div className="text-red-500 text-center p-4 bg-red-100 rounded-lg">{error}</div>}
                
                {stockData && (
                    <>
                        <StockDataCard data={stockData} onAddToWatchlist={handleAddToWatchlist} />
                        
                        {/* --- RENDER NEW & MODIFIED COMPONENTS --- */}
                        <StockOverviewCard 
                            summary={stockData.overview} 
                            financials={stockData.financials} 
                        />
                        <KeyMetricsCard metrics={stockData.keyMetrics} />
                        <AnalystRatingsCard 
                            ratings={stockData.analystRatings} 
                            price={stockData.price} 
                        />
                    </>
                )}
                
                {chartLoading && <div className="text-center p-8 text-gray-500">Loading chart...</div>}
                {chartData && !chartLoading && (
                    <StockChart
                        chartData={chartData}
                        ticker={searchedTicker}
                        onTimeFrameChange={handleTimeFrameChange}
                        activeTimeFrame={activeTimeFrame}
                    />
                )}

                {newsLoading && <div className="text-center p-8 text-gray-500">Loading news...</div>}
                {newsData && newsData.length > 0 && !newsLoading && (
                    <StockNewsCard newsData={newsData} />
                )}
            </div>
        </div>
    );
});

SearchPageComponent.displayName = 'SearchPage';
export default SearchPageComponent;