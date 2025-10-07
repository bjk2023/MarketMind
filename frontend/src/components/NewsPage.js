import React, { useState, useEffect } from 'react';

const NewsPage = () => {
    const [articles, setArticles] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState('');

    useEffect(() => {
        const fetchNews = async () => {
            try {
                const response = await fetch('http://127.0.0.1:5001/api/news');
                if (!response.ok) {
                    throw new Error('Failed to fetch news. The server might be down.');
                }
                const data = await response.json();
                setArticles(data);
            } catch (err) {
                setError(err.message);
            } finally {
                setLoading(false);
            }
        };

        fetchNews();
    }, []);

    if (loading) {
        return <div className="text-center py-10">Loading news...</div>;
    }

    if (error) {
        return <div className="text-center py-10 text-red-500">Error: {error}</div>;
    }

    return (
        <div className="container mx-auto px-4 py-8">
            <h1 className="text-4xl font-extrabold text-gray-800 text-center mb-12">Market News</h1>
            <div className="grid gap-8 md:grid-cols-2 lg:grid-cols-3">
                {articles.map((article) => (
                    <a href={article.url} key={article.id} target="_blank" rel="noopener noreferrer" className="block bg-white p-6 rounded-xl shadow-lg hover:shadow-2xl transition-shadow duration-300">
                        {article.image && <img src={article.image} alt={article.headline} className="w-full h-40 object-cover rounded-t-lg mb-4" />}
                        <h2 className="text-xl font-bold text-gray-900 mb-2">{article.headline}</h2>
                        <p className="text-gray-600 text-sm mb-4">{article.summary}</p>
                        <span className="text-xs font-semibold text-blue-500">{article.source}</span>
                    </a>
                ))}
            </div>
        </div>
    );
};

export default NewsPage;
