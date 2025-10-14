import React from 'react';
import { TrendingUpIcon, TrendingDownIcon } from '../Icons';

const StockDataCard = ({ data, onAddToWatchlist }) => {
    const isPositive = data.change >= 0;
    const changeColor = isPositive ? 'text-green-500' : 'text-red-500';

    const DataRow = ({ label, value }) => (
        <div className="flex justify-between py-3 border-b border-gray-200 last:border-b-0">
            <span className="text-sm text-gray-500">{label}</span>
            <span className="text-sm font-medium text-gray-800">{value}</span>
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
            <div className="mt-6 space-y-2">
                <DataRow label="Market Cap" value={data.marketCap} />
                <DataRow label="P/E Ratio" value={data.peRatio} />
                <DataRow label="52 Week High" value={`$${data.week52High.toFixed(2)}`} />
                <DataRow label="52 Week Low" value={`$${data.week52Low.toFixed(2)}`} />
            </div>
        </div>
    );
};

export default StockDataCard;