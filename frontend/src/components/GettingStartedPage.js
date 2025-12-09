import React from 'react';
import { gettingStartedContent } from '../data/content';
import { BookOpenIcon } from './Icons';

// --- InfoCard Component: Renders a single section of educational content ---
const InfoCard = ({ item }) => {
    return (
        // Card container with shadow and hover animation for visual appeal
        <div className="bg-white dark:bg-gray-800 rounded-xl shadow-md overflow-hidden transform hover:scale-105 transition-transform duration-300">
            <div className="p-8">
                {/* Main Title of the section */}
                <h2 className="text-2xl font-bold text-gray-800 dark:text-white mb-4">{item.title}</h2>
                <div className="space-y-4">
                {/* Map through the array of content elements (paragraphs, lists, headings, etc.) */}
                {item.content.map((el, index) => {
                    // Use a switch statement to render different JSX elements based on the content 'type'
                    switch (el.type) {
                        case 'paragraph':
                            return <p key={index} className="text-gray-600 dark:text-gray-300 leading-relaxed">{el.text}</p>;
                        case 'heading':
                            return <h3 key={index} className="text-xl font-semibold text-gray-700 dark:text-gray-200 mt-4">{el.text}</h3>;
                        case 'list':
                            return (
                                <ul key={index} className="list-disc list-inside space-y-2 text-gray-600 dark:text-gray-300">
                                    {/* Nested map for list items */}
                                    {el.items.map((li, i) => <li key={i}>{li}</li>)}
                                </ul>
                            );
                        case 'note':
                            // Special styling for informational notes or callouts
                            return <p key={index} className="text-sm text-blue-700 dark:text-blue-300 bg-blue-100 dark:bg-blue-900/30 p-3 rounded-lg mt-4">{el.text}</p>
                        default:
                            return null;
                    }
                })}
                </div>
            </div>
        </div>
    );
};

// --- GettingStartedPage Component: Main page structure ---
const GettingStartedPage = () => {
    return (
        <div className="container mx-auto px-4 py-8">
            {/* Page Header */}
            <div className="text-center mb-12">
                <BookOpenIcon />
                <h1 className="text-4xl font-extrabold text-gray-800 dark:text-white">Welcome to Investing!</h1>
                <p className="text-lg text-gray-500 dark:text-gray-400 mt-2">Your complete guide to understanding the market.</p>
            </div>
            
            {/* Content Grid */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
                {/* Map through the external content structure and render an InfoCard for each section */}
                {gettingStartedContent.map((item, index) => (
                    <InfoCard key={index} item={item} />
                ))}
            </div>
        </div>
    );
};

export default GettingStartedPage;