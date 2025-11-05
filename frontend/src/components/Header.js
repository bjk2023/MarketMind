import React, { useState } from 'react';
import { TrendingUpIcon } from './Icons';
import { useDarkMode } from '../context/DarkModeContext';

const Header = ({ activePage, setActivePage }) => {
    const { isDarkMode, toggleDarkMode } = useDarkMode();
    const [showOtherMenu, setShowOtherMenu] = useState(false);
    const NavButton = ({ pageName, children }) => {
        const isActive = activePage === pageName;
        return (
            <button
                onClick={() => setActivePage(pageName)}
                className={`px-3 py-2 rounded-md text-sm font-medium transition-colors duration-200 whitespace-nowrap ${
                    isActive
                        ? 'bg-blue-600 text-white shadow-md'
                        : 'text-gray-300 hover:bg-gray-700 hover:text-white'
                }`}
            >
                {children}
            </button>
        );
    };

    const NavDivider = () => (
        <div className="h-6 w-px bg-gray-700 dark:bg-gray-600 mx-1"></div>
    );

    return (
        <header className="bg-gray-800 dark:bg-gray-950 text-white shadow-lg transition-colors duration-200">
            <nav className="container mx-auto px-6 py-4 flex justify-between items-center">
                <div className="flex items-center">
                    <h1 className="text-xl font-bold tracking-wider">MarketMind</h1>
                </div>
                <div className="flex items-center space-x-4">
                    {/* Navigation Buttons - Organized by Section */}
                    <div className="flex items-center space-x-1 bg-gray-900 dark:bg-gray-800 rounded-lg p-1 relative">
                        {/* Main Actions */}
                        <NavButton pageName="search">🔍 Search</NavButton>
                        <NavButton pageName="watchlist">⭐ Watchlist</NavButton>
                        
                        <NavDivider />
                        
                        {/* Stock Analysis */}
                        <NavButton pageName="predictions">📈 Predict</NavButton>
                        <NavButton pageName="performance">🎯 Evaluate</NavButton>
                        
                        <NavDivider />
                        
                        {/* Other Markets Dropdown */}
                        <div className="relative">
                            <button
                                onClick={() => setShowOtherMenu(!showOtherMenu)}
                                className={`px-3 py-2 rounded-md text-sm font-medium transition-colors duration-200 whitespace-nowrap flex items-center space-x-1 ${
                                    ['forex', 'crypto', 'commodities'].includes(activePage)
                                        ? 'bg-blue-600 text-white shadow-md'
                                        : 'text-gray-300 hover:bg-gray-700 hover:text-white'
                                }`}
                            >
                                <span>🌐 Other</span>
                                <svg 
                                    className={`w-4 h-4 transition-transform duration-200 ${showOtherMenu ? 'rotate-180' : ''}`} 
                                    fill="none" 
                                    stroke="currentColor" 
                                    viewBox="0 0 24 24"
                                >
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                                </svg>
                            </button>
                            
                            {/* Dropdown Menu with Slide Animation */}
                            <div 
                                className={`absolute top-full left-0 mt-2 bg-gray-900 dark:bg-gray-800 rounded-lg shadow-xl border border-gray-700 overflow-hidden transition-all duration-300 ease-out z-50 ${
                                    showOtherMenu 
                                        ? 'opacity-100 translate-y-0 max-h-48' 
                                        : 'opacity-0 -translate-y-2 max-h-0 pointer-events-none'
                                }`}
                                style={{ minWidth: '180px' }}
                            >
                                <button
                                    onClick={() => {
                                        setActivePage('forex');
                                        setShowOtherMenu(false);
                                    }}
                                    className={`w-full px-4 py-3 text-left text-sm font-medium transition-colors duration-150 flex items-center space-x-2 ${
                                        activePage === 'forex'
                                            ? 'bg-blue-600 text-white'
                                            : 'text-gray-300 hover:bg-gray-700 hover:text-white'
                                    }`}
                                >
                                    <span>💱</span>
                                    <span>Forex</span>
                                </button>
                                <button
                                    onClick={() => {
                                        setActivePage('crypto');
                                        setShowOtherMenu(false);
                                    }}
                                    className={`w-full px-4 py-3 text-left text-sm font-medium transition-colors duration-150 flex items-center space-x-2 ${
                                        activePage === 'crypto'
                                            ? 'bg-blue-600 text-white'
                                            : 'text-gray-300 hover:bg-gray-700 hover:text-white'
                                    }`}
                                >
                                    <span>🪙</span>
                                    <span>Crypto</span>
                                </button>
                                <button
                                    onClick={() => {
                                        setActivePage('commodities');
                                        setShowOtherMenu(false);
                                    }}
                                    className={`w-full px-4 py-3 text-left text-sm font-medium transition-colors duration-150 flex items-center space-x-2 ${
                                        activePage === 'commodities'
                                            ? 'bg-blue-600 text-white'
                                            : 'text-gray-300 hover:bg-gray-700 hover:text-white'
                                    }`}
                                >
                                    <span>📊</span>
                                    <span>Commodities</span>
                                </button>
                            </div>
                        </div>
                        
                        <NavDivider />
                        
                        {/* Information */}
                        <NavButton pageName="news">📰 News</NavButton>
                        <NavButton pageName="gettingStarted">❓ Help</NavButton>
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
