import React, { useState } from 'react';
import { X, Send, Star } from 'lucide-react';

const FeedbackModal = ({ onClose }) => {
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [feedback, setFeedback] = useState('');
  const [rating, setRating] = useState(0);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [submitError, setSubmitError] = useState('');
  const [submitted, setSubmitted] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    // Validate required fields
    if (!name.trim()) {
      setSubmitError('Please enter your name.');
      return;
    }
    
    if (!email.trim()) {
      setSubmitError('Please enter your email address.');
      return;
    }
    
    if (!feedback.trim()) {
      setSubmitError('Please provide feedback before submitting.');
      return;
    }
    
    // Simple email validation
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(email)) {
      setSubmitError('Please enter a valid email address.');
      return;
    }
    
    setIsSubmitting(true);
    setSubmitError('');
    
    try {
      const response = await fetch('/api/app-feedback/submit', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          name,
          email,
          feedback,
          rating,
          timestamp: new Date().toISOString()
        })
      });
      
      if (!response.ok) {
        throw new Error('Failed to submit feedback');
      }
      
      setSubmitted(true);
      
      // Auto-close after 3 seconds
      setTimeout(() => {
        onClose();
      }, 3000);
      
    } catch (error) {
      console.error('Error submitting feedback:', error);
      setSubmitError('There was an error submitting your feedback. Please try again.');
    } finally {
      setIsSubmitting(false);
    }
  };

  const renderStars = () => {
    const stars = [];
    for (let i = 1; i <= 5; i++) {
      stars.push(
        <button
          key={i}
          type="button"
          onClick={() => setRating(i)}
          className={`star-btn ${i <= rating ? 'active' : ''}`}
          aria-label={`${i} star${i !== 1 ? 's' : ''}`}
        >
          <Star size={24} fill={i <= rating ? '#cc0000' : 'none'} />
        </button>
      );
    }
    return (
      <div className="rating-container">
        {stars}
      </div>
    );
  };

  return (
    <div className="feedback-modal-overlay">
      <div className="feedback-modal">
        <div className="feedback-modal-header">
          <h2>Send Feedback</h2>
          <button onClick={onClose} className="close-btn" aria-label="Close feedback">
            <X size={24} />
          </button>
        </div>
        
        <div className="feedback-modal-content">
          {!submitted ? (
            <form onSubmit={handleSubmit} className="feedback-form">
              <div className="form-field rating-field">
                <label>How would you rate your experience?</label>
                {renderStars()}
              </div>
              
              <div className="form-field">
                <label htmlFor="name">Name <span className="required">*</span></label>
                <input
                  type="text"
                  id="name"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  placeholder="Your name"
                  required
                />
              </div>
              
              <div className="form-field">
                <label htmlFor="email">Email <span className="required">*</span></label>
                <input
                  type="email"
                  id="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="Your email address"
                  required
                />
              </div>
              
              <div className="form-field">
                <label htmlFor="feedback">Feedback <span className="required">*</span></label>
                <textarea
                  id="feedback"
                  value={feedback}
                  onChange={(e) => setFeedback(e.target.value)}
                  placeholder="Share your thoughts, suggestions, or report issues..."
                  rows={5}
                  required
                />
              </div>
              
              {submitError && <div className="error-message">{submitError}</div>}
              
              <button 
                type="submit" 
                className="submit-btn"
                disabled={isSubmitting}
              >
                {isSubmitting ? 'Submitting...' : 'Submit Feedback'}
                {!isSubmitting && <Send size={16} className="submit-icon" />}
              </button>
            </form>
          ) : (
            <div className="feedback-success">
              <h3>Thank You!</h3>
              <p>Your feedback has been submitted successfully.</p>
              <p className="auto-close-message">This window will close automatically in a few seconds.</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default FeedbackModal;