import React, { useState } from 'react';
import { Search, Star, Briefcase, Building2, TrendingUp, Target, Globe, DollarSign, Bitcoin, BarChart3, Newspaper, HelpCircle, Sun, Moon, ChevronDown } from 'lucide-react';
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
                        <NavButton pageName="search">
                            <Search className="w-4 h-4 inline mr-1" />
                            Search
                        </NavButton>
                        <NavButton pageName="watchlist">
                            <Star className="w-4 h-4 inline mr-1" />
                            Watchlist
                        </NavButton>
                        <NavButton pageName="portfolio">
                            <Briefcase className="w-4 h-4 inline mr-1" />
                            Portfolio
                        </NavButton>
                        <NavButton pageName="fundamentals">
                            <Building2 className="w-4 h-4 inline mr-1" />
                            Fundamentals
                        </NavButton>
                        
                        <NavDivider />
                        
                        {/* Stock Analysis */}
                        <NavButton pageName="predictions">
                            <TrendingUp className="w-4 h-4 inline mr-1" />
                            Predict
                        </NavButton>
                        <NavButton pageName="performance">
                            <Target className="w-4 h-4 inline mr-1" />
                            Evaluate
                        </NavButton>
                        
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
                                <Globe className="w-4 h-4" />
                                <span>Other</span>
                                <ChevronDown className={`w-4 h-4 transition-transform duration-200 ${showOtherMenu ? 'rotate-180' : ''}`} />
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
                                    <DollarSign className="w-4 h-4" />
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
                                    <Bitcoin className="w-4 h-4" />
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
                                    <BarChart3 className="w-4 h-4" />
                                    <span>Commodities</span>
                                </button>
                            </div>
                        </div>
                        
                        <NavDivider />
                        
                        {/* Information */}
                        <NavButton pageName="news">
                            <Newspaper className="w-4 h-4 inline mr-1" />
                            News
                        </NavButton>
                        <NavButton pageName="gettingStarted">
                            <HelpCircle className="w-4 h-4 inline mr-1" />
                            Help
                        </NavButton>
                    </div>
                    {/* Dark Mode Toggle */}
                    <button
                        onClick={toggleDarkMode}
                        className="p-2 rounded-lg bg-gray-700 dark:bg-gray-800 hover:bg-gray-600 dark:hover:bg-gray-700 transition-colors duration-200"
                        aria-label="Toggle dark mode"
                    >
                        {isDarkMode ? (
                            <Sun className="w-5 h-5 text-yellow-400" />
                        ) : (
                            <Moon className="w-5 h-5 text-gray-300" />
                        )}
                    </button>
                </div>
            </nav>
        </header>
    );
};

export default Header;
