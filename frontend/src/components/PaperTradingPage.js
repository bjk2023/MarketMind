import React, { useState, useEffect } from 'react';
import { Briefcase, TrendingUp, RefreshCw, RotateCcw, BarChart3 } from 'lucide-react';
// --- NEW: Import the TradeModal from OptionsPage ---
import { TradeModal } from './OptionsPage';

// --- NEW: Helper to safely format numbers ---
const formatCurrency = (val) => {
    if (val === null || val === undefined || isNaN(val)) return '$0.00';
    return val.toLocaleString('en-US', { style: 'currency', currency: 'USD' });
};
const formatNum = (val) => {
    if (val === null || val === undefined || isNaN(val)) return '0.00';
    return val.toFixed(2);
}

const PaperTradingPage = () => {
    const [portfolio, setPortfolio] = useState(null);
    const [stockPositions, setStockPositions] = useState([]); // Use this for just stock positions
    const [optionsPositions, setOptionsPositions] = useState([]); 
    
    const [tradeHistory, setTradeHistory] = useState([]);
    const [loading, setLoading] = useState(true);
    const [showBuyModal, setShowBuyModal] = useState(false);
    const [showSellModal, setShowSellModal] = useState(false);
    const [selectedStock, setSelectedStock] = useState(null);
    const [buyTicker, setBuyTicker] = useState('');
    const [buyShares, setBuyShares] = useState('');
    const [sellShares, setSellShares] = useState('');
    const [tradeMessage, setTradeMessage] = useState({ type: '', text: '' });

    // --- NEW: State for the Option Sell Modal ---
    const [isOptionModalOpen, setIsOptionModalOpen] = useState(false);
    const [selectedOption, setSelectedOption] = useState(null);

    const fetchPortfolio = async () => {
        try {
            const response = await fetch('http://127.0.0.1:5001/paper/portfolio');
            const data = await response.json();
            setPortfolio(data);
            setStockPositions(data.positions || []);
            setOptionsPositions(data.options_positions || []); 
        } catch (err) {
            console.error('Error fetching portfolio:', err);
        } finally {
            setLoading(false);
        }
    };

    const fetchTradeHistory = async () => {
        try {
            const response = await fetch('http://localhost:5001/paper/history');
            const data = await response.json();
            setTradeHistory(data.trades || []);
        } catch (err) {
            console.error('Error fetching trade history:', err);
        }
    };

    useEffect(() => {
        setLoading(true); // Set loading on initial fetch
        fetchPortfolio();
        fetchTradeHistory();
        const interval = setInterval(() => {
            fetchPortfolio();
        }, 30000);
        return () => clearInterval(interval);
    }, []);

    const handleBuy = async (e) => {
        e.preventDefault();
        setTradeMessage({ type: '', text: '' });
        
        try {
            const response = await fetch('http://localhost:5001/paper/buy', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ ticker: buyTicker.toUpperCase(), shares: parseFloat(buyShares) })
            });
            
            const data = await response.json();
            
            if (response.ok) {
                setTradeMessage({ type: 'success', text: data.message });
                setBuyTicker('');
                setBuyShares('');
                setShowBuyModal(false);
                fetchPortfolio();
                fetchTradeHistory();
            } else {
                setTradeMessage({ type: 'error', text: data.error });
            }
        } catch (err) {
            setTradeMessage({ type: 'error', text: 'Failed to execute trade' });
        }
    };

    const handleSell = async (e) => {
        e.preventDefault();
        setTradeMessage({ type: '', text: '' });
        
        try {
            const response = await fetch('http://localhost:5001/paper/sell', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ ticker: selectedStock.ticker, shares: parseFloat(sellShares) })
            });
            
            const data = await response.json();
            
            if (response.ok) {
                setTradeMessage({ type: 'success', text: data.message });
                setSellShares('');
                setShowSellModal(false);
                setSelectedStock(null);
                fetchPortfolio();
                fetchTradeHistory();
            } else {
                setTradeMessage({ type: 'error', text: data.error });
            }
        } catch (err) {
            setTradeMessage({ type: 'error', text: 'Failed to execute trade' });
        }
    };

    // --- NEW: Function to handle selling an option from the modal ---
    const handleConfirmOptionSell = async (contractSymbol, quantity, price, isBuy) => {
        if (isBuy) return false; // We only sell from this page

        const body = JSON.stringify({
            contractSymbol: contractSymbol,
            quantity: quantity,
            price: price
        });
        
        try {
            const response = await fetch(`http://localhost:5001/paper/options/sell`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: body
            });
            const data = await response.json();
            if (!response.ok) {
                throw new Error(data.error || 'Trade failed');
            }
            setTradeMessage({ type: 'success', text: data.message });
            fetchPortfolio(); // Refresh portfolio
            fetchTradeHistory(); // Refresh history
            return true;
        } catch (err) {
            setTradeMessage({ type: 'error', text: err.message });
            return false;
        }
    };

    // --- NEW: Function to open the sell modal ---
    const handleManageOption = (optionPosition) => {
        // We need to create a "contract" object for the modal
        const contract = {
            contractSymbol: optionPosition.ticker,
            bid: optionPosition.current_price, // Sell at the 'bid' (current price)
            ask: optionPosition.current_price, // Ask isn't needed for sell
        };
        setSelectedOption(contract);
        setIsOptionModalOpen(true);
    };

    const handleReset = async () => {
        if (!window.confirm('Are you sure you want to reset your portfolio? This will delete all positions and trade history.')) {
            return;
        }
        
        try {
            const response = await fetch('http://localhost:5001/paper/reset', {
                method: 'POST'
            });
            const data = await response.json();
            setTradeMessage({ type: 'success', text: data.message });
            fetchPortfolio();
            fetchTradeHistory();
        } catch (err) {
            setTradeMessage({ type: 'error', text: 'Failed to reset portfolio' });
        }
    };

    if (loading) {
        return (
            <div className="container mx-auto px-6 py-8">
                <div className="text-center py-12">
                    <div className="inline-block animate-spin rounded-full h-12 w-12 border-4 border-green-600 border-t-transparent"></div>
                    <p className="mt-4 text-gray-600 dark:text-gray-400">Loading portfolio...</p>
                </div>
            </div>
        );
    }

    return (
        <>
            {/* --- NEW: Add the Option Sell Modal to the page --- */}
            {isOptionModalOpen && (
                <TradeModal
                    contract={selectedOption}
                    tradeType="Sell" // Hardcode to "Sell"
                    stockPrice={null} // Not needed for selling
                    onClose={() => setIsOptionModalOpen(false)}
                    onConfirmTrade={handleConfirmOptionSell}
                />
            )}

            <div className="container mx-auto px-6 py-8 max-w-7xl">
                {/* Header */}
                <div className="text-center mb-8 animate-fade-in">
                    <div className="flex items-center justify-center mb-2">
                        <Briefcase className="w-10 h-10 text-green-600 dark:text-green-400 mr-3" />
                        <h1 className="text-4xl font-bold text-gray-900 dark:text-white">
                            Paper Trading Portfolio
                        </h1>
                    </div>
                    <p className="text-gray-600 dark:text-gray-400">
                        Practice trading with virtual money - No risk, real market prices
                    </p>
                </div>

                {/* Trade Message */}
                {tradeMessage.text && (
                    <div className={`mb-6 p-4 rounded-lg animate-fade-in ${
                        tradeMessage.type === 'success' 
                            ? 'bg-green-50 dark:bg-green-900/30 border border-green-200 dark:border-green-800 text-green-700 dark:text-green-300'
                            : 'bg-red-50 dark:bg-red-900/30 border border-red-200 dark:border-red-800 text-red-700 dark:text-red-300'
                    }`}>
                        {tradeMessage.text}
                    </div>
                )}

                {/* --- MODIFIED: Portfolio Summary --- */}
                <div className="grid grid-cols-1 md:grid-cols-5 gap-6 mb-8 animate-fade-in">
                    <div className="bg-gradient-to-br from-green-50 to-emerald-50 dark:from-green-900/30 dark:to-emerald-900/30 rounded-xl p-6 border border-green-100 dark:border-green-800">
                        <p className="text-sm text-gray-600 dark:text-gray-400 mb-1">Total Value</p>
                        <p className="text-3xl font-bold text-gray-900 dark:text-white">
                            {formatCurrency(portfolio?.total_value)}
                        </p>
                        <p className={`text-sm mt-2 font-semibold ${
                            (portfolio?.total_pl || 0) >= 0 ? 'text-green-600 dark:text-green-400' : 'text-red-600 dark:text-red-400'
                        }`}>
                            {(portfolio?.total_pl || 0) >= 0 ? '+' : ''}{formatCurrency(portfolio?.total_pl)} 
                            ({(portfolio?.total_return || 0) >= 0 ? '+' : ''}{formatNum(portfolio?.total_return)}%)
                        </p>
                    </div>

                    <div className="bg-white dark:bg-gray-800 rounded-xl p-6 border border-gray-200 dark:border-gray-700">
                        <p className="text-sm text-gray-600 dark:text-gray-400 mb-1">Cash</p>
                        <p className="text-2xl font-bold text-gray-900 dark:text-white">
                            {formatCurrency(portfolio?.cash)}
                        </p>
                    </div>

                    <div className="bg-white dark:bg-gray-800 rounded-xl p-6 border border-gray-200 dark:border-gray-700">
                        <p className="text-sm text-gray-600 dark:text-gray-400 mb-1">Stock Value</p>
                        <p className="text-2xl font-bold text-gray-900 dark:text-white">
                            {formatCurrency(portfolio?.positions_value)}
                        </p>
                    </div>

                    {/* --- NEW: Options Value Card --- */}
                    <div className="bg-white dark:bg-gray-800 rounded-xl p-6 border border-gray-200 dark:border-gray-700">
                        <p className="text-sm text-gray-600 dark:text-gray-400 mb-1">Options Value</p>
                        <p className="text-2xl font-bold text-gray-900 dark:text-white">
                            {formatCurrency(portfolio?.options_value)}
                        </p>
                    </div>

                    <div className="bg-white dark:bg-gray-800 rounded-xl p-6 border border-gray-200 dark:border-gray-700">
                        <p className="text-sm text-gray-600 dark:text-gray-400 mb-1">Total Positions</p>
                        <p className="text-2xl font-bold text-gray-900 dark:text-white">
                            {(portfolio?.positions?.length || 0) + (optionsPositions?.length || 0)}
                        </p>
                    </div>
                </div>
                {/* --- END OF MODIFIED SUMMARY --- */}


                {/* Action Buttons */}
                <div className="flex gap-4 mb-8">
                    <button
                        onClick={() => setShowBuyModal(true)}
                        className="px-6 py-3 bg-green-600 hover:bg-green-700 text-white rounded-lg font-semibold transition-all active:scale-95 flex items-center space-x-2"
                    >
                        <TrendingUp className="w-5 h-5" />
                        <span>Buy Stock</span>
                    </button>
                    <button
                        onClick={fetchPortfolio}
                        className="px-6 py-3 bg-blue-600 hover:bg-blue-700 text-white rounded-lg font-semibold transition-all active:scale-95 flex items-center space-x-2"
                    >
                        <RefreshCw className="w-5 h-5" />
                        <span>Refresh</span>
                    </button>
                    <button
                        onClick={handleReset}
                        className="px-6 py-3 bg-red-600 hover:bg-red-700 text-white rounded-lg font-semibold transition-all active:scale-95 ml-auto flex items-center space-x-2"
                    >
                        <RotateCcw className="w-5 h-5" />
                        <span>Reset Portfolio</span>
                    </button>
                </div>

                {/* Stock Positions */}
                <div className="bg-white dark:bg-gray-800 rounded-xl shadow-lg p-6 mb-8 animate-fade-in">
                    <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-6">Stock Positions</h2>
                    
                    {(!portfolio?.positions || portfolio.positions.length === 0) ? (
                        <div className="text-center py-12">
                            <BarChart3 className="w-16 h-16 mx-auto mb-4 text-gray-400" />
                            <p className="text-gray-600 dark:text-gray-400 text-lg">No stock positions yet</p>
                            <p className="text-gray-500 dark:text-gray-500 text-sm mt-2">Click "Buy Stock" to start trading</p>
                        </div>
                    ) : (
                        <div className="grid grid-cols-1 gap-4">
                            {portfolio?.positions?.map((position) => (
                                <div key={position.ticker} className="border border-gray-200 dark:border-gray-700 rounded-lg p-4 hover:shadow-md transition-all">
                                    <div className="flex items-center justify-between">
                                        <div className="flex-1">
                                            <h3 className="text-xl font-bold text-gray-900 dark:text-white">{position.ticker}</h3>
                                            <p className="text-sm text-gray-600 dark:text-gray-400">{position.company_name}</p>
                                        </div>
                                        
                                        <div className="grid grid-cols-5 gap-6 flex-1 text-center">
                                            <div>
                                                <p className="text-xs text-gray-500 dark:text-gray-400">Shares</p>
                                                <p className="font-semibold text-gray-900 dark:text-white">{position.shares}</p>
                                            </div>
                                            <div>
                                                <p className="text-xs text-gray-500 dark:text-gray-400">Avg Cost</p>
                                                <p className="font-semibold text-gray-900 dark:text-white">{formatCurrency(position.avg_cost)}</p>
                                            </div>
                                            <div>
                                                <p className="text-xs text-gray-500 dark:text-gray-400">Current</p>
                                                <p className="font-semibold text-gray-900 dark:text-white">{formatCurrency(position.current_price)}</p>
                                            </div>
                                            <div>
                                                <p className="text-xs text-gray-500 dark:text-gray-400">Value</p>
                                                <p className="font-semibold text-gray-900 dark:text-white">{formatCurrency(position.current_value)}</p>
                                            </div>
                                            <div>
                                                <p className="text-xs text-gray-500 dark:text-gray-400">P/L</p>
                                                <p className={`font-semibold ${
                                                    position.total_pl >= 0 ? 'text-green-600 dark:text-green-400' : 'text-red-600 dark:text-red-400'
                                                }`}>
                                                    {position.total_pl >= 0 ? '+' : ''}{formatCurrency(position.total_pl)}
                                                    <span className="text-xs ml-1">({position.total_pl_percent >= 0 ? '+' : ''}{formatNum(position.total_pl_percent)}%)</span>
                                                </p>
                                            </div>
                                        </div>
                                        
                                        <button
                                            onClick={() => {
                                                setSelectedStock(position);
                                                setShowSellModal(true);
                                            }}
                                            className="ml-4 px-4 py-2 bg-red-600 hover:bg-red-700 text-white rounded-lg font-semibold transition-all"
                                        >
                                            Sell
                                        </button>
                                    </div>
                                </div>
                            ))}
                        </div>
                    )}
                </div>
                
                {/* --- MODIFIED: Options Positions Table --- */}
                <div className="bg-white dark:bg-gray-800 rounded-xl shadow-lg p-6 mb-8 animate-fade-in">
                    <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-6">Options Positions</h2>
                    {optionsPositions.length === 0 ? (
                        <div className="text-center py-12">
                            <BarChart3 className="w-16 h-16 mx-auto mb-4 text-gray-400" />
                            <p className="text-gray-600 dark:text-gray-400 text-lg">No options positions yet</p>
                            <p className="text-gray-500 dark:text-gray-500 text-sm mt-2">Go to the "Options" page to trade contracts</p>
                        </div>
                    ) : (
                        <div className="grid grid-cols-1 gap-4">
                            {optionsPositions.map((pos) => (
                                <div key={pos.ticker} className="border border-gray-200 dark:border-gray-700 rounded-lg p-4">
                                    <div className="flex items-center justify-between">
                                        <div className="flex-1">
                                            <h3 className="text-lg font-bold text-gray-900 dark:text-white">{pos.ticker}</h3>
                                            <p className="text-xs text-gray-600 dark:text-gray-400 max-w-xs truncate">{pos.company_name}</p>
                                        </div>
                                        <div className="grid grid-cols-5 gap-6 flex-1 text-center">
                                            <div><p className="text-xs text-gray-500 dark:text-gray-400">Qty</p><p className="font-semibold text-gray-900 dark:text-white">{pos.shares}</p></div>
                                            <div><p className="text-xs text-gray-500 dark:text-gray-400">Avg Premium</p><p className="font-semibold text-gray-900 dark:text-white">${formatNum(pos.avg_cost)}</p></div>
                                            <div><p className="text-xs text-gray-500 dark:text-gray-400">Current</p><p className="font-semibold text-gray-900 dark:text-white">${formatNum(pos.current_price)}</p></div>
                                            <div><p className="text-xs text-gray-500 dark:text-gray-400">Value</p><p className="font-semibold text-gray-900 dark:text-white">{formatCurrency(pos.current_value)}</p></div>
                                            <div><p className="text-xs text-gray-500 dark:text-gray-400">Total P/L</p><p className={`font-semibold ${pos.total_pl >= 0 ? 'text-green-600' : 'text-red-600'}`}>{formatCurrency(pos.total_pl)}</p></div>
                                        </div>
                                        {/* --- MODIFIED: This button now works --- */}
                                        <button
                                            onClick={() => handleManageOption(pos)}
                                            className="ml-4 px-4 py-2 bg-red-600 hover:bg-red-700 text-white rounded-lg font-semibold transition-all"
                                        >
                                            Sell
                                        </button>
                                    </div>
                                </div>
                            ))}
                        </div>
                    )}
                </div>
                {/* --- END OF NEW TABLE --- */}


                {/* Trade History */}
                <div className="bg-white dark:bg-gray-800 rounded-xl shadow-lg p-6 animate-fade-in">
                    <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-6">Trade History</h2>
                    
                    {tradeHistory.length === 0 ? (
                        <div className="text-center py-8">
                            <p className="text-gray-600 dark:text-gray-400">No trades yet</p>
                        </div>
                    ) : (
                        <div className="overflow-x-auto">
                            <table className="w-full">
                                <thead>
                                    <tr className="border-b-2 border-gray-200 dark:border-gray-700">
                                        <th className="text-left py-3 px-4 text-gray-700 dark:text-gray-300 font-semibold">Date</th>
                                        <th className="text-left py-3 px-4 text-gray-700 dark:text-gray-300 font-semibold">Type</th>
                                        <th className="text-left py-3 px-4 text-gray-700 dark:text-gray-300 font-semibold">Ticker/Contract</th>
                                        <th className="text-right py-3 px-4 text-gray-700 dark:text-gray-300 font-semibold">Qty/Shares</th>
                                        <th className="text-right py-3 px-4 text-gray-700 dark:text-gray-300 font-semibold">Price</th>
                                        <th className="text-right py-3 px-4 text-gray-700 dark:text-gray-300 font-semibold">Total</th>
                                        <th className="text-right py-3 px-4 text-gray-700 dark:text-gray-300 font-semibold">Profit</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {tradeHistory.slice().reverse().map((trade, index) => (
                                        <tr key={index} className="border-b border-gray-200 dark:border-gray-700">
                                            <td className="py-3 px-4 text-sm text-gray-600 dark:text-gray-400">
                                                {new Date(trade.timestamp).toLocaleString()}
                                            </td>
                                            <td className="py-3 px-4">
                                                {/* --- MODIFIED: Handle new trade types --- */}
                                                <span className={`px-2 py-1 rounded text-xs font-semibold ${
                                                    trade.type.includes('BUY') 
                                                        ? 'bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-400'
                                                        : 'bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-400'
                                                }`}>
                                                    {trade.type}
                                                </span>
                                            </td>
                                            <td className="py-3 px-4 font-semibold text-gray-900 dark:text-white text-xs">{trade.ticker}</td>
                                            <td className="py-3 px-4 text-right text-gray-900 dark:text-white">{trade.shares}</td>
                                            <td className="py-3 px-4 text-right text-gray-900 dark:text-white">${formatNum(trade.price)}</td>
                                            <td className="py-3 px-4 text-right text-gray-900 dark:text-white">${formatNum(trade.total)}</td>
                                            <td className={`py-3 px-4 text-right font-semibold ${
                                                (trade.profit || 0) >= 0 ? 'text-green-600 dark:text-green-400' : 'text-red-600 dark:text-red-400'
                                            }`}>
                                                {trade.profit ? formatCurrency(trade.profit) : '-'}
                                            </td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        </div>
                    )}
                </div>

                {/* Buy Modal */}
                {showBuyModal && (
                    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50" onClick={() => setShowBuyModal(false)}>
                        <div className="bg-white dark:bg-gray-800 rounded-xl p-8 max-w-md w-full mx-4" onClick={(e) => e.stopPropagation()}>
                            <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-6">Buy Stock</h2>
                            <form onSubmit={handleBuy}>
                                <div className="mb-4">
                                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                                        Ticker Symbol
                                    </label>
                                    <input
                                        type="text"
                                        value={buyTicker}
                                        onChange={(e) => setBuyTicker(e.target.value.toUpperCase())}
                                        className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 dark:bg-gray-700 dark:text-white rounded-lg focus:ring-2 focus:ring-green-500 outline-none"
                                        placeholder="AAPL"
                                        required
                                    />
                                </div>
                                <div className="mb-6">
                                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                                        Number of Shares
                                    </label>
                                    <input
                                        type="number"
                                        value={buyShares}
                                        onChange={(e) => setBuyShares(e.target.value)}
                                        className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 dark:bg-gray-700 dark:text-white rounded-lg focus:ring-2 focus:ring-green-500 outline-none"
                                        placeholder="10"
                                        min="0.01"
                                        step="0.01"
                                        required
                                    />
                                </div>
                                <div className="flex gap-4">
                                    <button
                                        type="submit"
                                        className="flex-1 px-6 py-3 bg-green-600 hover:bg-green-700 text-white rounded-lg font-semibold transition-all"
                                    >
                                        Buy
                                    </button>
                                    <button
                                        type="button"
                                        onClick={() => setShowBuyModal(false)}
                                        className="flex-1 px-6 py-3 bg-gray-600 hover:bg-gray-700 text-white rounded-lg font-semibold transition-all"
                                    >
                                        Cancel
                                    </button>
                                </div>
                            </form>
                        </div>
                    </div>
                )}

                {/* Sell Modal */}
                {showSellModal && selectedStock && (
                    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50" onClick={() => setShowSellModal(false)}>
                        <div className="bg-white dark:bg-gray-800 rounded-xl p-8 max-w-md w-full mx-4" onClick={(e) => e.stopPropagation()}>
                            <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-2">Sell {selectedStock.ticker}</h2>
                            <p className="text-gray-600 dark:text-gray-400 mb-6">
                                You have {selectedStock.shares} shares available
                            </p>
                            <form onSubmit={handleSell}>
                                <div className="mb-6">
                                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                                        Number of Shares
                                    </label>
                                    <input
                                        type="number"
                                        value={sellShares}
                                        onChange={(e) => setSellShares(e.target.value)}
                                        className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 dark:bg-gray-700 dark:text-white rounded-lg focus:ring-2 focus:ring-red-500 outline-none"
                                        placeholder={`Max: ${selectedStock.shares}`}
                                        min="0.01"
                                        max={selectedStock.shares}
                                        step="0.01"
                                        required
                                    />
                                </div>
                                <div className="flex gap-4">
                                    <button
                                        type="submit"
                                        className="flex-1 px-6 py-3 bg-red-600 hover:bg-red-700 text-white rounded-lg font-semibold transition-all"
                                    >
                                        Sell
                                    </button>
                                    <button
                                        type="button"
                                        onClick={() => {
                                            setShowSellModal(false);
                                            setSelectedStock(null);
                                        }}
                                        className="flex-1 px-6 py-3 bg-gray-600 hover:bg-gray-700 text-white rounded-lg font-semibold transition-all"
                                    >
                                        Cancel
                                    </button>
                                </div>
                            </form>
                        </div>
                    </div>
                )}
            </div>
        </>
    );
};

export default PaperTradingPage;