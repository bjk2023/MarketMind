import React, { useState, useRef } from 'react';
import Header from './components/Header';
import SearchPage from './components/SearchPage';
import GettingStartedPage from './components/GettingStartedPage';
import WatchlistPage from './components/WatchlistPage';
import PaperTradingPage from './components/PaperTradingPage';

function App() {
    const [activePage, setActivePage] = useState('search');
    const searchPageRef = useRef(null);

    const handleHeaderSearch = (ticker) => {
        setActivePage('search');
        // Give the page a moment to render, then trigger search
        setTimeout(() => {
            if (searchPageRef.current) {
                searchPageRef.current.performSearch(ticker);
            }
        }, 100);
    };

    return (
        <div className="min-h-screen bg-gray-50 font-sans">
            <style>{`
                @keyframes fade-in {
                    from { opacity: 0; transform: translateY(10px); }
                    to { opacity: 1; transform: translateY(0); }
                }
                .animate-fade-in { animation: fade-in 0.5s ease-out forwards; }
            `}</style>
            <Header activePage={activePage} setActivePage={setActivePage} onSearch={handleHeaderSearch} />
            <main>
                {activePage === 'search' && <SearchPage ref={searchPageRef} />}
                {activePage === 'watchlist' && <WatchlistPage />}
                {activePage === 'paper' && <PaperTradingPage />}
                {activePage === 'gettingStarted' && <GettingStartedPage />}
            </main>
        </div>
    );
}

export default App;

