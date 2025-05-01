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

        .modal-content h2 {
          margin-bottom: 1rem;
        }

        .modal-content button {
          margin-top: 1.5rem;
          padding: 10px 20px;
          border: none;
          background: red;
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
			<h2>👋 Welcome to Ask NEU!</h2>
			<p>
			  Ask NEU is your personal chatbot for everything Northeastern. Whether you're exploring courses,
			  finding classroom details, or just need quick answers — we’ve got you covered.
			</p>

			<p>
			  🧭 <strong>Namespaces:</strong> Use the <em>Course</em> or <em>Classroom</em> toggles to ask context-specific questions.
			  For example, Don't want to sit in Snell Library ? Just switch to <strong>Classroom</strong> to ask: “Which Classes are available to study today?”
			</p>

			<p>
				🔍 <strong>DeepSearch:</strong> Click the radar icon <Radar size={16} style={{ display: 'inline-block', verticalAlign: 'middle', margin: '0 4px' }} />  next to the input to run a deeper AI-powered search across university resources.
			</p>

			<p>
			  🕵️ <strong>Incognito Mode:</strong> Use the eye icon (<code>👁️</code>) to hide your activity. Conversations in this mode won't be saved.
			</p>

			<p>
			  💡 Just type your question below and press <strong>Enter</strong>. AskNEU will instantly guide you with real-time answers.
			</p>

          <button onClick={onClose}>Got it!</button>
        </div>
      </div>
    </>
  );
};

export default IntroModal;
