import React, { useState, useEffect } from 'react';
import { Star, MessageSquare, AlertCircle, BarChart3, RefreshCw, CheckCircle2 } from 'lucide-react';

const Dashboard = () => {
  const [reviews, setReviews] = useState([]);
  const [stats, setStats] = useState({
    total_reviews: 0,
    average_rating: 0,
    sentiment_summary: { positive: 0, neutral: 0, negative: 0 }
  });
  const [loading, setLoading] = useState(true);
  const [syncing, setSyncing] = useState(false);

  const fetchData = async () => {
    try {
      const [reviewsRes, statsRes] = await Promise.all([
        fetch('/api/reviews/'),
        fetch('/api/reviews/stats')
      ]);
      const reviewsData = await reviewsRes.json();
      const statsData = await statsRes.json();
      setReviews(reviewsData);
      setStats(statsData);
      setLoading(false);
    } catch (err) {
      console.error(err);
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  const handleSync = async () => {
    setSyncing(true);
    try {
      await fetch('/api/reviews/sync', { method: 'POST' });
      // Show feedback, then refresh after a short delay
      setTimeout(() => {
        setSyncing(false);
        fetchData();
      }, 2000);
    } catch (err) {
      console.error(err);
      setSyncing(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-50 p-8 font-sans">
      <header className="mb-8 flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">Sage House Reviews</h1>
          <p className="text-slate-500 text-sm">Portfolio Reputation Management</p>
        </div>
        <button 
          onClick={handleSync}
          disabled={syncing}
          className={`flex items-center gap-2 px-4 py-2 rounded-lg border shadow-sm transition-all ${
            syncing 
              ? "bg-slate-100 text-slate-400 border-slate-200 cursor-not-allowed" 
              : "bg-white text-slate-700 border-slate-200 hover:bg-slate-50 active:scale-95"
          }`}
        >
          <RefreshCw size={18} className={syncing ? "animate-spin" : ""} />
          <span>{syncing ? "Syncing..." : "Manual Sync"}</span>
        </button>
      </header>

      <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
        <StatCard title="Total Reviews" value={stats.total_reviews} icon={<MessageSquare className="text-blue-500" />} />
        <StatCard title="Avg Rating" value={stats.average_rating} icon={<Star className="text-yellow-500 fill-yellow-500" />} />
        <StatCard 
          title="Sentiment" 
          value={stats.sentiment_summary.positive > stats.sentiment_summary.negative ? "Positive" : "Critical"} 
          icon={<BarChart3 className={stats.sentiment_summary.positive > stats.sentiment_summary.negative ? "text-green-500" : "text-red-500"} />} 
        />
        <StatCard title="Active Alerts" value={reviews.filter(r => r.rating <= 3).length} icon={<AlertCircle className="text-red-500" />} />
      </div>

      <div className="bg-white rounded-xl shadow-sm border border-slate-200 overflow-hidden">
        <div className="p-6 border-b border-slate-100 flex justify-between items-center">
          <h2 className="text-lg font-semibold text-slate-800">Unified Review Feed</h2>
          <span className="bg-slate-100 text-slate-500 text-xs font-bold px-2 py-1 rounded uppercase tracking-wider">
            {reviews.length} total
          </span>
        </div>
        <div className="divide-y divide-slate-100">
          {loading ? (
            <div className="p-12 text-center text-slate-400">Loading reviews...</div>
          ) : reviews.length === 0 ? (
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
      <span className="text-slate-500 text-sm font-medium uppercase tracking-wider">{title}</span>
      {icon}
    </div>
    <div className="text-2xl font-bold text-slate-900">{value}</div>
  </div>
);

const ReviewItem = ({ review }) => {
  const [replyText, setReplyText] = useState('');
  const [showReply, setShowReply] = useState(false);
  const [isResponded, setIsResponded] = useState(!!review.response_text);

  const submitResponse = async () => {
    if (!replyText) return;
    try {
      await fetch(`/api/reviews/${review.id}/response?response_text=${encodeURIComponent(replyText)}`, { method: 'POST' });
      setIsResponded(true);
      setShowReply(false);
    } catch (err) {
      console.error(err);
    }
  };

  return (
    <div className="p-6 hover:bg-slate-50/50 transition-colors">
      <div className="flex justify-between items-start mb-2">
        <div>
          <h3 className="font-semibold text-slate-900 flex items-center gap-2">
            {review.reviewer_name}
            {review.rating <= 2 && (
              <span className="bg-red-50 text-red-600 text-[10px] font-bold px-1.5 py-0.5 rounded uppercase border border-red-100">Action Needed</span>
            )}
          </h3>
          <p className="text-xs text-slate-400 mt-0.5">{new Date(review.review_date).toLocaleDateString()}</p>
        </div>
        <div className="flex gap-0.5">
          {[...Array(5)].map((_, i) => (
            <Star key={i} size={14} className={i < review.rating ? "text-yellow-400 fill-yellow-400" : "text-slate-200"} />
          ))}
        </div>
      </div>
      <p className="text-slate-600 text-sm leading-relaxed mb-4">{review.review_text}</p>
      
      {isResponded ? (
        <div className="bg-emerald-50 p-4 rounded-lg border border-emerald-100">
          <div className="flex items-center gap-2 mb-1">
            <CheckCircle2 size={14} className="text-emerald-600" />
            <span className="text-emerald-800 text-xs font-bold uppercase">Our Response</span>
          </div>
          <p className="text-emerald-700 text-sm italic">"{review.response_text || replyText}"</p>
        </div>
      ) : (
        <div>
          {!showReply ? (
            <button 
              onClick={() => setShowReply(true)}
              className="text-blue-600 text-xs font-bold uppercase hover:text-blue-700 tracking-tight"
            >
              Respond to review
            </button>
          ) : (
            <div className="mt-2">
              <textarea 
                className="w-full p-3 text-sm border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-100 focus:border-blue-300 min-h-[100px]"
                placeholder="Write your response..."
                value={replyText}
                onChange={(e) => setReplyText(e.target.value)}
              />
              <div className="flex gap-2 mt-2">
                <button 
                  onClick={submitResponse}
                  className="bg-blue-600 text-white text-xs font-bold px-4 py-2 rounded-lg hover:bg-blue-700"
                >
                  Post Response
                </button>
                <button 
                  onClick={() => setShowReply(false)}
                  className="text-slate-500 text-xs font-bold px-4 py-2 hover:bg-slate-100 rounded-lg"
                >
                  Cancel
                </button>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default Dashboard;
