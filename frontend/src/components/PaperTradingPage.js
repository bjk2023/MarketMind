import React, { useEffect, useState, useMemo } from 'react';
import { Line } from 'react-chartjs-2';
import {
  Chart as ChartJS, CategoryScale, LinearScale, PointElement,
  LineElement, Title, Tooltip, Legend, TimeScale, Filler
} from 'chart.js';
import 'chartjs-adapter-date-fns';

// Register Chart.js components
ChartJS.register(
  CategoryScale, LinearScale, PointElement, LineElement, Title, Tooltip, Legend, TimeScale, Filler
);

// Helper to format numbers as currency
const formatCurrency = (value) => {
  if (typeof value !== 'number') return '$0.00';
  return value.toLocaleString('en-US', { style: 'currency', currency: 'USD' });
};

// Helper to format gain/loss with color
const GainLoss = ({ value }) => {
  const isPositive = value >= 0;
  const color = isPositive ? 'text-green-600' : 'text-red-600';
  return (
    <span className={color}>
      {isPositive ? '+' : ''}{formatCurrency(value)}
    </span>
  );
};

// The pop-up chart component
const PositionChart = ({ ticker, onClose }) => {
    const [chartData, setChartData] = useState([]);

    useEffect(() => {
        if (ticker) {
            fetch(`http://127.0.0.1:5001/chart/${ticker}?period=6mo`)
              .then(res => res.json())
              .then(data => {
                  if (Array.isArray(data)) {
                      setChartData(data);
                  }
              });
        }
    }, [ticker]);

    const chartConfig = useMemo(() => {
        if (!chartData.length) return null;
        const labels = chartData.map(d => new Date(d.date));
        const dataPoints = chartData.map(d => d.close);
        const firstPrice = dataPoints[0];
        const lastPrice = dataPoints[dataPoints.length - 1];
        const isUp = lastPrice >= firstPrice;

        return {
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: { legend: { display: false } },
                scales: { x: { type: 'time', time: { unit: 'day' }, grid: { display: false } }, y: { grid: { color: 'rgba(200, 200, 200, 0.1)' } } },
                elements: { point: { radius: 0 } },
                interaction: { intersect: false, mode: 'index' },
            },
            data: {
                labels,
                datasets: [{
                    label: 'Price',
                    data: dataPoints,
                    borderWidth: 2,
                    borderColor: isUp ? '#10B981' : '#EF4444',
                    backgroundColor: (context) => {
                        const ctx = context.chart.ctx;
                        const gradient = ctx.createLinearGradient(0, 0, 0, 200);
                        gradient.addColorStop(0, isUp ? 'rgba(16, 185, 129, 0.4)' : 'rgba(239, 68, 68, 0.4)');
                        gradient.addColorStop(1, 'rgba(0, 0, 0, 0)');
                        return gradient;
                    },
                    fill: 'start',
                }]
            }
        };
    }, [chartData]);

    return (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50" onClick={onClose}>
            <div className="bg-white rounded-xl shadow-2xl p-6 w-full max-w-2xl" onClick={e => e.stopPropagation()}>
                <div className="flex justify-between items-center mb-4">
                    <h2 className="text-2xl font-bold">{ticker} - 6 Month History</h2>
                    <button onClick={onClose} className="text-gray-500 hover:text-gray-800 text-2xl">&times;</button>
                </div>
                <div className="h-64">
                    {chartConfig ? <Line options={chartConfig.options} data={chartConfig.data} /> : 'Loading chart...'}
                </div>
            </div>
        </div>
    );
};


function PaperTradingPage() {
  const [portfolio, setPortfolio] = useState(null);
  const [ticker, setTicker] = useState('');
  const [shares, setShares] = useState('');
  const [message, setMessage] = useState('');
  const [error, setError] = useState('');
  const [selectedTicker, setSelectedTicker] = useState(null);

  const fetchPortfolio = () => {
    fetch('http://127.0.0.1:5001/paper/portfolio')
      .then(res => res.json())
      .then(setPortfolio)
      .catch(() => setError("Failed to fetch portfolio. Is the server running?"));
  };

  const handleTrade = (type) => {
    setMessage('');
    setError('');
    const endpoint = type === 'buy' ? '/paper/buy' : '/paper/sell';
    fetch(`http://127.0.0.1:5001${endpoint}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ ticker, shares: parseInt(shares) })
    })
    .then(res => res.json())
    .then(data => {
      if (data.error) {
        setError(data.error);
      } else {
        setMessage(data.message);
        setTicker('');
        setShares('');
        fetchPortfolio();
      }
    });
  };

  useEffect(() => {
    fetchPortfolio();
  }, []);

  if (!portfolio) return <div className="text-center mt-10 text-gray-500">Loading Portfolio...</div>;

  return (
    <div className="p-4 md:p-8 font-sans">
      <h1 className="text-4xl font-bold mb-6 text-gray-800">Paper Trading Portfolio</h1>

      {/* Portfolio Summary Card */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        <div className="bg-white p-6 rounded-xl shadow-lg">
            <h3 className="text-sm font-medium text-gray-500">Account Value</h3>
            <p className="text-3xl font-bold text-gray-800 mt-2">{formatCurrency(portfolio.account_value)}</p>
        </div>
        <div className="bg-white p-6 rounded-xl shadow-lg">
            <h3 className="text-sm font-medium text-gray-500">Day's Gain/Loss</h3>
            <p className="text-3xl font-bold mt-2"><GainLoss value={portfolio.daily_gain_loss} /></p>
        </div>
        <div className="bg-white p-6 rounded-xl shadow-lg">
            <h3 className="text-sm font-medium text-gray-500">Total Gain/Loss</h3>
            <p className="text-3xl font-bold mt-2"><GainLoss value={portfolio.total_gain_loss} /></p>
        </div>
        <div className="bg-white p-6 rounded-xl shadow-lg">
            <h3 className="text-sm font-medium text-gray-500">Cash</h3>
            <p className="text-3xl font-bold text-gray-800 mt-2">{formatCurrency(portfolio.cash)}</p>
        </div>
      </div>

      {/* Trading Form */}
      <div className="mb-8 p-6 bg-white rounded-xl shadow-lg">
        <h2 className="text-2xl font-semibold mb-4 text-gray-700">Make a Trade</h2>
        <div className="flex flex-wrap items-center gap-4">
          <input
            className="border p-3 rounded-lg flex-grow min-w-[150px] focus:ring-2 focus:ring-blue-500 outline-none"
            placeholder="Ticker (e.g., AAPL)"
            value={ticker}
            onChange={e => setTicker(e.target.value.toUpperCase())}
          />
          <input
            className="border p-3 rounded-lg flex-grow min-w-[100px] focus:ring-2 focus:ring-blue-500 outline-none"
            type="number"
            placeholder="Shares"
            value={shares}
            onChange={e => setShares(e.target.value)}
          />
          <button className="bg-green-600 text-white font-bold px-6 py-3 rounded-lg hover:bg-green-700 transition-colors" onClick={() => handleTrade('buy')}>Buy</button>
          <button className="bg-red-600 text-white font-bold px-6 py-3 rounded-lg hover:bg-red-700 transition-colors" onClick={() => handleTrade('sell')}>Sell</button>
        </div>
        {message && <p className="text-green-600 mt-3">{message}</p>}
        {error && <p className="text-red-600 mt-3">{error}</p>}
      </div>

      {/* Positions Table */}
       <div className="bg-white shadow-lg rounded-xl overflow-x-auto">
         <table className="w-full">
            <thead className="bg-gray-50">
                <tr>
                    <th className="p-4 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">Position</th>
                    <th className="p-4 text-right text-xs font-semibold text-gray-500 uppercase tracking-wider">Shares</th>
                    <th className="p-4 text-right text-xs font-semibold text-gray-500 uppercase tracking-wider">Avg Cost</th>
                    <th className="p-4 text-right text-xs font-semibold text-gray-500 uppercase tracking-wider">Current Value</th>
                    <th className="p-4 text-right text-xs font-semibold text-gray-500 uppercase tracking-wider">Daily P/L</th>
                    <th className="p-4 text-right text-xs font-semibold text-gray-500 uppercase tracking-wider">Total P/L</th>
                </tr>
            </thead>
            <tbody className="divide-y divide-gray-200">
                {portfolio.positions.map(pos => (
                    <tr key={pos.ticker} className="hover:bg-gray-50 cursor-pointer" onClick={() => setSelectedTicker(pos.ticker)}>
                        <td className="p-4">
                            <div className="font-bold text-gray-800">{pos.ticker}</div>
                            <div className="text-xs text-gray-500">{pos.companyName}</div>
                        </td>
                        <td className="p-4 text-right">{pos.shares}</td>
                        <td className="p-4 text-right">{formatCurrency(pos.avg_cost)}</td>
                        <td className="p-4 text-right font-medium">{formatCurrency(pos.current_value)}</td>
                        <td className="p-4 text-right"><GainLoss value={pos.daily_pl} /></td>
                        <td className="p-4 text-right"><GainLoss value={pos.total_pl} /></td>
                    </tr>
                ))}
            </tbody>
         </table>
       </div>
       {portfolio.positions.length === 0 && <p className="text-center text-gray-500 mt-8">You have no open positions.</p>}

      {selectedTicker && <PositionChart ticker={selectedTicker} onClose={() => setSelectedTicker(null)} />}
    </div>
  );
}

export default PaperTradingPage;
