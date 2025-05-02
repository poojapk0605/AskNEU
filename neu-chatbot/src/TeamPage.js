import React from 'react';
import { X, Linkedin, Github, Mail } from 'lucide-react';

const TeamPage = ({ onClose }) => {
  return (
    <div className="team-modal-overlay">
      <div className="team-modal">
        <div className="team-modal-header">
          <h2>Meet Our Team</h2>
          <button 
            onClick={onClose} 
            className="close-btn" 
            aria-label="Close team info"
          >
            <X size={24} />
          </button>
        </div>
        
        <div className="team-modal-content">
          <p className="team-intro">
            Ask NEU was built by Northeastern students who wanted to make campus information
            more accessible to the university community.
          </p>
          
          <div className="team-grid">
            {/* Example team member cards - replace with actual team info */}
            <div className="team-member">
              <div className="team-member-photo">
                {/* Placeholder for team member photo */}
                <div className="photo-placeholder">JD</div>
              </div>
              <h3>Jane Doe</h3>
              <p>Computer Science, 2025</p>
              <div className="team-member-links">
                <a href="https://linkedin.com/" target="_blank" rel="noopener noreferrer" aria-label="LinkedIn profile">
                  <Linkedin size={18} />
                </a>
                <a href="https://github.com/" target="_blank" rel="noopener noreferrer" aria-label="GitHub profile">
                  <Github size={18} />
                </a>
                <a href="mailto:example@northeastern.edu" aria-label="Email">
                  <Mail size={18} />
                </a>
              </div>
            </div>
            
            <div className="team-member">
              <div className="team-member-photo">
                <div className="photo-placeholder">JS</div>
              </div>
              <h3>John Smith</h3>
              <p>Data Science, 2024</p>
              <div className="team-member-links">
                <a href="https://linkedin.com/" target="_blank" rel="noopener noreferrer" aria-label="LinkedIn profile">
                  <Linkedin size={18} />
                </a>
                <a href="https://github.com/" target="_blank" rel="noopener noreferrer" aria-label="GitHub profile">
                  <Github size={18} />
                </a>
                <a href="mailto:example@northeastern.edu" aria-label="Email">
                  <Mail size={18} />
                </a>
              </div>
            </div>
            
            <div className="team-member">
              <div className="team-member-photo">
                <div className="photo-placeholder">AK</div>
              </div>
              <h3>Alex Kim</h3>
              <p>Information Systems, 2025</p>
              <div className="team-member-links">
                <a href="https://linkedin.com/" target="_blank" rel="noopener noreferrer" aria-label="LinkedIn profile">
                  <Linkedin size={18} />
                </a>
                <a href="https://github.com/" target="_blank" rel="noopener noreferrer" aria-label="GitHub profile">
                  <Github size={18} />
                </a>
                <a href="mailto:example@northeastern.edu" aria-label="Email">
                  <Mail size={18} />
                </a>
              </div>
            </div>
            
            <div className="team-member">
              <div className="team-member-photo">
                <div className="photo-placeholder">MP</div>
              </div>
              <h3>Maria Patel</h3>
              <p>Computer Engineering, 2024</p>
              <div className="team-member-links">
                <a href="https://linkedin.com/" target="_blank" rel="noopener noreferrer" aria-label="LinkedIn profile">
                  <Linkedin size={18} />
                </a>
                <a href="https://github.com/" target="_blank" rel="noopener noreferrer" aria-label="GitHub profile">
                  <Github size={18} />
                </a>
                <a href="mailto:example@northeastern.edu" aria-label="Email">
                  <Mail size={18} />
                </a>
              </div>
            </div>
          </div>
          
          <div className="team-contact">
            <h3>Want to join our team?</h3>
            <p>We're always looking for talented Huskies to help improve Ask NEU.</p>
            <a href="mailto:askneu@northeastern.edu" className="contact-btn">
              Contact Us
            </a>
          </div>
        </div>
      </div>
    </div>
  );
};

export default TeamPage;