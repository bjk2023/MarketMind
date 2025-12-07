import React from 'react';
import { gettingStartedContent } from '../data/content';
import { BookOpenIcon } from './Icons';

const InfoCard = ({ item }) => {
    return (
        <div className="bg-white rounded-xl shadow-md overflow-hidden transform hover:scale-105 transition-transform duration-300">
            <div className="p-8">
                <h2 className="text-2xl font-bold text-gray-800 mb-4">{item.title}</h2>
                <div className="space-y-4">
                {item.content.map((el, index) => {
                    switch (el.type) {
                        case 'paragraph':
                            return <p key={index} className="text-gray-600 leading-relaxed">{el.text}</p>;
                        case 'heading':
                            return <h3 key={index} className="text-xl font-semibold text-gray-700 mt-4">{el.text}</h3>;
                        case 'list':
                            return (
                                <ul key={index} className="list-disc list-inside space-y-2 text-gray-600">
                                    {el.items.map((li, i) => <li key={i}>{li}</li>)}
                                </ul>
                            );
                        case 'note':
                            return <p key={index} className="text-sm text-blue-700 bg-blue-100 p-3 rounded-lg mt-4">{el.text}</p>
                        default:
                            return null;
                    }
                })}
                </div>
            </div>
        </div>
    );
};

const GettingStartedPage = () => {
    return (
        <div className="container mx-auto px-4 py-8">
            <div className="text-center mb-12">
                <BookOpenIcon />
                <h1 className="text-4xl font-extrabold text-gray-800">Welcome to Investing!</h1>
                <p className="text-lg text-gray-500 mt-2">Your complete guide to understanding the market.</p>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
                {gettingStartedContent.map((item, index) => (
                    <InfoCard key={index} item={item} />
                ))}
            </div>
        </div>
    );
};

export default GettingStartedPage;