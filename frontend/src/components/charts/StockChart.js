import React, { useState, useMemo } from 'react';
import { Line, Bar, Chart } from 'react-chartjs-2';

const StockChart = ({ chartData }) => {
    const [chartType, setChartType] = useState('line');

    const chartConfig = useMemo(() => {
        if (!chartData || chartData.length === 0) return null;
        const labels = chartData.map(d => d.date);
        const options = {
            responsive: true,
            plugins: { 
                legend: { position: 'top' }, 
                title: { display: true, text: 'Stock Price History', font: { size: 18 } }
            },
            scales: { 
                x: { type: 'time', time: { unit: 'day' }, ticks: { source: 'auto' } },
            },
        };

        let data;
        if (chartType === 'candlestick') {
            data = { datasets: [{ label: 'OHLC', data: chartData.map(d => ({ x: new Date(d.date).valueOf(), o: d.open, h: d.high, l: d.low, c: d.close })) }] };
        } else {
             data = { labels, datasets: [{ label: 'Closing Price', data: chartData.map(d => d.close), borderColor: 'rgb(53, 162, 235)', backgroundColor: 'rgba(53, 162, 235, 0.5)' }] };
        }
        return { type: chartType, options, data };
    }, [chartData, chartType]);

    if (!chartConfig) return null;

    return (
         <div className="mt-8 bg-white p-6 rounded-xl shadow-lg animate-fade-in">
            <div className="flex justify-end mb-4">
                <select value={chartType} onChange={(e) => setChartType(e.target.value)} className="p-2 border rounded-lg bg-gray-50 focus:ring-2 focus:ring-blue-500 outline-none">
                    <option value="line">Line Chart</option>
                    <option value="bar">Bar Chart</option>
                    <option value="candlestick">Candlestick Chart</option>
                </select>
            </div>
            {chartType === 'line' && <Line options={chartConfig.options} data={chartConfig.data} />}
            {chartType === 'bar' && <Bar options={chartConfig.options} data={chartConfig.data} />}
            {chartType === 'candlestick' && <Chart type='candlestick' options={chartConfig.options} data={chartConfig.data} />}
        </div>
    );
};

export default StockChart;