import React, { useEffect, useState } from 'react';

function PaperTradingPage() {
  const [portfolio, setPortfolio] = useState(null);
  const [ticker, setTicker] = useState('');
  const [shares, setShares] = useState('');
  const [viewMode, setViewMode] = useState('total'); // 'total' or 'daily'
  const [selectedTicker, setSelectedTicker] = useState(null);
  const [chartData, setChartData] = useState([]);

  const fetchPortfolio = () => {
    fetch('http://127.0.0.1:5001/paper/portfolio')
      .then(res => res.json())
      .then(setPortfolio);
  };

  const handleTrade = (type) => {
    if (!ticker || !shares || isNaN(Number(shares))) {
      alert("Enter a valid ticker and number of shares");
      return;
    }
    const endpoint = type === 'buy' ? '/paper/buy' : '/paper/sell';
    fetch(`http://127.0.0.1:5001${endpoint}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ ticker, shares: parseInt(shares) })
    })
    .then(res => res.json())
    .then(() => {
      setTicker('');
      setShares('');
      fetchPortfolio();
    });
  };

  const fetchChart = (symbol) => {
    setSelectedTicker(symbol);
    fetch(`http://127.0.0.1:5001/chart/${symbol}?period=6mo`)
      .then(res => res.json())
      .then(setChartData);
  };

  useEffect(() => {
    fetchPortfolio();
  }, []);

  if (!portfolio) return <div className="text-center mt-10">Loading...</div>;

  return (
    <div className="p-6">
      <h1 className="text-3xl font-bold mb-6">Paper Trading</h1>
      <p className="mb-4 text-gray-600">Starting balance: $100,000</p>
      <div className="mb-6 p-4 bg-gray-100 rounded-lg">
        <h2 className="text-xl font-semibold mb-2">Cash: ${portfolio.cash.toFixed(2)}</h2>
        <div className="flex gap-2 mt-3">
          <input
            className="border p-2 rounded"
            placeholder="Ticker (e.g. AAPL)"
            value={ticker}
            onChange={e => setTicker(e.target.value.toUpperCase())}
          />
          <input
            className="border p-2 rounded"
            type="number"
            placeholder="Shares"
            value={shares}
            onChange={e => setShares(e.target.value)}
          />
          <button className="bg-green-500 text-white px-4 py-2 rounded" onClick={() => handleTrade('buy')}>Buy</button>
          <button className="bg-red-500 text-white px-4 py-2 rounded" onClick={() => handleTrade('sell')}>Sell</button>
        </div>
      </div>

      <div className="mb-4">
        <button
          onClick={() => setViewMode('daily')}
          className={`px-4 py-2 mr-2 rounded ${viewMode === 'daily' ? 'bg-blue-500 text-white' : 'bg-gray-200'}`}
        >
          Daily P/L
        </button>
        <button
          onClick={() => setViewMode('total')}
          className={`px-4 py-2 rounded ${viewMode === 'total' ? 'bg-blue-500 text-white' : 'bg-gray-200'}`}
        >
          Total P/L
        </button>
      </div>

      <table className="w-full border-collapse bg-white shadow rounded-lg">
        <thead>
          <tr className="bg-gray-100 text-gray-700">
            <th className="p-2">Ticker</th>
            <th className="p-2">Shares</th>
            <th className="p-2">Avg Cost</th>
            <th className="p-2">Current</th>
            <th className="p-2">P/L</th>
          </tr>
        </thead>
        <tbody>
          {portfolio.positions.map(pos => (
            <tr key={pos.ticker} className="border-t hover:bg-gray-50 cursor-pointer" onClick={() => fetchChart(pos.ticker)}>
              <td className="p-2">{pos.ticker}</td>
              <td className="p-2">{pos.shares}</td>
              <td className="p-2">${pos.avg_cost.toFixed(2)}</td>
              <td className="p-2">${pos.current_price.toFixed(2)}</td>
              <td className={`p-2 ${ (viewMode === 'total' ? pos.total_pl : pos.daily_pl) >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                ${(viewMode === 'total' ? pos.total_pl : pos.daily_pl).toFixed(2)}
              </td>
            </tr>
          ))}
        </tbody>
      </table>

      {selectedTicker && chartData.length > 0 && (
        <div className="mt-8 p-4 bg-white rounded-lg shadow">
          <h2 className="text-xl font-bold mb-2">Chart: {selectedTicker}</h2>
          <div className="overflow-x-auto">
            <svg width="100%" height="200">
              {chartData.map((point, i) => {
                if (i === 0) return null;
                const x1 = (i - 1) * 3;
                const x2 = i * 3;
                const y1 = 200 - (chartData[i - 1].close / Math.max(...chartData.map(p => p.close))) * 200;
                const y2 = 200 - (point.close / Math.max(...chartData.map(p => p.close))) * 200;
                return <line key={i} x1={x1} y1={y1} x2={x2} y2={y2} stroke="blue" strokeWidth="1" />;
              })}
            </svg>
          </div>
        </div>
      )}
    </div>
  );
}

export default PaperTradingPage;
