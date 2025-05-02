import React from 'react';
import { X, Radar, BookOpen, School, Eye, EyeOff, MessageSquare } from 'lucide-react';

const HelpModal = ({ onClose, onFeedbackClick }) => {
  return (
    <div className="help-modal-overlay">
      <div className="help-modal">
        <div className="help-modal-header">
          <h2>Help & Information</h2>
          <button onClick={onClose} className="close-btn" aria-label="Close help">
            <X size={24} />
          </button>
        </div>
        
        <div className="help-modal-content">
          <div className="help-modal-logo">
            <img src="/logo.png" alt="AskNEU Logo" />
          </div>
          
          <h3>Welcome to askNEU — your one-stop solution for everything Northeastern!</h3>
          <p>
            Built on information from 100+ official Northeastern websites, askNEU has all the resources you need to answer any university-related question. Whatever you're curious about — chances are, we've got you covered.
          </p>
          <p>
            Our search results don't just give you answers — they also show you the source, so you can easily verify the information yourself.
          </p>

          <div className="help-section">
            <h4>Search Spaces</h4>
            <div className="help-item">
              <div className="help-icon course-icon">
                <BookOpen size={20} />
              </div>
              <div className="help-text">
                <strong>Course Lookup</strong> - Quickly search and explore Northeastern's course offerings — because who has time to dig through endless catalogs?
                <div className="update-info">Last updated: Fall 2025 offerings</div>
              </div>
            </div>
            
            <div className="help-item">
              <div className="help-icon classroom-icon">
                <School size={20} />
              </div>
              <div className="help-text">
                <strong>Classroom Finder</strong> - Need a quiet study spot? Snell might be packed (as usual), but don't worry — we suggest available classrooms around campus where you can study. We'll even let you know when a room is occupied so you can plan smartly!
                <div className="update-info">Last updated: Spring 2025 schedule</div>
              </div>
            </div>
          </div>

          <div className="help-section">
            <h4>Search Modes</h4>
            <div className="help-item">
              <div className="help-icon deepsearch-icon">
                <Radar size={20} />
              </div>
              <div className="help-text">
                <strong>Deep Search</strong> - For complex queries that require serious digging. Enables an AI-powered deeper search across university resources.
              </div>
            </div>
            
            <div className="help-item">
              <div className="help-icon">
                <Eye size={20} />
              </div>
              <div className="help-text">
                <strong>Incognito Mode</strong> - Use Incognito Mode (toggle in the top right) to keep your searches private. We store your queries to help improve our model and provide better responses over time.
                <Eye size={16} /> indicates standard mode, while <EyeOff size={16} /> indicates incognito mode.
              </div>
            </div>
          </div>

          <div className="help-section">
            <h4>Important Notes</h4>
            <ul className="help-tips">
              <li>Feel free to leave feedback using the thumbs up or thumbs down to quickly share your thoughts about the model's responses</li>
              <li>This initiative is driven by Northeastern students, created to support and assist students across campus</li>
              <li>The model may hallucinate. Please verify the sources provided to ensure you have the latest and most accurate information!</li>
              <li>The data in the search spaces is regularly updated to ensure it reflects the latest information</li>
            </ul>
          </div>
          
          {/* Feedback Button */}
          <div style={{ textAlign: 'center', marginTop: '2rem' }}>
            <button 
              className="guest-btn"
              onClick={onFeedbackClick}
              style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', margin: '0 auto' }}
            >
              <MessageSquare size={18} />
              Share Your Feedback
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default HelpModal;