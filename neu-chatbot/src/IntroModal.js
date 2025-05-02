import React from 'react';
import { Radar } from 'lucide-react';


const IntroModal = ({ onClose }) => {
  return (
    <>
      <style>{`
        .modal-overlay {
          position: fixed;
          top: 0;
          left: 0;
          width: 100%;
          height: 100%;
          backdrop-filter: blur(5px);
          background-color: rgba(0, 0, 0, 0.4);
          z-index: 9999;
          display: flex;
          align-items: center;
          justify-content: center;
        }
		    .modal-content i.lucide {
		      display: inline-block;
		      vertical-align: middle;
		      margin-left: 4px;
		    }

        .modal-content {
          background: white;
          padding: 2rem;
          border-radius: 12px;
          box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3);
          max-width: 500px;
          text-align: center;
          animation: fadeIn 0.4s ease;
        }
        
        .modal-logo {
          margin-bottom: 1.5rem;
        }
        
        .modal-logo img {
          height: 60px;
          width: auto;
        }

        .modal-content h3 {
          font-size: 1.3rem;
          margin-bottom: 1rem;
          color: var(--primary-color);
        }

        .modal-content button {
          margin-top: 1.5rem;
          padding: 10px 20px;
          border: none;
          background: #cc0000;
          color: white;
          font-size: 1rem;
          border-radius: 6px;
          cursor: pointer;
        }

        @keyframes fadeIn {
          from { opacity: 0; transform: scale(0.95); }
          to { opacity: 1; transform: scale(1); }
        }
      `}</style>

      <div className="modal-overlay">
        <div className="modal-content">
          <div className="modal-logo">
            <img src="/logo.png" alt="AskNEU Logo" />
          </div>
        
          <h3>Welcome to askNEU!</h3>
          <p>
            Welcome to askNEU — your one-stop solution for everything Northeastern! Built on information from 100+ official Northeastern websites, askNEU has all the resources you need to answer any university-related question.
          </p>

          <p>
            🧭 <strong>Search Spaces:</strong> <em>Course Lookup</em> for quickly finding course offerings, or <em>Classroom Finder</em> to discover available study spots when Snell is packed! We'll even let you know when rooms are occupied.
          </p>

          <p>
            🔍 <strong>Search Modes:</strong> Use Normal Search for general questions or Deep Search <Radar size={16} style={{ display: 'inline-block', verticalAlign: 'middle', margin: '0 4px' }} /> for complex queries that require serious digging.
          </p>

          <p>
            🕵️ <strong>Incognito Mode:</strong> Use the eye icon (<code>👁️</code>) to keep your searches private. We store regular queries to improve our model over time.
          </p>

          <p>
            💡 <strong>Note:</strong> The model may hallucinate. Please verify the sources provided to ensure you have the latest and most accurate information!
          </p>

          <button onClick={onClose}>Got it!</button>
        </div>
      </div>
    </>
  );
};

export default IntroModal;