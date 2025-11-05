import React from 'react';
import { TrendingUpIcon } from './Icons';
import { useDarkMode } from '../context/DarkModeContext';

const Header = ({ activePage, setActivePage }) => {
    const { isDarkMode, toggleDarkMode } = useDarkMode();
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
        <header className="bg-gray-800 dark:bg-gray-950 text-white shadow-lg transition-colors duration-200">
            <nav className="container mx-auto px-6 py-4 flex justify-between items-center">
                <div className="flex items-center">
                    <h1 className="text-xl font-bold tracking-wider">MarketMind</h1>
                </div>
                <div className="flex items-center space-x-4">
                    {/* Navigation Buttons */}
                    <div className="flex items-center space-x-2 bg-gray-900 dark:bg-gray-800 rounded-lg p-1">
                        <NavButton pageName="search">Search</NavButton>
                        <NavButton pageName="predictions">Predictions</NavButton>
                        <NavButton pageName="performance">Performance</NavButton>
                        <NavButton pageName="forex">Forex</NavButton>
                        <NavButton pageName="crypto">Crypto</NavButton>
                        <NavButton pageName="watchlist">Watchlist</NavButton>
                        <NavButton pageName="news">News</NavButton>
                        <NavButton pageName="gettingStarted">Getting Started</NavButton>
                    </div>
                    {/* Dark Mode Toggle */}
                    <button
                        onClick={toggleDarkMode}
                        className="p-2 rounded-lg bg-gray-700 dark:bg-gray-800 hover:bg-gray-600 dark:hover:bg-gray-700 transition-colors duration-200"
                        aria-label="Toggle dark mode"
                    >
                        {isDarkMode ? (
                            // Sun Icon (Light Mode)
                            <svg className="w-5 h-5 text-yellow-400" fill="currentColor" viewBox="0 0 20 20">
                                <path fillRule="evenodd" d="M10 2a1 1 0 011 1v1a1 1 0 11-2 0V3a1 1 0 011-1zm4 8a4 4 0 11-8 0 4 4 0 018 0zm-.464 4.95l.707.707a1 1 0 001.414-1.414l-.707-.707a1 1 0 00-1.414 1.414zm2.12-10.607a1 1 0 010 1.414l-.706.707a1 1 0 11-1.414-1.414l.707-.707a1 1 0 011.414 0zM17 11a1 1 0 100-2h-1a1 1 0 100 2h1zm-7 4a1 1 0 011 1v1a1 1 0 11-2 0v-1a1 1 0 011-1zM5.05 6.464A1 1 0 106.465 5.05l-.708-.707a1 1 0 00-1.414 1.414l.707.707zm1.414 8.486l-.707.707a1 1 0 01-1.414-1.414l.707-.707a1 1 0 011.414 1.414zM4 11a1 1 0 100-2H3a1 1 0 000 2h1z" clipRule="evenodd" />
                            </svg>
                        ) : (
                            // Moon Icon (Dark Mode)
                            <svg className="w-5 h-5 text-gray-300" fill="currentColor" viewBox="0 0 20 20">
                                <path d="M17.293 13.293A8 8 0 016.707 2.707a8.001 8.001 0 1010.586 10.586z" />
                            </svg>
                        )}
                    </button>
                </div>
            </nav>
        </header>
    );
};

export default Header;
