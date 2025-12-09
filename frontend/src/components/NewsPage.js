import React, { useState, useEffect } from 'react';

// Defines the API base URL. It defaults to the local server (127.0.0.1:5001) 
// if the public environment variable (REACT_APP_API_URL) is not set (e.g., during local development).
const API_URL = process.env.REACT_APP_API_URL || 'http://127.0.0.1:5001';

const NewsPage = () => {
    // State to hold the fetched articles (array of objects)
    const [articles, setArticles] = useState([]);
    // State to manage the loading status of the fetch operation
    const [loading, setLoading] = useState(true);
    // State to store any error messages during the fetch
    const [error, setError] = useState('');

    // Effect Hook: Runs once after the initial render to fetch market news
    useEffect(() => {
        const fetchNews = async () => {
            try {
                // Fetch general news from the backend API endpoint
                // FIX: Changed from single quotes to backticks (``) to correctly interpolate API_URL
                const response = await fetch(`${API_URL}/api/news`);
                
                if (!response.ok) {
                    // Throw an error if the HTTP status code indicates failure
                    throw new Error('Failed to fetch news. The server might be down.');
                }
                
                // Parse the JSON data from the response body
                const data = await response.json();
                setArticles(data);
            } catch (err) {
                // Catch any fetch errors (network, parsing, etc.)
                setError(err.message);
            } finally {
                // Ensure loading state is false regardless of success or failure
                setLoading(false);
            }
        };

        fetchNews();
    }, []); // Empty dependency array ensures this runs only once

    // --- Conditional Rendering ---

    if (loading) {
        return <div className="text-center py-10 text-gray-600 dark:text-gray-400">Loading news...</div>;
    }

    if (error) {
        return <div className="text-center py-10 text-red-500 dark:text-red-400">Error: {error}</div>;
    }

    // Main News Grid Layout
    return (
        <div className="container mx-auto px-4 py-8">
            <h1 className="text-4xl font-extrabold text-gray-800 dark:text-white text-center mb-12">Market News</h1>
            
            {/* Responsive grid layout for articles */}
            <div className="grid gap-8 md:grid-cols-2 lg:grid-cols-3">
                {/* Map over the fetched articles to create individual cards */}
                {articles.map((article, index) => (
                    // The article card is wrapped in an anchor tag to link to the source
                    <a href={article.url} key={index} target="_blank" rel="noopener noreferrer" 
                       className="block bg-white dark:bg-gray-800 p-6 rounded-xl shadow-lg hover:shadow-2xl transition-shadow duration-300">
                        
                        {/* Optional image display */}
                        {article.image && 
                            <img 
                                src={article.image} 
                                alt={article.headline} 
                                className="w-full h-40 object-cover rounded-t-lg mb-4" 
                            />
                        }
                        
                        {/* Article Headline/Title */}
                        <h2 className="text-xl font-bold text-gray-900 dark:text-white mb-2">{article.headline}</h2>
                        
                        {/* Article Summary/Excerpt */}
                        <p className="text-gray-600 dark:text-gray-400 text-sm mb-4">{article.summary}</p>
                        
                        {/* Source/Publisher of the Article */}
                        <span className="text-xs font-semibold text-blue-500">{article.source}</span>
                    </a>
                ))}
            </div>
        </div>
    );
};

export default NewsPage;