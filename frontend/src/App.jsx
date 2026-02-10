import React, { useState, useEffect } from 'react';
import { Star, MessageSquare, AlertCircle, BarChart3, RefreshCw } from 'lucide-react';

const Dashboard = () => {
  const [reviews, setReviews] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch('/api/reviews/')
      .then(res => res.json())
      .then(data => {
        setReviews(data);
        setLoading(false);
      })
      .catch(err => console.error(err));
  }, []);

  return (
    <div className="min-h-screen bg-slate-50 p-8">
      <header className="mb-8 flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">Sage House Reviews</h1>
          <p className="text-slate-500">Reputation Management & Monitoring</p>
        </div>
        <button className="flex items-center gap-2 bg-white px-4 py-2 rounded-lg border border-slate-200 shadow-sm hover:bg-slate-50 transition-colors">
          <RefreshCw size={18} />
          <span>Manual Sync</span>
        </button>
      </header>

      <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
        <StatCard title="Total Reviews" value={reviews.length} icon={<MessageSquare className="text-blue-500" />} />
        <StatCard title="Avg Rating" value="4.8" icon={<Star className="text-yellow-500 fill-yellow-500" />} />
        <StatCard title="Active Alerts" value="2" icon={<AlertCircle className="text-red-500" />} />
        <StatCard title="Sentiment" value="Positive" icon={<BarChart3 className="text-green-500" />} />
      </div>

      <div className="bg-white rounded-xl shadow-sm border border-slate-200 overflow-hidden">
        <div className="p-6 border-b border-slate-100">
          <h2 className="text-lg font-semibold text-slate-800">Review Feed</h2>
        </div>
        <div className="divide-y divide-slate-100">
          {reviews.length === 0 ? (
            <div className="p-12 text-center text-slate-400">
              No reviews found. Trigger a sync to begin.
            </div>
          ) : (
            reviews.map(review => (
              <ReviewItem key={review.id} review={review} />
            ))
          )}
        </div>
      </div>
    </div>
  );
};

const StatCard = ({ title, value, icon }) => (
  <div className="bg-white p-6 rounded-xl shadow-sm border border-slate-200">
    <div className="flex justify-between items-start mb-4">
      <span className="text-slate-500 text-sm font-medium">{title}</span>
      {icon}
    </div>
    <div className="text-2xl font-bold text-slate-900">{value}</div>
  </div>
);

const ReviewItem = ({ review }) => (
  <div className="p-6 hover:bg-slate-50 transition-colors">
    <div className="flex justify-between mb-2">
      <h3 className="font-semibold text-slate-900">{review.reviewer_name}</h3>
      <span className="text-slate-400 text-sm">{new Date(review.review_date).toLocaleDateString()}</span>
    </div>
    <div className="flex gap-1 mb-3">
      {[...Array(5)].map((_, i) => (
        <Star key={i} size={16} className={i < review.rating ? "text-yellow-400 fill-yellow-400" : "text-slate-200"} />
      ))}
    </div>
    <p className="text-slate-600 mb-4">{review.review_text}</p>
    {review.response_text ? (
      <div className="bg-blue-50 p-4 rounded-lg border border-blue-100">
        <p className="text-blue-800 text-sm font-medium mb-1">Response:</p>
        <p className="text-blue-700 text-sm">{review.response_text}</p>
      </div>
    ) : (
      <button className="text-blue-600 text-sm font-semibold hover:underline">Respond to review</button>
    )}
  </div>
);

export default Dashboard;
