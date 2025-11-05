import React, { useState } from 'react';
import Header from './components/Header';
import SearchPage from './components/SearchPage';
import PredictionsPage from './components/PredictionsPage';
import NewsPage from './components/NewsPage';
import GettingStartedPage from './components/GettingStartedPage';
// NEW: Import the WatchlistPage component
import WatchlistPage from './components/WatchlistPage';
import ModelPerformancePage from './components/ModelPerformancePage';
import ForexPage from './components/ForexPage';
import CryptoPage from './components/CryptoPage';


function App() {
    // NEW: Add 'watchlist' as a possible page state
    const [activePage, setActivePage] = useState('search');
    const [predictionTicker, setPredictionTicker] = useState('');

    const handleNavigateToPredictions = (ticker) => {
        setPredictionTicker(ticker);
        setActivePage('predictions');
    };

    return (
        <div className="min-h-screen bg-gray-50 dark:bg-gray-900 font-sans transition-colors duration-200">
            <style>{`
                @keyframes fade-in {
                    from { opacity: 0; transform: translateY(10px); }
                    to { opacity: 1; transform: translateY(0); }
                }
                .animate-fade-in { animation: fade-in 0.5s ease-out forwards; }
            `}</style>
            
            <Header activePage={activePage} setActivePage={setActivePage} />
            
            <main>
                {activePage === 'search' && <SearchPage onNavigateToPredictions={handleNavigateToPredictions} />}
                {activePage === 'predictions' && <PredictionsPage initialTicker={predictionTicker} />}
                {activePage === 'forex' && <ForexPage />}
                {activePage === 'crypto' && <CryptoPage />}
                {activePage === 'news' && <NewsPage />}
                {activePage === 'gettingStarted' && <GettingStartedPage />}
                {/* NEW: Render the WatchlistPage when active */}
                {activePage === 'watchlist' && <WatchlistPage />}
                {activePage === 'performance' && <ModelPerformancePage />}
            </main>
        </div>
    );
}

export default App;