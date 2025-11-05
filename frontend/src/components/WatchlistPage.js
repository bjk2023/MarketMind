import React, { useState, useEffect } from 'react';

// A single row in the watchlist
const WatchlistRow = ({ stock, onRemove }) => {
    const isPositive = stock.change >= 0;
    return (
        <tr className="border-b border-gray-200 dark:border-gray-700 hover:bg-gray-50 dark:hover:bg-gray-700">
            <td className="py-3 px-4 font-bold text-gray-800 dark:text-gray-200">{stock.symbol}</td>
            <td className="py-3 px-4 text-gray-600 dark:text-gray-400">{stock.companyName}</td>
            <td className="py-3 px-4 font-medium dark:text-gray-200">${stock.price.toFixed(2)}</td>
            <td className={`py-3 px-4 font-medium ${isPositive ? 'text-green-500' : 'text-red-500'}`}>
                {isPositive ? '+' : ''}{stock.change.toFixed(2)} ({stock.changePercent.toFixed(2)}%)
            </td>
            <td className="py-3 px-4">
                <button
                    onClick={() => onRemove(stock.symbol)}
                    className="bg-red-500 hover:bg-red-600 text-white font-semibold py-1 px-3 rounded-md transition-colors"
                >
                    Remove
                </button>
            </td>
        </tr>
    );
};


const WatchlistPage = () => {
    const [watchlistData, setWatchlistData] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    // Function to fetch all data for the watchlist
    const fetchWatchlistData = async () => {
        setLoading(true);
        setError(null);
        try {
            // 1. Get the list of tickers from our /watchlist endpoint
            const response = await fetch('http://localhost:5001/watchlist');
            const tickers = await response.json();

            if (tickers.length === 0) {
                setWatchlistData([]);
                setLoading(false);
                return;
            }

            // 2. Fetch detailed data for each ticker in parallel
            const promises = tickers.map(ticker =>
                fetch(`http://localhost:5001/stock/${ticker}`).then(res => res.json())
            );
            const detailedData = await Promise.all(promises);

            // Filter out any results that returned an error
            setWatchlistData(detailedData.filter(data => !data.error));

        } catch (err) {
            setError('Failed to fetch watchlist data. Is the backend server running?');
        } finally {
            setLoading(false);
        }
    };

    // Function to handle removing a stock
    const handleRemoveStock = async (ticker) => {
        try {
            await fetch(`http://localhost:5001/watchlist/${ticker}`, {
                method: 'DELETE',
            });
            // Refresh the watchlist data after removing a stock
            fetchWatchlistData();
        } catch (err) {
            setError('Failed to remove stock.');
        }
    };

    // Fetch data when the component mounts
    useEffect(() => {
        fetchWatchlistData();
    }, []);

    if (loading) return <div className="text-center p-8 text-gray-600 dark:text-gray-400">Loading watchlist...</div>;
    if (error) return <div className="text-center p-8 text-red-500 dark:text-red-400">{error}</div>;

    return (
        <div className="container mx-auto p-4 md:p-8 animate-fade-in">
            <h1 className="text-3xl font-bold text-gray-800 dark:text-white mb-6">My Watchlist</h1>
            {watchlistData.length > 0 ? (
                <div className="bg-white dark:bg-gray-800 shadow-md rounded-lg overflow-x-auto">
                    <table className="min-w-full text-left text-sm">
                        <thead className="bg-gray-100 dark:bg-gray-700 border-b border-gray-300 dark:border-gray-600">
                            <tr>
                                <th className="py-3 px-4 font-semibold text-gray-600 dark:text-gray-300">Symbol</th>
                                <th className="py-3 px-4 font-semibold text-gray-600 dark:text-gray-300">Company</th>
                                <th className="py-3 px-4 font-semibold text-gray-600 dark:text-gray-300">Price</th>
                                <th className="py-3 px-4 font-semibold text-gray-600 dark:text-gray-300">Change</th>
                                <th className="py-3 px-4 font-semibold text-gray-600 dark:text-gray-300">Actions</th>
                            </tr>
                        </thead>
                        <tbody>
                            {watchlistData.map(stock => (
                                <WatchlistRow key={stock.symbol} stock={stock} onRemove={handleRemoveStock} />
                            ))}
                        </tbody>
                    </table>
                </div>
            ) : (
                <p className="text-center text-gray-500 dark:text-gray-400 mt-8">Your watchlist is empty. Add stocks from the Search page.</p>
            )}
        </div>
    );
};

export default WatchlistPage;