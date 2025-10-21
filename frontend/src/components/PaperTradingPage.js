import React, { useEffect, useState } from 'react';
import { Line } from 'react-chartjs-2';
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
} from 'chart.js';
import 'chartjs-adapter-date-fns';

// Register Chart.js components
ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  TimeScale
);

// --- NEW: A dedicated component for trade notifications ---
const TradeNotification = ({ message }) => {
    if (!message) return null;

    const baseStyle = "px-4 py-3 rounded-lg text-white font-semibold animate-fade-in text-center";
    const successStyle = "bg-green-500";
    const errorStyle = "bg-red-500";

    return (
        <div className={`mt-4 ${baseStyle} ${message.type === 'success' ? successStyle : errorStyle}`}>
            {message.text}
        </div>
    );
};


function PaperTradingPage() {
  const [portfolio, setPortfolio] = useState(null);
  const [ticker, setTicker] = useState('');
  const [shares, setShares] = useState('');
  const [tradeMessage, setTradeMessage] = useState(null); // State for success/error messages
  const [viewMode, setViewMode] = useState('total');
  const [selectedTicker, setSelectedTicker] = useState(null);
  const [chartData, setChartData] = useState(null);

  const fetchPortfolio = () => {
    fetch('http://127.0.0.1:5001/paper/portfolio')
      .then(res => {
        if (!res.ok) throw new Error("Failed to fetch portfolio");
        return res.json();
      })
      .then(setPortfolio)
      .catch(err => {
          setTradeMessage({ type: 'error', text: 'Could not connect to the backend server.' });
      });
  };

  // --- UPDATED: The handleTrade function now handles errors ---
  const handleTrade = async (type) => {
    if (!ticker || !shares || parseInt(shares) <= 0) {
        setTradeMessage({ type: 'error', text: 'Please enter a valid ticker and a positive number of shares.' });
        return;
    }

    const endpoint = type === 'buy' ? '/paper/buy' : '/paper/sell';

    try {
        const response = await fetch(`http://127.0.0.1:5001${endpoint}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ ticker, shares: parseInt(shares) })
        });

        const result = await response.json();

        if (!response.ok) {
            // If the server returns an error (like 400 or 404), display it
            throw new Error(result.error || 'An unknown error occurred.');
        }

        // On success, show the success message from the backend
        setTradeMessage({ type: 'success', text: result.message });
        setTicker('');
        setShares('');
        fetchPortfolio(); // Refresh portfolio data

    } catch (err) {
        // This catches both network errors and backend error messages
        setTradeMessage({ type: 'error', text: err.message });
    }
  };

  const fetchChart = (symbol) => {
    if (selectedTicker === symbol) {
      setSelectedTicker(null); // Allow toggling the chart off
      setChartData(null);
      return;
    }
    setSelectedTicker(symbol);
    fetch(`http://127.0.0.1:5001/chart/${symbol}?period=6mo`)
      .then(res => res.json())
      .then(data => {
          const formattedData = {
              labels: data.map(d => new Date(d.date)),
              datasets: [{
                  label: 'Price',
                  data: data.map(d => d.close),
                  borderColor: '#3B82F6',
                  backgroundColor: 'rgba(59, 130, 246, 0.1)',
                  fill: true,
                  tension: 0.1,
                  pointRadius: 0
              }]
          };
          setChartData(formattedData);
      });
  };

  // --- NEW: useEffect to clear messages after a few seconds ---
  useEffect(() => {
    if (tradeMessage) {
        const timer = setTimeout(() => {
            setTradeMessage(null);
        }, 5000); // Message disappears after 5 seconds
        return () => clearTimeout(timer);
    }
  }, [tradeMessage]);

  useEffect(() => {
    fetchPortfolio();
    const interval = setInterval(fetchPortfolio, 30000); // Auto-refresh portfolio every 30 seconds
    return () => clearInterval(interval);
  }, []);

  if (!portfolio) return <div className="text-center mt-10">Loading...</div>;

  const summaryData = [
    { label: 'Account Value', value: portfolio.account_value, color: 'text-gray-900', isLarge: true },
    { label: "Day's Gain/Loss", value: portfolio.daily_gain_loss, color: portfolio.daily_gain_loss >= 0 ? 'text-green-600' : 'text-red-600' },
    { label: 'Total Gain/Loss', value: portfolio.total_gain_loss, color: portfolio.total_gain_loss >= 0 ? 'text-green-600' : 'text-red-600' },
    { label: 'Cash', value: portfolio.cash, color: 'text-gray-700' },
  ];

  return (
    <div className="container mx-auto p-4 sm:p-6 lg:p-8 animate-fade-in">
      <h1 className="text-4xl font-bold mb-6 text-gray-800">Paper Trading</h1>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
        {summaryData.map(item => (
            <div key={item.label} className={`bg-white p-4 rounded-xl shadow-md ${item.isLarge ? 'lg:col-span-1' : ''}`}>
                <h3 className="text-sm font-medium text-gray-500">{item.label}</h3>
                <p className={`text-2xl font-semibold ${item.color} ${item.isLarge ? 'text-3xl' : ''}`}>
                    {item.value.toLocaleString('en-US', { style: 'currency', currency: 'USD' })}
                </p>
            </div>
        ))}
      </div>

      <div className="mb-6 p-6 bg-white rounded-xl shadow-md">
        <h2 className="text-xl font-semibold mb-4 text-gray-700">Place a Trade</h2>
        <div className="flex flex-wrap gap-3 items-center">
          <input
            className="border p-3 rounded-lg flex-grow min-w-[120px] focus:ring-2 focus:ring-blue-500 outline-none"
            placeholder="Ticker (e.g. AAPL)"
            value={ticker}
            onChange={e => setTicker(e.target.value.toUpperCase())}
          />
          <input
            className="border p-3 rounded-lg w-32 focus:ring-2 focus:ring-blue-500 outline-none"
            type="number"
            placeholder="Shares"
            value={shares}
            onChange={e => setShares(e.target.value)}
          />
          <button className="bg-green-500 text-white px-6 py-3 rounded-lg font-semibold hover:bg-green-600 transition-colors" onClick={() => handleTrade('buy')}>Buy</button>
          <button className="bg-red-500 text-white px-6 py-3 rounded-lg font-semibold hover:bg-red-600 transition-colors" onClick={() => handleTrade('sell')}>Sell</button>
        </div>
        {/* --- The notification message will appear here --- */}
        <TradeNotification message={tradeMessage} />
      </div>

      <div className="flex justify-between items-center mb-4">
        <h2 className="text-2xl font-bold text-gray-800">My Positions</h2>
        <div className="bg-gray-100 p-1 rounded-lg">
            <button onClick={() => setViewMode('daily')} className={`px-3 py-1 rounded-md text-sm ${viewMode === 'daily' ? 'bg-blue-500 text-white shadow' : 'text-gray-600'}`}>Daily P/L</button>
            <button onClick={() => setViewMode('total')} className={`px-3 py-1 rounded-md text-sm ${viewMode === 'total' ? 'bg-blue-500 text-white shadow' : 'text-gray-600'}`}>Total P/L</button>
        </div>
      </div>

      <div className="overflow-x-auto bg-white shadow-md rounded-lg">
        <table className="w-full text-left">
            <thead className="bg-gray-50 border-b border-gray-200">
                <tr>
                    <th className="p-4 font-semibold text-gray-600">Ticker</th>
                    <th className="p-4 font-semibold text-gray-600">Shares</th>
                    <th className="p-4 font-semibold text-gray-600">Avg Cost</th>
                    <th className="p-4 font-semibold text-gray-600">Current Price</th>
                    <th className="p-4 font-semibold text-gray-600">P/L</th>
                </tr>
            </thead>
            <tbody>
            {portfolio.positions.map(pos => (
                <tr key={pos.ticker} className="border-t hover:bg-gray-50 cursor-pointer" onClick={() => fetchChart(pos.ticker)}>
                    <td className="p-4 font-medium text-gray-900">{pos.ticker}</td>
                    <td className="p-4 text-gray-600">{pos.shares}</td>
                    <td className="p-4 text-gray-600">${pos.avg_cost.toFixed(2)}</td>
                    <td className="p-4 font-medium text-gray-900">${pos.current_price.toFixed(2)}</td>
                    <td className={`p-4 font-semibold ${(viewMode === 'total' ? pos.total_pl : pos.daily_pl) >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                        ${(viewMode === 'total' ? pos.total_pl : pos.daily_pl).toFixed(2)}
                    </td>
                </tr>
            ))}
            </tbody>
        </table>
      </div>

      {selectedTicker && chartData && (
        <div className="mt-8 p-6 bg-white rounded-xl shadow-lg">
          <h2 className="text-xl font-bold mb-4">Chart: {selectedTicker}</h2>
          <div className="h-64">
             <Line data={chartData} options={{ maintainAspectRatio: false, responsive: true }} />
          </div>
        </div>
      )}
    </div>
  );
}

export default PaperTradingPage;

