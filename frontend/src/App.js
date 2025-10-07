import React, { useState } from 'react';
import Header from './components/Header';
import SearchPage from './components/SearchPage';
import GettingStartedPage from './components/GettingStartedPage';

function App() {
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
            </main>
        </div>
    );
}

export default App;