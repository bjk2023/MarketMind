import React, { useState, useEffect } from 'react';
import { Bell, Plus, Trash2, BellRing, X } from 'lucide-react';

// Reusable Notification Component for this page
const FormNotification = ({ message, onDismiss }) => {
    if (!message) return null;

    const baseStyle = "px-4 py-3 rounded-lg text-white font-semibold animate-fade-in text-center flex justify-between items-center";
    const successStyle = "bg-green-500";
    const errorStyle = "bg-red-500";

    return (
        <div className={`mt-4 ${baseStyle} ${message.type === 'success' ? successStyle : errorStyle}`}>
            <span>{message.text}</span>
            <button onClick={onDismiss} className="text-white hover:bg-black/10 p-1 rounded-full">
                <X size={18} />
            </button>
        </div>
    );
};

const NotificationsPage = ({ onClearAlerts }) => {
    const [activeAlerts, setActiveAlerts] = useState([]);
    const [triggeredAlerts, setTriggeredAlerts] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [message, setMessage] = useState(null);

    // Form state
    const [ticker, setTicker] = useState('');
    const [condition, setCondition] = useState('below');
    const [price, setPrice] = useState('');

    const fetchAllAlerts = async () => {
        setLoading(true);
        setError(null);
        try {
            // Fetch both active and triggered alerts
            const [activeRes, triggeredRes] = await Promise.all([
                fetch('http://127.0.0.1:5001/notifications'),
                fetch('http://127.0.0.1:5001/notifications/triggered?all=true') // Get all triggered
            ]);

            if (!activeRes.ok) throw new Error('Failed to fetch active alerts.');
            if (!triggeredRes.ok) throw new Error('Failed to fetch triggered alerts.');

            const activeData = await activeRes.json();
            const triggeredData = await triggeredRes.json();

            setActiveAlerts(activeData);
            setTriggeredAlerts(triggeredData);
        } catch (err) {
            setError(err.message);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchAllAlerts();
        // Optional: poll every 30 seconds to refresh triggered alerts
        const interval = setInterval(() => {
            // Only refresh triggered alerts (less frequent)
            fetch('http://127.0.0.1:5001/notifications/triggered?all=true')
                .then(res => res.json())
                .then(data => setTriggeredAlerts(data))
                .catch(() => {}); // Silent fail
        }, 30000);
        return () => clearInterval(interval);
    }, []);

    const handleSubmit = async (e) => {
        e.preventDefault();
        if (!ticker || !price) {
            setMessage({ type: 'error', text: 'Please fill in all fields.' });
            return;
        }

        try {
            const res = await fetch('http://127.0.0.1:5001/notifications', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    ticker: ticker.toUpperCase(),
                    condition,
                    target_price: parseFloat(price)
                })
            });

            if (!res.ok) {
                const errData = await res.json();
                throw new Error(errData.error || 'Failed to create alert.');
            }

            const newAlert = await res.json();
            setActiveAlerts(prev => [...prev, newAlert]);
            setMessage({ type: 'success', text: 'Alert created successfully!' });
            setTicker('');
            setPrice('');
            setTimeout(() => setMessage(null), 3000);
        } catch (err) {
            setMessage({ type: 'error', text: err.message });
            setTimeout(() => setMessage(null), 5000);
        }
    };

    const handleDeleteActive = async (alertId) => {
        try {
            const res = await fetch(`http://127.0.0.1:5001/notifications/${alertId}`, {
                method: 'DELETE'
            });
            if (!res.ok) throw new Error('Failed to delete alert.');
            setActiveAlerts(prev => prev.filter(a => a.id !== alertId));
        } catch (err) {
            setError(err.message);
        }
    };

    const handleDeleteTriggered = async (alertId) => {
        try {
            const res = await fetch(`http://127.0.0.1:5001/notifications/triggered/${alertId}`, {
                method: 'DELETE'
            });
            if (!res.ok) throw new Error('Failed to dismiss alert.');
            setTriggeredAlerts(prev => prev.filter(a => a.id !== alertId));
        } catch (err) {
            setError(err.message);
        }
    };

    const handleClearAllTriggered = async () => {
        try {
            const res = await fetch('http://127.0.0.1:5001/notifications/triggered', {
                method: 'DELETE'
            });
            if (!res.ok) throw new Error('Failed to clear alerts.');
            setTriggeredAlerts([]);
            if (onClearAlerts) onClearAlerts(); // Notify parent to clear badge
        } catch (err) {
            setError(err.message);
        }
    };

    return (
        <div className="min-h-screen bg-gray-50 dark:bg-gray-900 p-4">
            <div className="max-w-4xl mx-auto">
                <h1 className="text-3xl font-bold text-gray-800 dark:text-white mb-8 flex items-center">
                    <BellRing className="mr-2 text-blue-600" />
                    Price Alerts
                </h1>

                {/* Create Alert Form */}
                <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6 mb-8">
                    <h2 className="text-xl font-semibold text-gray-700 dark:text-gray-300 mb-4 flex items-center">
                        <Plus className="mr-2" />
                        Create New Alert
                    </h2>
                    <form onSubmit={handleSubmit} className="space-y-4">
                        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                            <div>
                                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                                    Stock Ticker
                                </label>
                                <input
                                    type="text"
                                    value={ticker}
                                    onChange={(e) => setTicker(e.target.value.toUpperCase())}
                                    placeholder="e.g., AAPL"
                                    className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent dark:bg-gray-700 dark:text-white"
                                    maxLength={5}
                                />
                            </div>
                            <div>
                                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                                    Condition
                                </label>
                                <select
                                    value={condition}
                                    onChange={(e) => setCondition(e.target.value)}
                                    className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent dark:bg-gray-700 dark:text-white"
                                >
                                    <option value="above">Above</option>
                                    <option value="below">Below</option>
                                </select>
                            </div>
                            <div>
                                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                                    Target Price ($)
                                </label>
                                <input
                                    type="number"
                                    step="0.01"
                                    value={price}
                                    onChange={(e) => setPrice(e.target.value)}
                                    placeholder="e.g., 150.00"
                                    className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent dark:bg-gray-700 dark:text-white"
                                />
                            </div>
                        </div>
                        <button
                            type="submit"
                            className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition-colors flex items-center"
                        >
                            <Plus className="mr-2" size={18} />
                            Create Alert
                        </button>
                    </form>
                    <FormNotification message={message} onDismiss={() => setMessage(null)} />
                </div>

                {/* Triggered Alerts */}
                {triggeredAlerts.length > 0 && (
                    <div className="bg-red-50 dark:bg-red-900/20 rounded-lg shadow-md p-6 mb-8">
                        <div className="flex justify-between items-center mb-4">
                            <h2 className="text-xl font-semibold text-red-700 dark:text-red-400 flex items-center">
                                <BellRing className="mr-2" />
                                Triggered Alerts ({triggeredAlerts.length})
                            </h2>
                            <button
                                onClick={handleClearAllTriggered}
                                className="text-sm bg-red-600 text-white px-3 py-1 rounded hover:bg-red-700 transition-colors"
                            >
                                Clear All
                            </button>
                        </div>
                        <div className="space-y-3">
                            {triggeredAlerts.map(alert => (
                                <div key={alert.id} className="bg-white dark:bg-gray-800 p-3 rounded border-l-4 border-red-500 flex justify-between items-center">
                                    <div>
                                        <p className="font-medium text-gray-800 dark:text-gray-200">{alert.message}</p>
                                        <p className="text-xs text-gray-500 dark:text-gray-400">
                                            {new Date(alert.timestamp).toLocaleString()}
                                        </p>
                                    </div>
                                    <button
                                        onClick={() => handleDeleteTriggered(alert.id)}
                                        className="text-red-600 hover:text-red-800 dark:text-red-400 dark:hover:text-red-300"
                                    >
                                        <Trash2 size={16} />
                                    </button>
                                </div>
                            ))}
                        </div>
                    </div>
                )}

                {/* Active Alerts */}
                <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6">
                    <h2 className="text-xl font-semibold text-gray-700 dark:text-gray-300 mb-4">
                        Active Alerts ({activeAlerts.length})
                    </h2>
                    {loading ? (
                        <p className="text-gray-500 dark:text-gray-400">Loading alerts...</p>
                    ) : error ? (
                        <p className="text-red-500">Error: {error}</p>
                    ) : activeAlerts.length === 0 ? (
                        <p className="text-gray-500 dark:text-gray-400">No active alerts.</p>
                    ) : (
                        <div className="space-y-3">
                            {activeAlerts.map(alert => (
                                <div key={alert.id} className="border border-gray-200 dark:border-gray-600 p-3 rounded flex justify-between items-center">
                                    <div>
                                        <span className="font-medium text-gray-800 dark:text-gray-200">
                                            {alert.ticker}
                                        </span>
                                        <span className="mx-2 text-gray-500 dark:text-gray-400">
                                            {alert.condition === 'above' ? '↑' : '↓'} ${alert.target_price}
                                        </span>
                                        <p className="text-xs text-gray-500 dark:text-gray-400">
                                            Created {new Date(alert.created_at).toLocaleString()}
                                        </p>
                                    </div>
                                    <button
                                        onClick={() => handleDeleteActive(alert.id)}
                                        className="text-red-600 hover:text-red-800 dark:text-red-400 dark:hover:text-red-300"
                                    >
                                        <Trash2 size={16} />
                                    </button>
                                </div>
                            ))}
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
};

export default NotificationsPage;
