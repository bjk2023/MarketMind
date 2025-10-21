import React from 'react';
import { TrendingUpIcon, TrendingDownIcon } from '../Icons';

const StockPredictionCard = ({ data }) => {
    const spe = Math.abs((data.predictedClose - data.lastActualClose) / data.lastActualClose) * 100;
    const isAccurate = spe <= 1;
    const changeColor = isAccurate ? 'text-green-500' : 'text-red-500';

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
                    <h2 className="text-2xl font-bold text-gray-900">
                        {data.companyName} ({data.symbol})
                    </h2>
                </div>
                <div className="text-right">
                    <div className={`flex items-center justify-end text-lg font-semibold ${changeColor}`}>
                        <span>Prediction Percentage Error: {spe.toFixed(2)}%</span>
                    </div>
                </div>
            </div>
            <div className="mt-6 space-y-2">
                <DataRow label="Predicted Close" value={`$${data.predictedClose.toFixed(2)}`} />
                <DataRow label="Actual Close" value={`$${data.lastActualClose.toFixed(2)}`} />
                <DataRow label="Date" value={data.todayDate} />
            </div>
        </div>
    );
};

export default StockPredictionCard;