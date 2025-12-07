import React, { useState } from 'react';
import { TrendingUpIcon, SearchIcon } from './Icons';

const Header = ({ activePage, setActivePage, onSearch }) => {
    const [searchInput, setSearchInput] = useState('');

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

    const handleSearchSubmit = (e) => {
        e.preventDefault();
        if (searchInput.trim()) {
            onSearch(searchInput.trim());
            setSearchInput('');
        }
    };

    return (
        <header className="bg-gray-800 text-white shadow-lg">
            <nav className="container mx-auto px-6 py-4">
                <div className="flex justify-between items-center mb-4">
                    <div className="flex items-center">
                        <TrendingUpIcon className="h-8 w-8 text-blue-400 mr-2" />
                        <h1 className="text-xl font-bold tracking-wider">MarketMind</h1>
                    </div>
                    
                    {/* Global Search Bar */}
                    <form onSubmit={handleSearchSubmit} className="flex-1 max-w-md mx-4">
                        <div className="relative">
                            <input
                                type="text"
                                placeholder="Search stocks..."
                                value={searchInput}
                                onChange={(e) => setSearchInput(e.target.value.toUpperCase())}
                                className="w-full px-4 py-2 bg-gray-700 text-white rounded-lg focus:ring-2 focus:ring-blue-500 outline-none placeholder-gray-400"
                            />
                            <button
                                type="submit"
                                className="absolute right-3 top-1/2 transform -translate-y-1/2 text-gray-400 hover:text-white"
                            >
                                <SearchIcon className="h-5 w-5" />
                            </button>
                        </div>
                    </form>
                </div>

                <div className="flex items-center space-x-2 bg-gray-900 rounded-lg p-1">
                    <NavButton pageName="search">Search</NavButton>
                    <NavButton pageName="watchlist">Watchlist</NavButton>
                    <NavButton pageName="comparison">Comparison</NavButton>
                    <NavButton pageName="paper">Paper Trading</NavButton>
                    <NavButton pageName="gettingStarted">Getting Started</NavButton>
                </div>
            </nav>
        </header>
    );
};

export default Header;

