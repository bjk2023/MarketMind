import React, { useState, useEffect, useMemo, useCallback } from 'react';
import { Sparklines, SparklinesLine, SparklinesReferenceLine } from 'react-sparklines';
import { StockChart } from './SearchPage'; // Import from SearchPage

// --- Helper Functions & Components ---

// --- NEW: Helper to format numbers and return 'N/A' ---
const formatNum = (num, isPercent = false) => {
    if (num === null || num === undefined || isNaN(num)) return 'N/A';
    const val = Number(num);
    if (isPercent) return `${val.toFixed(2)}%`;
    return val.toFixed(2);
};

// Creates a visual bar for the 52-week range
const FiftyTwoWeekRange = ({ low, high, price }) => {
    if (!low || !high || !price) return <span>N/A</span>;
    const percent = ((price - low) / (high - low)) * 100;
    return (
        <div className="w-full h-2 bg-gray-200 rounded-full relative" title={`Low: $${low} | High: $${high}`}>
            <div 
                className="h-2 bg-blue-500 rounded-full absolute"
                style={{ left: `${percent}%` }}
            >
                {/* This is the dot */}
                <div className="w-2 h-2 bg-blue-700 rounded-full absolute -top-0 -right-1"></div>
            </div>
        </div>
    );
};

// Creates a colored pill for the analyst rating
const RatingPill = ({ rating }) => {
    if (!rating) return <span className="text-gray-400">N/A</span>;
    let color = "bg-gray-200 text-gray-800";
    if (rating.includes("buy")) color = "bg-green-100 text-green-800";
    if (rating.includes("sell")) color = "bg-red-100 text-red-800";
    if (rating.includes("hold")) color = "bg-yellow-100 text-yellow-800";

    return (
        <span className={`px-2 py-0.5 rounded-full text-xs font-semibold capitalize ${color}`}>
            {rating}
        </span>
    );
};

// Creates a small sparkline chart
const SparklineChart = ({ data, change }) => {
    if (!data || data.length === 0) return <div className="h-10 w-24"></div>;
    const color = change >= 0 ? '#10B981' : '#EF4444';
    return (
        <div className="h-10 w-24">
            <Sparklines data={data}>
                <SparklinesLine color={color} style={{ strokeWidth: 2 }} />
                <SparklinesReferenceLine type="avg" style={{ stroke: 'rgba(0,0,0,0.1)', strokeDasharray: '2, 2' }} />
            </Sparklines>
        </div>
    );
};

// A single row in the watchlist
const WatchlistRow = ({ stock, onRemove, onRowClick }) => {
    const isPositive = stock.change >= 0;
    
    const pe = stock.peRatio || 'N/A';
    const mktCap = stock.marketCap || 'N/A';
    const rating = stock.analystRatings?.recommendationKey;
    
    // --- NEW: Calculate Upside ---
    const targetPrice = stock.analystRatings?.targetMeanPrice;
    let upsidePercent = 'N/A';
    let upsideColor = 'text-gray-600';
    if (targetPrice && stock.price) {
        const upside = ((targetPrice - stock.price) / stock.price) * 100;
        upsidePercent = formatNum(upside, true);
        upsideColor = upside >= 0 ? 'text-green-600' : 'text-red-600';
    }
    
    return (
        <tr className="border-b border-gray-200 hover:bg-gray-50 cursor-pointer" onClick={() => onRowClick(stock.symbol)}>
            <td className="py-3 px-4">
                <div className="font-bold text-gray-900">{stock.symbol}</div>
                <div className="text-xs text-gray-500 truncate w-40">{stock.companyName}</div>
            </td>
            <td className="py-3 px-4 font-medium">${formatNum(stock.price)}</td>
            <td className={`py-3 px-4 font-medium ${isPositive ? 'text-green-600' : 'text-red-600'}`}>
                {isPositive ? '+' : ''}{formatNum(stock.change)} ({formatNum(stock.changePercent)}%)
            </td>
            <td className="py-3 px-4 text-gray-600">{mktCap}</td>
            <td className="py-3 px-4 text-gray-600">{pe === 'N/A' ? 'N/A' : formatNum(pe)}</td>
            <td className="py-3 px-4 w-40">
                <FiftyTwoWeekRange low={stock.week52Low} high={stock.week52High} price={stock.price} />
            </td>
            <td className="py-3 px-4">
                <SparklineChart data={stock.sparkline} change={stock.change} />
            </td>
            <td className="py-3 px-4">
                <RatingPill rating={rating} />
            </td>
            {/* --- NEW: Price Target and Upside Cells --- */}
            <td className="py-3 px-4 font-medium text-gray-900">
                ${formatNum(targetPrice)}
            </td>
            <td className={`py-3 px-4 font-semibold ${upsideColor}`}>
                {upsidePercent}
            </td>
            {/* --- End of New Cells --- */}
            <td className="py-3 px-4">
                <button
                    onClick={(e) => {
                        e.stopPropagation();
                        onRemove(stock.symbol);
                    }}
                    className="bg-red-500 hover:bg-red-600 text-white font-semibold py-1 px-3 rounded-md transition-colors"
                >
                    Remove
                </button>
            </td>
        </tr>
    );
};


// --- Main Watchlist Page Component ---
const WatchlistPage = () => {
    const [watchlistData, setWatchlistData] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [sortConfig, setSortConfig] = useState({ key: 'symbol', direction: 'ascending' });

    const [selectedTicker, setSelectedTicker] = useState(null);
    const [chartData, setChartData] = useState(null);
    const [chartError, setChartError] = useState(null);
    const [activeTimeFrame, setActiveTimeFrame] = useState({ label: '6M', value: '6mo' });

    const fetchWatchlistData = useCallback(async () => {
        setError(null);
        try {
            const response = await fetch('http://127.0.0.1:5001/watchlist');
            const tickers = await response.json();
            if (tickers.length === 0) {
                setWatchlistData([]);
                setLoading(false);
                return;
            }
            const promises = tickers.map(ticker =>
                fetch(`http://127.0.0.1:5001/stock/${ticker}`).then(res => res.json())
            );
            const detailedData = await Promise.all(promises);
            setWatchlistData(detailedData.filter(data => !data.error));
        } catch (err) {
            setError('Failed to fetch watchlist data. Is the backend server running?');
        } finally {
            setLoading(false);
        }
    }, []);

    const handleRemoveStock = async (ticker) => {
        try {
            await fetch(`http://127.0.0.1:5001/watchlist/${ticker}`, { method: 'DELETE' });
            setWatchlistData(prevData => prevData.filter(stock => stock.symbol !== ticker));
        } catch (err) {
            setError('Failed to remove stock.');
        }
    };

    const fetchChartData = async (symbol, timeFrame) => {
        setChartData(null);
        setChartError(null);
        try {
            const chartResponse = await fetch(`http://127.0.0.1:5001/chart/${symbol}?period=${timeFrame.value}`);
            if (!chartResponse.ok) throw new Error('Chart data not found');
            const chartJson = await chartResponse.json();
            setChartData(chartJson);
        } catch (err) {
            setChartError(err.message);
        }
    };

    const handleRowClick = (symbol) => {
        if (selectedTicker === symbol) {
            setSelectedTicker(null);
            setChartData(null);
        } else {
            setSelectedTicker(symbol);
            const defaultTimeFrame = { label: '6M', value: '6mo' };
            setActiveTimeFrame(defaultTimeFrame);
            fetchChartData(symbol, defaultTimeFrame);
        }
    };

    const handleTimeFrameChange = (timeFrame) => {
        setActiveTimeFrame(timeFrame);
        if (selectedTicker) {
            fetchChartData(selectedTicker, timeFrame);
        }
    };

    useEffect(() => {
        setLoading(true); 
        fetchWatchlistData(); 
        const refreshInterval = setInterval(fetchWatchlistData, 60000); 
        return () => clearInterval(refreshInterval); 
    }, [fetchWatchlistData]);

    const sortedWatchlistData = useMemo(() => {
        let sortableData = [...watchlistData];
        if (sortConfig.key) {
            sortableData.sort((a, b) => {
                let aValue, bValue;
                
                // --- NEW: Add sorting logic for targetPrice and upside ---
                if (sortConfig.key === 'targetPrice') {
                    aValue = a.analystRatings?.targetMeanPrice || 0;
                    bValue = b.analystRatings?.targetMeanPrice || 0;
                } else if (sortConfig.key === 'upside') {
                    aValue = ((a.analystRatings?.targetMeanPrice - a.price) / a.price) || -Infinity;
                    bValue = ((b.analystRatings?.targetMeanPrice - b.price) / b.price) || -Infinity;
                } else if (sortConfig.key === 'peRatio') {
                    aValue = a.peRatio || 0;
                    bValue = b.peRatio || 0;
                } else if (sortConfig.key === 'marketCap') {
                    const parseCap = (cap) => {
                        if (typeof cap !== 'string') return 0;
                        if (cap.endsWith('T')) return parseFloat(cap) * 1e12;
                        if (cap.endsWith('B')) return parseFloat(cap) * 1e9;
                        return 0;
                    }
                    aValue = parseCap(a.marketCap);
                    bValue = parseCap(b.marketCap);
                } else {
                    aValue = a[sortConfig.key];
                    bValue = b[sortConfig.key];
                }

                if (aValue < bValue) return sortConfig.direction === 'ascending' ? -1 : 1;
                if (aValue > bValue) return sortConfig.direction === 'ascending' ? 1 : -1;
                return 0;
            });
        }
        return sortableData;
    }, [watchlistData, sortConfig]);

    const requestSort = (key) => {
        let direction = 'ascending';
        if (sortConfig.key === key && sortConfig.direction === 'ascending') {
            direction = 'descending';
        }
        setSortConfig({ key, direction });
    };

    if (loading) return <div className="text-center p-8">Loading watchlist...</div>;
    if (error) return <div className="text-center p-8 text-red-500">{error}</div>;

    const SortableTh = ({ label, sortKey }) => {
        const isSorted = sortConfig.key === sortKey;
        const arrow = isSorted ? (sortConfig.direction === 'ascending' ? '▲' : '▼') : '';
        return (
            <th 
                className="py-3 px-4 font-semibold text-gray-600 cursor-pointer hover:bg-gray-200"
                onClick={() => requestSort(sortKey)}
            >
                {label} {arrow}
            </th>
        );
    };

    return (
        <div className="container mx-auto p-4 md:p-8 animate-fade-in">
            <h1 className="text-3xl font-bold text-gray-800 mb-6">My Watchlist</h1>
            {sortedWatchlistData.length > 0 ? (
                <div className="bg-white shadow-md rounded-lg overflow-x-auto">
                    <table className="min-w-full text-left text-sm">
                        <thead className="bg-gray-100 border-b border-gray-300">
                            <tr>
                                <SortableTh label="Symbol" sortKey="symbol" />
                                <SortableTh label="Price" sortKey="price" />
                                <SortableTh label="Change" sortKey="change" />
                                <SortableTh label="Market Cap" sortKey="marketCap" />
                                <SortableTh label="P/E (TTM)" sortKey="peRatio" />
                                <th className="py-3 px-4 font-semibold text-gray-600">52-Week Range</th>
                                <th className="py-3 px-4 font-semibold text-gray-600">7-Day Trend</th>
                                <th className="py-3 px-4 font-semibold text-gray-600">Rating</th>
                                {/* --- NEW: Table Headers --- */}
                                <SortableTh label="Price Target" sortKey="targetPrice" />
                                <SortableTh label="Upside" sortKey="upside" />
                                {/* --- End of New Headers --- */}
                                <th className="py-3 px-4 font-semibold text-gray-600">Actions</th>
                            </tr>
                        </thead>
                        <tbody>
                            {sortedWatchlistData.map(stock => (
                                <WatchlistRow 
                                    key={stock.symbol} 
                                    stock={stock} 
                                    onRemove={handleRemoveStock}
                                    onRowClick={handleRowClick} 
                                />
                            ))}
                        </tbody>
                    </table>
                </div>
            ) : (
                <p className="text-center text-gray-500 mt-8">Your watchlist is empty. Add stocks from the Search page.</p>
            )}

            {selectedTicker && (
                <div className="mt-8">
                    {chartData && (
                        <StockChart
                            chartData={chartData}
                            ticker={selectedTicker}
                            onTimeFrameChange={handleTimeFrameChange}
                            activeTimeFrame={activeTimeFrame}
                        />
                    )}
                    {chartError && <div className="text-center p-8 text-red-500">{chartError}</div>}
                </div>
            )}
        </div>
    );
};

export default WatchlistPage;
