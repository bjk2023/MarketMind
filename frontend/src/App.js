import React, { useState } from 'react';
import Header from './components/Header';
import SearchPage from './components/SearchPage';
import GettingStartedPage from './components/GettingStartedPage';
// NEW: Import the WatchlistPage component
import WatchlistPage from './components/WatchlistPage';
import NewsPage from './components/NewsPage';


function App() {
    // NEW: Add 'watchlist' as a possible page state
    const [activePage, setActivePage] = useState('search');

    return (
        <div className="min-h-screen bg-gray-50 font-sans">
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
                {activePage === 'gettingStarted' && <GettingStartedPage />}
                {/* NEW: Render the WatchlistPage when active */}
                {activePage === 'watchlist' && <WatchlistPage />}
                {activePage === 'news' && <NewsPage />}
            </main>
        </div>
    );
}

export default App;