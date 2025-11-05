import React, { useState } from 'react';
import Header from './components/Header';
import SearchPage from './components/SearchPage';
import PredictionsPage from './components/PredictionsPage';
import NewsPage from './components/NewsPage';
import GettingStartedPage from './components/GettingStartedPage';
// NEW: Import the WatchlistPage component
import WatchlistPage from './components/WatchlistPage';


function App() {
    // NEW: Add 'watchlist' as a possible page state
    const [activePage, setActivePage] = useState('search');

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
                {activePage === 'search' && <SearchPage />}
                {activePage === 'predictions' && <PredictionsPage />}
                {activePage === 'news' && <NewsPage />}
                {activePage === 'gettingStarted' && <GettingStartedPage />}
                {/* NEW: Render the WatchlistPage when active */}
                {activePage === 'watchlist' && <WatchlistPage />}
            </main>
        </div>
    );
}

export default App;