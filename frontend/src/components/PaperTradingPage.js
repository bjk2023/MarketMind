import React, { useEffect, useState, useMemo } from 'react';
import { Chart } from 'react-chartjs-2';
import {
  Chart as ChartJS, CategoryScale, LinearScale, PointElement, LineElement, Title,
  Tooltip, Legend, TimeScale, Filler,
} from 'chart.js';
import { CandlestickController, CandlestickElement } from 'chartjs-chart-financial';
import 'chartjs-adapter-date-fns';

// Register all Chart.js components and controllers
ChartJS.register(
  CategoryScale, LinearScale, PointElement, LineElement, Title, Tooltip,
  Legend, TimeScale, Filler, CandlestickController, CandlestickElement
);

// --- Reusable Notification Component ---
const TradeNotification = ({ message }) => {
    if (!message) return null;
    const style = message.type === 'success' ? "bg-green-500" : "bg-red-500";
    return <div className={`mt-4 px-4 py-3 rounded-lg text-white font-semibold animate-fade-in text-center ${style}`}>{message.text}</div>;
};

// --- Reusable Time Frame Buttons ---
const timeFrames = [
    { label: '1D', value: '1d' }, { label: '5D', value: '5d' }, { label: '1M', value: '1mo' },
    { label: '6M', value: '6mo' }, { label: '1Y', value: '1y' },
];

// --- ADVANCED CHART COMPONENT (Integrated) ---
const StockChart = ({ chartData, ticker, onTimeFrameChange, activeTimeFrame }) => {
    const [chartType, setChartType] = useState('line');

    const chartConfig = useMemo(() => {
        if (!chartData || chartData.length === 0) return null;
        const chartComponentType = chartType === 'candlestick' ? 'candlestick' : 'line';
        const isUp = chartData[chartData.length - 1].close >= chartData[0].close;

        const data = {
            datasets: [
                chartType === 'line' ? {
                    type: 'line', label: 'Price',
                    data: chartData.map(d => ({ x: new Date(d.date), y: d.close })),
                    fill: 'start',
                    backgroundColor: (context) => {
                        const gradient = context.chart.ctx.createLinearGradient(0, 0, 0, 400);
                        gradient.addColorStop(0, isUp ? 'rgba(16, 185, 129, 0.4)' : 'rgba(239, 68, 68, 0.4)');
                        gradient.addColorStop(1, 'rgba(0, 0, 0, 0)');
                        return gradient;
                    },
                    segment: { borderColor: (ctx) => (ctx.p1.parsed.y >= ctx.p0.parsed.y ? '#10B981' : '#EF4444') },
                    borderWidth: 2,
                } : {
                    type: 'candlestick', label: `${ticker} OHLC`,
                    data: chartData.map(d => ({ x: new Date(d.date).valueOf(), o: d.open, h: d.high, l: d.low, c: d.close })),
                }
            ]
        };
        const options = {
            responsive: true, maintainAspectRatio: false,
            plugins: {
                legend: { display: false },
                title: { display: true, text: `${ticker} Price History (${activeTimeFrame.label})`, font: { size: 18 }, padding: { top: 10, bottom: 20 } },
            },
            scales: {
                x: { type: 'time', time: { unit: activeTimeFrame.value === '1d' ? 'hour' : 'day' }, grid: { display: false } },
                y: { grid: { color: 'rgba(200, 200, 200, 0.1)' } }
            },
            interaction: { intersect: false, mode: 'index' },
            elements: { point: { radius: 0 } }
        };
        return { type: chartComponentType, options, data };
    }, [chartData, chartType, ticker, activeTimeFrame]);

    if (!chartConfig) return null;

    return (
        <div className="mt-8 bg-white p-4 sm:p-6 rounded-xl shadow-lg animate-fade-in">
            <div className="flex flex-col sm:flex-row justify-between items-center mb-4 gap-4">
                <div className="flex items-center space-x-1 bg-gray-100 p-1 rounded-lg">
                    {timeFrames.map((frame) => (
                        <button key={frame.value} onClick={() => onTimeFrameChange(frame)} className={`px-3 py-1 text-sm font-semibold rounded-md transition-colors duration-200 ${ activeTimeFrame.value === frame.value ? 'bg-blue-600 text-white shadow' : 'text-gray-600 hover:bg-gray-200' }`}>{frame.label}</button>
                    ))}
                </div>
                <select value={chartType} onChange={(e) => setChartType(e.target.value)} className="p-2 border rounded-lg bg-gray-50 focus:ring-2 focus:ring-blue-500 outline-none text-sm">
                    <option value="line">Line Chart</option>
                    <option value="candlestick">Candlestick</option>
                </select>
            </div>
            <div className="h-96">
                <Chart type={chartConfig.type} options={chartConfig.options} data={chartConfig.data} />
            </div>
        </div>
    );
};

// --- Prediction Display Component ---
const PredictionDisplay = ({ prediction, loading, error }) => {
    if (loading) return <div className="text-center p-4 text-gray-500">Calculating prediction...</div>;
    if (error) return <div className="text-center p-4 text-red-500 bg-red-100 rounded-lg">{error}</div>;
    if (!prediction) return null;

    return (
        <div className="mt-6 bg-blue-50 p-4 rounded-xl shadow-md border border-blue-200">
            <h3 className="text-lg font-semibold text-blue-800">7-Day Price Prediction</h3>
            <p className="text-2xl font-bold text-blue-900 mt-2">
                {/* --- FIX: Added fallback to prevent crash --- */}
                ${(prediction.predicted_price || 0).toFixed(2)}
            </p>
            <p className="text-sm text-gray-500">for {prediction.prediction_for_date}</p>
        </div>
    );
};

// --- MAIN PAGE COMPONENT ---
function PaperTradingPage() {
  // --- FIX 1: Set a default "shape" for portfolio to prevent crashes ---
  const [portfolio, setPortfolio] = useState({
      account_value: 0,
      daily_gain_loss: 0,
      total_gain_loss: 0,
      cash: 0,
      positions: []
  });
  // --- FIX 2: Add a dedicated loading state ---
  const [isLoading, setIsLoading] = useState(true);

  const [ticker, setTicker] = useState('');
  const [shares, setShares] = useState('');
  const [tradeMessage, setTradeMessage] = useState(null);
  const [viewMode, setViewMode] = useState('total');

  // Chart and Prediction State
  const [selectedTicker, setSelectedTicker] = useState(null);
  const [activeTimeFrame, setActiveTimeFrame] = useState(timeFrames.find(f => f.value === '6mo'));
  const [chartData, setChartData] = useState(null);
  const [prediction, setPrediction] = useState(null);
  const [predictionLoading, setPredictionLoading] = useState(false);
  const [predictionError, setPredictionError] = useState('');


  const fetchPortfolio = () => {
    fetch('http://127.0.0.1:5001/paper/portfolio')
      .then(res => res.ok ? res.json() : Promise.reject("Failed to fetch portfolio"))
      .then(data => {
          setPortfolio(data);
          setIsLoading(false); // --- FIX 3: Set loading to false on success ---
      })
      .catch(err => {
          setTradeMessage({ type: 'error', text: 'Could not connect to the backend.' });
          setIsLoading(false); // --- FIX 4: Set loading to false on error ---
      });
  };

  const handleTrade = async (type) => {
    if (!ticker || !shares || parseInt(shares) <= 0) {
        setTradeMessage({ type: 'error', text: 'Please enter a valid ticker and positive shares.' });
        return;
    }
    try {
        const response = await fetch(`http://127.0.0.1:5001/paper/${type}`, {
            method: 'POST', headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ ticker, shares: parseInt(shares) })
        });
        const result = await response.json();
        if (!response.ok) throw new Error(result.error || 'Trade failed.');
        setTradeMessage({ type: 'success', text: result.message });
        setTicker(''); setShares('');
        fetchPortfolio();
    } catch (err) {
        setTradeMessage({ type: 'error', text: err.message });
    }
  };

  const fetchChartAndPrediction = async (symbol, timeFrame) => {
      setSelectedTicker(symbol);
      setActiveTimeFrame(timeFrame);
      setChartData(null); // Clear old data
      setPrediction(null);
      setPredictionError('');

      // Fetch Chart Data
      fetch(`http://127.0.0.1:5001/chart/${symbol}?period=${timeFrame.value}`)
        .then(res => res.json())
        .then(data => {
            if (data.error) throw new Error(data.error);
            setChartData(data);
        })
        .catch(err => setPredictionError('Could not load chart data.')); // Use predictionError for chart too

      // Fetch Prediction Data
      setPredictionLoading(true);
      fetch(`http://127.0.0.1:5001/predict/${symbol}`)
          .then(res => res.json())
          .then(data => {
              if (data.error) throw new Error(data.error);
              setPrediction(data);
          })
          .catch(err => setPredictionError(err.message))
          .finally(() => setPredictionLoading(false));
  };

  const handleTimeFrameChange = (timeFrame) => {
      if(selectedTicker) {
          fetchChartAndPrediction(selectedTicker, timeFrame);
      }
  };

  const handlePositionClick = (symbol) => {
      if (selectedTicker === symbol) {
          setSelectedTicker(null); // Toggle off
      } else {
          const defaultTimeFrame = timeFrames.find(f => f.value === '6mo');
          fetchChartAndPrediction(symbol, defaultTimeFrame);
      }
  };

  useEffect(() => {
    if (tradeMessage) {
        const timer = setTimeout(() => setTradeMessage(null), 5000);
        return () => clearTimeout(timer);
    }
  }, [tradeMessage]);

  useEffect(() => {
    fetchPortfolio();
    const interval = setInterval(fetchPortfolio, 30000);
    return () => clearInterval(interval);
  }, []);

  // --- FIX 5: Use the new isLoading state for the loading guard ---
  if (isLoading) return <div className="text-center mt-10">Loading Portfolio...</div>;

  const summaryData = [
    // --- FIX 6: Add fallbacks (|| 0) to ensure values are always numbers ---
    { label: 'Account Value', value: portfolio.account_value || 0 },
    { label: "Day's Gain/Loss", value: portfolio.daily_gain_loss || 0, color: (portfolio.daily_gain_loss || 0) >= 0 ? 'text-green-600' : 'text-red-600' },
    { label: 'Total Gain/Loss', value: portfolio.total_gain_loss || 0, color: (portfolio.total_gain_loss || 0) >= 0 ? 'text-green-600' : 'text-red-600' },
    { label: 'Cash', value: portfolio.cash || 0 },
  ];

  return (
    <div className="container mx-auto p-4 sm:p-6 lg:p-8 animate-fade-in">
      <h1 className="text-4xl font-bold mb-6 text-gray-800">Paper Trading</h1>
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
        {summaryData.map(item => (
            <div key={item.label} className="bg-white p-4 rounded-xl shadow-md">
                <h3 className="text-sm font-medium text-gray-500">{item.label}</h3>
                <p className={`text-2xl font-semibold ${item.color || 'text-gray-900'}`}>
                    {item.value.toLocaleString('en-US', { style: 'currency', currency: 'USD' })}
                </p>
            </div>
        ))}
      </div>
      <div className="mb-6 p-6 bg-white rounded-xl shadow-md">
        <h2 className="text-xl font-semibold mb-4 text-gray-700">Place a Trade</h2>
        <div className="flex flex-wrap gap-3 items-center">
          <input className="border p-3 rounded-lg flex-grow min-w-[120px] focus:ring-2 focus:ring-blue-500 outline-none" placeholder="Ticker" value={ticker} onChange={e => setTicker(e.target.value.toUpperCase())} />
          <input className="border p-3 rounded-lg w-32 focus:ring-2 focus:ring-blue-500 outline-none" type="number" placeholder="Shares" value={shares} onChange={e => setShares(e.target.value)} />
          <button className="bg-green-500 text-white px-6 py-3 rounded-lg font-semibold hover:bg-green-600 transition-colors" onClick={() => handleTrade('buy')}>Buy</button>
          <button className="bg-red-500 text-white px-6 py-3 rounded-lg font-semibold hover:bg-red-600 transition-colors" onClick={() => handleTrade('sell')}>Sell</button>
        </div>
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
            {/* --- FIX 7: Add (|| []) to safely map positions --- */}
            {(portfolio.positions || []).map(pos => (
                <tr key={pos.ticker} className="border-t hover:bg-gray-50 cursor-pointer" onClick={() => handlePositionClick(pos.ticker)}>
                    <td className="p-4 font-medium text-gray-900">{pos.ticker} <span className="block text-xs text-gray-500 font-normal">{pos.companyName}</span></td>
                    <td className="p-4 text-gray-600">{pos.shares}</td>
                    {/* --- FIX 8: Add fallbacks (|| 0) to prevent crashes --- */}
                    <td className="p-4 text-gray-600">${(pos.avg_cost || 0).toFixed(2)}</td>
                    <td className="p-4 font-medium text-gray-900">${(pos.current_price || 0).toFixed(2)}</td>
                    <td className={`p-4 font-semibold ${((viewMode === 'total' ? pos.total_pl : pos.daily_pl) || 0) >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                        ${((viewMode === 'total' ? pos.total_pl : pos.daily_pl) || 0).toFixed(2)}
                    </td>
                </tr>
            ))}
            </tbody>
        </table>
      </div>
      {selectedTicker && (
          <div>
              {chartData ? (
                  <StockChart chartData={chartData} ticker={selectedTicker} onTimeFrameChange={handleTimeFrameChange} activeTimeFrame={activeTimeFrame} />
              ) : (
                  <div className="text-center p-8 text-gray-500">Loading chart...</div>
              )}
              <PredictionDisplay prediction={prediction} loading={predictionLoading} error={predictionError} />
          </div>
      )}
    </div>
  );
}

export default PaperTradingPage;