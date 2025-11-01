import React from 'react';
import { TrendingUpIcon } from './Icons';

const Header = ({ activePage, setActivePage }) => {
    const NavButton = ({ pageName, children }) => {
        const isActive = activePage === pageName;
        return (
            <button
                onClick={() => setActivePage(pageName)}
                className={`px-4 py-2 rounded-md text-sm font-medium transition-colors duration-200 ${
                    isActive
                        ? 'bg-blue-600 text-white shadow-md'
                        : 'text-gray-300 hover:bg-gray-700 hover:text-white'
                }`}
            >
                {children}
            </button>
        );
    };

    return (
        <header className="bg-gray-800 text-white shadow-lg">
            <nav className="container mx-auto px-6 py-4 flex justify-between items-center">
                <div className="flex items-center">
                    <h1 className="text-xl font-bold tracking-wider">MarketMind</h1>
                </div>
                {/* --- UPDATED: Added Watchlist button --- */}
                <div className="flex items-center space-x-2 bg-gray-900 rounded-lg p-1">
                    <NavButton pageName="search">Search</NavButton>
                    <NavButton pageName="predictions">Predictions</NavButton>
                    <NavButton pageName="watchlist">Watchlist</NavButton>
                    <NavButton pageName="news">News</NavButton>
                    <NavButton pageName="gettingStarted">Getting Started</NavButton>
                </div>
            </nav>
        </header>
    );
};

export default Header;
